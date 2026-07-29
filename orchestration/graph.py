# orchestration/graph.py
from langgraph.graph import StateGraph, END  # type: ignore
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, bus: Any = None):
        logger.info("Initializing Orchestrator with LangGraph")
        self.bus = bus

    def run_pipeline(self, agents: Dict[str, Any], repo_source: str, style: str = "Technical Blog", goal: str = ""):
        """Run pipeline using LangGraph."""
        logger.info(
            f"Orchestrator: executing pipeline (Style: {style}, Goal: {goal})")

        workflow = StateGraph(dict)

        def analyze_repo(state):
            try:
                repo_analysis = agents["repo_analyzer"].run()
            except Exception as exc:
                logger.exception("repo_analyzer failed", exc_info=exc)
                repo_analysis = None
            return {**state, "repo_analysis": repo_analysis}

        def recommend_metadata(state):
            repo_analysis = state.get("repo_analysis")
            if not repo_analysis:
                raise ValueError("Repo analysis missing in state")
            try:
                metadata = agents["metadata_recommender"].run(
                    repo_analysis.readme, repo_analysis.files)
            except Exception as exc:
                logger.exception("metadata_recommender failed", exc_info=exc)
                metadata = type("StubMetadata", (), {
                    "title_suggestions": ["Untitled Project"],
                    "tags": ["AI", "Project"],
                    "short_description": "Project description unavailable."
                })()
            if metadata is None:
                raise ValueError("Metadata recommender returned no metadata")
            return {**state, "metadata": metadata}

        def improve_content(state):
            repo_analysis = state.get("repo_analysis")
            metadata = state.get("metadata")
            style_val = state.get("style", "Technical Blog")
            goal_val = state.get("goal", "")
            try:
                content_improvement = agents["content_improver"].run(
                    getattr(repo_analysis, "readme", ""), metadata, style=style_val, goal=goal_val)
            except Exception as exc:
                logger.exception("content_improver failed", exc_info=exc)
                content_improvement = None
            if content_improvement is None:
                content_improvement = type("StubContent", (), {
                    "improved_readme": "# Improved README\n\nContent generation unavailable. Please review the repository manually.",
                    "suggested_images": {}
                })()
            return {**state, "content_improvement": content_improvement}

        def review_content(state):
            content = state.get("content_improvement")
            repo_analysis = state.get("repo_analysis")
            try:
                review = agents["reviewer_critic"].run(
                    getattr(content, 'improved_readme', ''), getattr(repo_analysis, 'code_stats', {}))
            except Exception as exc:
                logger.exception("reviewer_critic failed", exc_info=exc)
                review = type("StubReview", (), {
                    "score": 5.0,
                    "issues": ["Review unavailable"],
                    "strengths": ["Basic fallback review"],
                    "recommendations": ["Add more detail to the repository documentation"]
                })()
            return {**state, "review": review}

        def fact_check(state):
            repo_analysis = state.get("repo_analysis")
            try:
                fact_issues = agents["fact_checker"].run(
                    getattr(repo_analysis, 'readme', ''))
            except Exception as exc:
                logger.exception("fact_checker failed", exc_info=exc)
                fact_issues = type("StubFactCheck", (), {
                    "claims_found": [],
                    "verified": [],
                    "flagged": ["Fact-checking unavailable in fallback mode"]
                })()
            return {**state, "fact_check": fact_issues}

        workflow.add_node("analyze_repo", analyze_repo)
        workflow.add_node("recommend_metadata", recommend_metadata)
        workflow.add_node("improve_content", improve_content)
        workflow.add_node("review_content", review_content)
        workflow.add_node("fact_check", fact_check)

        workflow.set_entry_point("analyze_repo")
        workflow.add_edge("analyze_repo", "recommend_metadata")
        workflow.add_edge("recommend_metadata", "improve_content")
        workflow.add_edge("improve_content", "review_content")
        workflow.add_edge("review_content", "fact_check")
        workflow.add_edge("fact_check", END)

        compiled = workflow.compile()
        inputs = {
            "repo_source": repo_source,
            "style": style,
            "goal": goal
        }
        try:
            result = compiled.invoke(inputs)
        except Exception as exc:
            # If the pipeline failed due to missing required metadata, surface that
            # error to callers so tests and callers can react accordingly.
            if isinstance(exc, ValueError):
                logger.exception(
                    "Pipeline execution failed with ValueError", exc_info=exc)
                raise
            # Otherwise, log and return partial results
            logger.exception("Pipeline execution failed", exc_info=exc)
            # Attempt to extract whatever state the compiled graph retained
            try:
                result = getattr(compiled, "last_result", {}) or {}
            except Exception:
                result = {}

        return {
            "analysis": result.get("repo_analysis"),
            "metadata": result.get("metadata"),
            "content_improvement": result.get("content_improvement"),
            "review": result.get("review"),
            "fact_check": result.get("fact_check")
        }

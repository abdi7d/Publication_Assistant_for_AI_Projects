# orchestration/graph.py
from langgraph.graph import StateGraph, END  # type: ignore
import logging
from typing import Any, Dict

from utils.publication_builder import PublicationBuilder
from orchestration.collaborative_orchestrator import CollaborativeOrchestrator

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, bus: Any = None, use_collaborative: bool = False):
        logger.info("Initializing Orchestrator with LangGraph (collaborative: %s)", use_collaborative)
        self.bus = bus
        self.publication_builder = PublicationBuilder()
        self.collaborative_orchestrator = CollaborativeOrchestrator() if use_collaborative else None
        self.use_collaborative = use_collaborative

    def compile(self):
        return self

    def execute(self, repo_source: str, agents: Dict[str, Any] | None = None, style: str = "Technical Blog", goal: str = ""):
        if agents is None:
            return {}
        
        # Use collaborative orchestration if enabled and enhanced agents are available
        if self.use_collaborative and self._has_enhanced_agents(agents):
            return self._run_collaborative_pipeline(agents, repo_source, style, goal)
        
        return self.run_pipeline(agents, repo_source, style=style, goal=goal)

    def _has_enhanced_agents(self, agents: Dict[str, Any]) -> bool:
        """Check if enhanced agents are available."""
        enhanced_agent_keys = [
            'deep_repo_analyzer',
            'intelligent_content_improver',
            'comprehensive_fact_checker',
            'adaptive_technical_writer',
            'seo_strategy_agent'
        ]
        return any(key in agents for key in enhanced_agent_keys)

    def _run_collaborative_pipeline(self, agents: Dict[str, Any], repo_source: str, 
                                   style: str, goal: str) -> Dict[str, Any]:
        """Run enhanced collaborative pipeline with new agents."""
        logger.info("Orchestrator: running collaborative enhanced pipeline")
        
        # Build repository context for collaborative orchestration
        repo_context = self._build_repository_context(agents, repo_source)
        
        # Run collaborative orchestration
        collaborative_result = self.collaborative_orchestrator.orchestrate_collaboration(
            agents, repo_context, goal
        )
        
        # Extract results from collaborative process
        result = {
            "analysis": repo_context.get("repo_analysis"),
            "metadata": repo_context.get("metadata"),
            "content_improvement": collaborative_result.final_content,
            "review": self._generate_review_from_collaboration(collaborative_result),
            "fact_check": self._generate_fact_check_from_collaboration(collaborative_result),
            "publication_readme": collaborative_result.final_content,
            "collaborative_metrics": collaborative_result.collaboration_metrics,
            "quality_gates": collaborative_result.quality_gates,
        }
        
        return result

    def _build_repository_context(self, agents: Dict[str, Any], repo_source: str) -> Dict[str, Any]:
        """Build repository context from agents."""
        context = {"repo_source": repo_source}
        
        # Try to get deep repository analysis
        if "deep_repo_analyzer" in agents:
            try:
                context["repo_analysis"] = agents["deep_repo_analyzer"].run()
            except Exception as exc:
                logger.warning("Deep repository analysis failed: %s", exc)
                # Fallback to basic analyzer
                if "repo_analyzer" in agents:
                    context["repo_analysis"] = agents["repo_analyzer"].run()
        
        # Get metadata
        if "metadata_recommender" in agents:
            try:
                context["metadata"] = agents["metadata_recommender"].run(
                    context.get("repo_analysis", type("obj", (object,), {"readme": "", "files": {}})()).readme,
                    context.get("repo_analysis", type("obj", (object,), {"files": {}})()).files
                )
            except Exception as exc:
                logger.warning("Metadata recommendation failed: %s", exc)
        
        return context

    def _generate_review_from_collaboration(self, collaborative_result) -> Any:
        """Generate review from collaborative result."""
        # Create a review object based on quality gates
        quality_gates = collaborative_result.quality_gates
        passed_gates = sum(quality_gates.values())
        total_gates = len(quality_gates)
        
        score = (passed_gates / total_gates) * 10 if total_gates > 0 else 5.0
        
        issues = []
        recommendations = []
        
        if not quality_gates.get("factual_accuracy", True):
            issues.append("Some claims lack repository evidence")
            recommendations.append("Add more repository-specific examples")
        
        if not quality_gates.get("completeness", True):
            issues.append("Documentation may be incomplete")
            recommendations.append("Review and expand missing sections")
        
        return type("Review", (), {
            "score": score,
            "issues": issues,
            "strengths": ["Collaboratively generated content"],
            "recommendations": recommendations
        })()

    def _generate_fact_check_from_collaboration(self, collaborative_result) -> Any:
        """Generate fact check from collaborative result."""
        shared_memory = collaborative_result.shared_memory
        
        verified = []
        flagged = []
        
        for insight in shared_memory.insights.values():
            if insight.confidence > 0.7:
                verified.append(f"{insight.content} (confidence: {insight.confidence:.2f})")
            else:
                flagged.append(f"{insight.content} (confidence: {insight.confidence:.2f})")
        
        return type("FactCheck", (), {
            "claims_found": [insight.content for insight in shared_memory.insights.values()],
            "verified": verified,
            "flagged": flagged
        })()

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
        
        # Add enhanced nodes if available
        if "deep_repo_analyzer" in agents:
            def deep_analyze_repo(state):
                try:
                    repo_analysis = agents["deep_repo_analyzer"].run()
                except Exception as exc:
                    logger.exception("deep_repo_analyzer failed, falling back to standard analyzer", exc_info=exc)
                    # Fallback to standard analyzer
                    try:
                        repo_analysis = agents["repo_analyzer"].run()
                    except Exception as fallback_exc:
                        logger.exception("Standard repo_analyzer also failed", exc_info=fallback_exc)
                        repo_analysis = None
                return {**state, "repo_analysis": repo_analysis}
            workflow.add_node("deep_analyze_repo", deep_analyze_repo)
        
        if "intelligent_content_improver" in agents:
            def intelligent_improve_content(state):
                repo_analysis = state.get("repo_analysis")
                metadata = state.get("metadata")
                style_val = state.get("style", "Technical Blog")
                goal_val = state.get("goal", "")
                try:
                    content_improvement = agents["intelligent_content_improver"].run(
                        getattr(repo_analysis, "readme", ""), metadata, repo_analysis, style=style_val, goal=goal_val)
                except Exception as exc:
                    logger.exception("intelligent_content_improver failed", exc_info=exc)
                    content_improvement = None
                if content_improvement is None:
                    content_improvement = type("StubContent", (), {
                        "improved_readme": "# Improved README\n\nEnhanced content generation unavailable.",
                        "suggested_images": {}
                    })()
                return {**state, "content_improvement": content_improvement}
            workflow.add_node("intelligent_improve_content", intelligent_improve_content)
        
        if "comprehensive_fact_checker" in agents:
            def comprehensive_fact_check(state):
                repo_analysis = state.get("repo_analysis")
                content_improvement = state.get("content_improvement")
                try:
                    fact_check_result = agents["comprehensive_fact_checker"].run(
                        getattr(content_improvement, "improved_readme", ""),
                        repo_evidence=None,
                        files=getattr(repo_analysis, "files", {})
                    )
                except Exception as exc:
                    logger.exception("comprehensive_fact_checker failed", exc_info=exc)
                    fact_check_result = type("StubFactCheck", (), {
                        "claims_found": [],
                        "verified": [],
                        "flagged": ["Comprehensive fact-checking unavailable"]
                    })()
                return {**state, "fact_check": fact_check_result}
            workflow.add_node("comprehensive_fact_check", comprehensive_fact_check)
        
        if "seo_strategy_agent" in agents:
            def seo_optimization(state):
                repo_analysis = state.get("repo_analysis")
                metadata = state.get("metadata")
                try:
                    seo_strategy = agents["seo_strategy_agent"].generate_comprehensive_strategy(
                        repo_analysis, metadata, {}
                    )
                except Exception as exc:
                    logger.exception("seo_strategy_agent failed", exc_info=exc)
                    seo_strategy = None
                return {**state, "seo_strategy": seo_strategy}
            workflow.add_node("seo_optimization", seo_optimization)

        # Set workflow entry point and edges
        if "deep_repo_analyzer" in agents:
            workflow.set_entry_point("deep_analyze_repo")
            workflow.add_edge("deep_analyze_repo", "recommend_metadata")
        else:
            workflow.set_entry_point("analyze_repo")
            workflow.add_edge("analyze_repo", "recommend_metadata")
        
        # Add SEO optimization as sequential path if available
        if "seo_strategy_agent" in agents:
            workflow.add_edge("recommend_metadata", "seo_optimization")
        
        # Content improvement (after SEO if available)
        if "intelligent_content_improver" in agents:
            if "seo_strategy_agent" in agents:
                workflow.add_edge("seo_optimization", "intelligent_improve_content")
            else:
                workflow.add_edge("recommend_metadata", "intelligent_improve_content")
            workflow.add_edge("intelligent_improve_content", "review_content")
        else:
            if "seo_strategy_agent" in agents:
                workflow.add_edge("seo_optimization", "improve_content")
            else:
                workflow.add_edge("recommend_metadata", "improve_content")
            workflow.add_edge("improve_content", "review_content")
        
        # Fact checking
        if "comprehensive_fact_checker" in agents:
            workflow.add_edge("review_content", "comprehensive_fact_check")
            workflow.add_edge("comprehensive_fact_check", END)
        else:
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

        repo_analysis = result.get("repo_analysis")
        metadata = result.get("metadata")
        
        # Use collaborative content if available, otherwise use publication builder
        if "content_improvement" in result and hasattr(result["content_improvement"], "improved_readme"):
            publication_readme = result["content_improvement"].improved_readme
        else:
            publication_readme = self.publication_builder.build_readme(
                repo_analysis=repo_analysis,
                metadata=metadata,
                repo_source=repo_source,
                style=style,
                goal=goal,
            )

        return {
            "analysis": repo_analysis,
            "metadata": metadata,
            "content_improvement": result.get("content_improvement"),
            "review": result.get("review"),
            "fact_check": result.get("fact_check"),
            "publication_readme": publication_readme,
            "seo_strategy": result.get("seo_strategy"),
        }

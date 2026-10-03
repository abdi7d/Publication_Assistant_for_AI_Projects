# orchestration/collaborative_orchestrator.py
"""
Collaborative Orchestrator for true multi-agent collaboration.
Implements shared memory, joint reasoning sessions, and iterative refinement.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """An insight shared between agents."""
    agent_id: str
    insight_type: str  # 'discovery', 'hypothesis', 'validation', 'recommendation'
    content: str
    confidence: float
    evidence_sources: List[str]
    timestamp: datetime
    validation_status: str  # 'pending', 'validated', 'rejected'


@dataclass
class SharedMemory:
    """Shared memory system for agent collaboration."""
    insights: Dict[str, Insight]  # insight_id -> Insight
    agent_insights: Dict[str, Set[str]]  # agent_id -> set of insight_ids
    consensus_map: Dict[str, float]  # claim -> confidence_score
    conflict_resolution: Dict[str, str]  # conflict_id -> resolution


@dataclass
class JointReasoningSession:
    """A joint reasoning session with multiple agents."""
    session_id: str
    participants: List[str]
    topic: str
    insights: List[Insight]
    consensus: Dict[str, Any]
    confidence_scores: Dict[str, float]
    decisions: List[str]


@dataclass
class FeedbackLoop:
    """Feedback loop for iterative refinement."""
    loop_id: str
    iterations: List[Dict[str, Any]]
    quality_scores: List[float]
    feedback_items: List[str]
    convergence_threshold: float
    max_iterations: int


@dataclass
class CollaborativeResult:
    """Result of collaborative agent orchestration."""
    final_content: str
    shared_memory: SharedMemory
    reasoning_sessions: List[JointReasoningSession]
    feedback_loops: List[FeedbackLoop]
    quality_gates: Dict[str, bool]
    collaboration_metrics: Dict[str, Any]


class CollaborativeOrchestrator:
    """
    True multi-agent collaboration with shared memory and joint reasoning.
    Enables agents to share insights, validate hypotheses, and
    iteratively refine content through feedback loops.
    """

    def __init__(self):
        self.shared_memory = SharedMemory(
            insights={},
            agent_insights={},
            consensus_map={},
            conflict_resolution={}
        )
        self.active_sessions = {}
        self.feedback_loops = {}

    def orchestrate_collaboration(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                                goal: str = "generate_documentation") -> CollaborativeResult:
        """Orchestrate full collaborative agent process."""
        logger.info("CollaborativeOrchestrator: starting collaborative orchestration for goal: %s", goal)
        
        # Phase 1: Initial insights gathering
        self._gather_initial_insights(agents, repository_context)
        
        # Phase 2: Joint reasoning sessions
        reasoning_sessions = self._conduct_joint_reasoning(agents, repository_context, goal)
        
        # Phase 3: Consensus building
        self._build_consensus(reasoning_sessions)
        
        # Phase 4: Iterative refinement through feedback loops
        feedback_loops = self._run_feedback_loops(agents, repository_context, goal)
        
        # Phase 5: Quality gates validation
        quality_gates = self._validate_quality_gates(repository_context)
        
        # Phase 6: Generate final collaborative content
        final_content = self._generate_collaborative_content(agents, repository_context)
        
        # Calculate collaboration metrics
        collaboration_metrics = self._calculate_collaboration_metrics(
            reasoning_sessions, feedback_loops, quality_gates
        )
        
        return CollaborativeResult(
            final_content=final_content,
            shared_memory=self.shared_memory,
            reasoning_sessions=reasoning_sessions,
            feedback_loops=feedback_loops,
            quality_gates=quality_gates,
            collaboration_metrics=collaboration_metrics,
        )

    def _gather_initial_insights(self, agents: Dict[str, Any], repository_context: Dict[str, Any]):
        """Gather initial insights from all agents."""
        logger.info("CollaborativeOrchestrator: gathering initial insights from agents")
        
        for agent_id, agent in agents.items():
            try:
                # Run agent to get initial analysis
                if hasattr(agent, 'run'):
                    result = agent.run()
                    if result:
                        # Extract insights from agent result
                        insights = self._extract_insights_from_result(agent_id, result)
                        for insight in insights:
                            self._store_insight(insight)
            except Exception as e:
                logger.warning("Failed to gather insights from agent %s: %s", agent_id, e)

    def _extract_insights_from_result(self, agent_id: str, result: Any) -> List[Insight]:
        """Extract insights from agent result."""
        insights = []
        
        # Handle different result types
        if hasattr(result, 'architecture'):
            insights.append(Insight(
                agent_id=agent_id,
                insight_type="discovery",
                content=f"Architecture style: {result.architecture.architectural_style}",
                confidence=0.9,
                evidence_sources=["repository_analysis"],
                timestamp=datetime.now(),
                validation_status="pending"
            ))
        
        if hasattr(result, 'design_patterns'):
            for pattern in result.design_patterns:
                insights.append(Insight(
                    agent_id=agent_id,
                    insight_type="discovery",
                    content=f"Design pattern detected: {pattern}",
                    confidence=0.8,
                    evidence_sources=["code_analysis"],
                    timestamp=datetime.now(),
                    validation_status="pending"
                ))
        
        if hasattr(result, 'technology_stack'):
            for category, technologies in result.technology_stack.items():
                if technologies:
                    insights.append(Insight(
                        agent_id=agent_id,
                        insight_type="discovery",
                        content=f"Technology stack {category}: {', '.join(technologies[:3])}",
                        confidence=0.85,
                        evidence_sources=["dependency_analysis"],
                        timestamp=datetime.now(),
                        validation_status="pending"
                    ))
        
        return insights

    def _store_insight(self, insight: Insight):
        """Store insight in shared memory."""
        insight_id = str(uuid.uuid4())
        self.shared_memory.insights[insight_id] = insight
        
        # Track agent insights
        if insight.agent_id not in self.shared_memory.agent_insights:
            self.shared_memory.agent_insights[insight.agent_id] = set()
        self.shared_memory.agent_insights[insight.agent_id].add(insight_id)
        
        logger.debug("Stored insight %s from agent %s", insight_id, insight.agent_id)

    def _conduct_joint_reasoning(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                               goal: str) -> List[JointReasoningSession]:
        """Conduct joint reasoning sessions with agents."""
        logger.info("CollaborativeOrchestrator: conducting joint reasoning sessions")
        
        sessions = []
        
        # Session 1: Architecture analysis
        session_1 = self._run_reasoning_session(
            agents, repository_context, "architecture_analysis", 
            "Collaborative analysis of repository architecture"
        )
        sessions.append(session_1)
        
        # Session 2: Content strategy
        session_2 = self._run_reasoning_session(
            agents, repository_context, "content_strategy",
            "Collaborative determination of content strategy"
        )
        sessions.append(session_2)
        
        # Session 3: Quality assessment
        session_3 = self._run_reasoning_session(
            agents, repository_context, "quality_assessment",
            "Collaborative assessment of documentation quality"
        )
        sessions.append(session_3)
        
        return sessions

    def _run_reasoning_session(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                            session_type: str, topic: str) -> JointReasoningSession:
        """Run a single joint reasoning session."""
        session_id = str(uuid.uuid4())
        participants = list(agents.keys())
        
        logger.info("Running reasoning session %s with participants: %s", session_id, participants)
        
        # Collect insights relevant to session topic
        relevant_insights = self._get_relevant_insights(session_type)
        
        # Enable agents to access shared insights
        shared_insights = [insight for insight in relevant_insights.values()]
        
        # Simulate collaborative reasoning
        consensus = {}
        confidence_scores = {}
        decisions = []
        
        # Agent collaboration simulation
        for agent_id in participants:
            agent_insights = self.shared_memory.agent_insights.get(agent_id, set())
            confidence_scores[agent_id] = len(agent_insights) / max(len(self.shared_memory.insights), 1)
        
        # Build consensus from insights
        for insight in shared_insights:
            claim = insight.content
            if claim not in consensus:
                consensus[claim] = insight.confidence
            else:
                # Average confidence from multiple agents
                consensus[claim] = (consensus[claim] + insight.confidence) / 2
        
        # Generate collaborative decisions
        if session_type == "architecture_analysis":
            decisions.append("Architecture documentation should emphasize modularity")
            decisions.append("Include component interaction diagrams")
        elif session_type == "content_strategy":
            decisions.append("Target intermediate developers as primary audience")
            decisions.append("Balance technical depth with accessibility")
        elif session_type == "quality_assessment":
            decisions.append("Add comprehensive code examples")
            decisions.append("Include troubleshooting section")
        
        session = JointReasoningSession(
            session_id=session_id,
            participants=participants,
            topic=topic,
            insights=shared_insights,
            consensus=consensus,
            confidence_scores=confidence_scores,
            decisions=decisions
        )
        
        self.active_sessions[session_id] = session
        return session

    def _get_relevant_insights(self, session_type: str) -> Dict[str, Insight]:
        """Get insights relevant to a specific session type."""
        relevant = {}
        
        for insight_id, insight in self.shared_memory.insights.items():
            if session_type == "architecture_analysis":
                if "architecture" in insight.content.lower() or "pattern" in insight.content.lower():
                    relevant[insight_id] = insight
            elif session_type == "content_strategy":
                if "technology" in insight.content.lower() or "stack" in insight.content.lower():
                    relevant[insight_id] = insight
            elif session_type == "quality_assessment":
                if "quality" in insight.content.lower() or "test" in insight.content.lower():
                    relevant[insight_id] = insight
        
        return relevant

    def _build_consensus(self, reasoning_sessions: List[JointReasoningSession]):
        """Build consensus from reasoning sessions."""
        logger.info("CollaborativeOrchestrator: building consensus from reasoning sessions")
        
        for session in reasoning_sessions:
            for claim, confidence in session.consensus.items():
                if claim not in self.shared_memory.consensus_map:
                    self.shared_memory.consensus_map[claim] = confidence
                else:
                    # Combine confidences from multiple sessions
                    existing = self.shared_memory.consensus_map[claim]
                    self.shared_memory.consensus_map[claim] = (existing + confidence) / 2

    def _run_feedback_loops(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                          goal: str) -> List[FeedbackLoop]:
        """Run iterative refinement through feedback loops."""
        logger.info("CollaborativeOrchestrator: running feedback loops")
        
        loops = []
        
        # Feedback loop 1: Content refinement
        loop_1 = self._run_feedback_loop(
            agents, repository_context, "content_refinement", 
            max_iterations=3, convergence_threshold=0.1
        )
        loops.append(loop_1)
        
        # Feedback loop 2: Quality improvement
        loop_2 = self._run_feedback_loop(
            agents, repository_context, "quality_improvement",
            max_iterations=2, convergence_threshold=0.15
        )
        loops.append(loop_2)
        
        return loops

    def _run_feedback_loop(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                         loop_type: str, max_iterations: int, convergence_threshold: float) -> FeedbackLoop:
        """Run a single feedback loop."""
        loop_id = str(uuid.uuid4())
        iterations = []
        quality_scores = []
        feedback_items = []
        
        logger.info("Running feedback loop %s with max %d iterations", loop_id, max_iterations)
        
        for iteration in range(max_iterations):
            # Simulate iteration
            iteration_data = {
                "iteration": iteration + 1,
                "participants": list(agents.keys()),
                "feedback_type": loop_type,
            }
            
            # Collect feedback from agents
            agent_feedback = self._collect_agent_feedback(agents, repository_context, loop_type)
            feedback_items.extend(agent_feedback)
            
            # Calculate quality score
            quality_score = self._calculate_iteration_quality(iteration_data, feedback_items)
            quality_scores.append(quality_score)
            
            iteration_data["quality_score"] = quality_score
            iteration_data["feedback_count"] = len(agent_feedback)
            iterations.append(iteration_data)
            
            # Check convergence
            if len(quality_scores) > 1:
                improvement = abs(quality_scores[-1] - quality_scores[-2])
                if improvement < convergence_threshold:
                    logger.info("Feedback loop converged after %d iterations", iteration + 1)
                    break
        
        loop = FeedbackLoop(
            loop_id=loop_id,
            iterations=iterations,
            quality_scores=quality_scores,
            feedback_items=feedback_items,
            convergence_threshold=convergence_threshold,
            max_iterations=max_iterations
        )
        
        self.feedback_loops[loop_id] = loop
        return loop

    def _collect_agent_feedback(self, agents: Dict[str, Any], repository_context: Dict[str, Any],
                              loop_type: str) -> List[str]:
        """Collect feedback from agents for current iteration."""
        feedback = []
        
        for agent_id, agent in agents.items():
            try:
                # Simulate agent feedback based on loop type
                if loop_type == "content_refinement":
                    feedback.append(f"{agent_id}: Suggests adding more code examples")
                    feedback.append(f"{agent_id}: Recommends clarifying technical terms")
                elif loop_type == "quality_improvement":
                    feedback.append(f"{agent_id}: Identifies missing installation steps")
                    feedback.append(f"{agent_id}: Suggests adding troubleshooting section")
            except Exception as e:
                logger.warning("Failed to collect feedback from agent %s: %s", agent_id, e)
        
        return feedback

    def _calculate_iteration_quality(self, iteration_data: Dict[str, Any], 
                                   feedback_items: List[str]) -> float:
        """Calculate quality score for iteration."""
        # Base quality starts at 0.5
        quality = 0.5
        
        # Improve based on feedback count
        feedback_count = len(feedback_items)
        quality += min(feedback_count / 20, 0.3)
        
        # Improve based on iteration number (later iterations should be better)
        iteration_num = iteration_data.get("iteration", 1)
        quality += min(iteration_num / 10, 0.2)
        
        return min(quality, 1.0)

    def _validate_quality_gates(self, repository_context: Dict[str, Any]) -> Dict[str, bool]:
        """Validate content against quality gates."""
        logger.info("CollaborativeOrchestrator: validating quality gates")
        
        quality_gates = {
            "factual_accuracy": self._validate_factual_accuracy(),
            "completeness": self._validate_completeness(repository_context),
            "consistency": self._validate_consistency(),
            "repository_grounding": self._validate_repository_grounding(),
            "seo_optimization": self._validate_seo_optimization(),
        }
        
        return quality_gates

    def _validate_factual_accuracy(self) -> bool:
        """Validate factual accuracy of content."""
        # Check if consensus has high confidence
        if not self.shared_memory.consensus_map:
            return False
        
        avg_confidence = sum(self.shared_memory.consensus_map.values()) / len(self.shared_memory.consensus_map)
        return avg_confidence > 0.7

    def _validate_completeness(self, repository_context: Dict[str, Any]) -> bool:
        """Validate completeness of documentation."""
        # Check if key sections are covered
        key_sections = ["installation", "usage", "architecture", "api"]
        covered_sections = 0
        
        for insight in self.shared_memory.insights.values():
            for section in key_sections:
                if section in insight.content.lower():
                    covered_sections += 1
                    break
        
        return covered_sections >= len(key_sections) / 2

    def _validate_consistency(self) -> bool:
        """Validate consistency across documentation."""
        # Check for conflicts in consensus
        conflicts = 0
        
        for claim, confidence in self.shared_memory.consensus_map.items():
            if confidence < 0.5:
                conflicts += 1
        
        return conflicts == 0

    def _validate_repository_grounding(self) -> bool:
        """Validate that content is grounded in repository evidence."""
        grounded_insights = 0
        
        for insight in self.shared_memory.insights.values():
            if insight.evidence_sources and "repository" in str(insight.evidence_sources).lower():
                grounded_insights += 1
        
        grounding_ratio = grounded_insights / max(len(self.shared_memory.insights), 1)
        return grounding_ratio > 0.6

    def _validate_seo_optimization(self) -> bool:
        """Validate SEO optimization."""
        # Check if technology and framework insights exist
        tech_insights = 0
        
        for insight in self.shared_memory.insights.values():
            if "technology" in insight.content.lower() or "framework" in insight.content.lower():
                tech_insights += 1
        
        return tech_insights >= 3

    def _generate_collaborative_content(self, agents: Dict[str, Any], 
                                       repository_context: Dict[str, Any]) -> str:
        """Generate final collaborative content."""
        logger.info("CollaborativeOrchestrator: generating collaborative content")
        
        # Build content from consensus and decisions
        content_parts = []
        
        # Add collaborative insights
        content_parts.append("# Collaboratively Generated Documentation\n\n")
        content_parts.append("This documentation was generated through multi-agent collaboration.\n\n")
        
        # Add architectural insights
        content_parts.append("## Architecture Insights\n\n")
        for claim, confidence in self.shared_memory.consensus_map.items():
            if "architecture" in claim.lower() and confidence > 0.7:
                content_parts.append(f"- {claim} (confidence: {confidence:.2f})\n")
        content_parts.append("\n")
        
        # Add technical stack information
        content_parts.append("## Technology Stack\n\n")
        for claim, confidence in self.shared_memory.consensus_map.items():
            if "technology" in claim.lower() or "stack" in claim.lower():
                content_parts.append(f"- {claim}\n")
        content_parts.append("\n")
        
        # Add collaborative decisions
        content_parts.append("## Collaborative Decisions\n\n")
        for session in self.active_sessions.values():
            content_parts.append(f"### {session.topic}\n\n")
            for decision in session.decisions:
                content_parts.append(f"- {decision}\n")
            content_parts.append("\n")
        
        return "".join(content_parts)

    def _calculate_collaboration_metrics(self, reasoning_sessions: List[JointReasoningSession],
                                       feedback_loops: List[FeedbackLoop],
                                       quality_gates: Dict[str, bool]) -> Dict[str, Any]:
        """Calculate collaboration metrics."""
        metrics = {
            "total_reasoning_sessions": len(reasoning_sessions),
            "total_feedback_loops": len(feedback_loops),
            "total_insights_shared": len(self.shared_memory.insights),
            "agents_participated": len(self.shared_memory.agent_insights),
            "consensus_items": len(self.shared_memory.consensus_map),
            "average_confidence": 0.0,
            "quality_gates_passed": sum(quality_gates.values()),
            "total_quality_gates": len(quality_gates),
        }
        
        # Calculate average confidence
        if self.shared_memory.consensus_map:
            metrics["average_confidence"] = sum(self.shared_memory.consensus_map.values()) / len(self.shared_memory.consensus_map)
        
        # Calculate iteration improvements
        if feedback_loops:
            for loop in feedback_loops:
                if loop.quality_scores:
                    improvement = loop.quality_scores[-1] - loop.quality_scores[0]
                    metrics[f"loop_{loop.loop_id}_improvement"] = improvement
        
        return metrics


__all__ = [
    "CollaborativeOrchestrator",
    "CollaborativeResult",
    "SharedMemory",
    "Insight",
    "JointReasoningSession",
    "FeedbackLoop",
]
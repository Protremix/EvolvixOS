"""
Agent Learning Loop — Phase 19

Enables AI agents to learn from past execution results and improve
over time. Features:
- Performance tracking per agent and task type
- Pattern recognition from successful/failed executions
- Prompt optimization suggestions based on outcomes
- Learning feedback injection into future agent calls
- Performance trend analysis and improvement metrics
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import threading
import statistics
from app.core.logging import get_logger

logger = get_logger("service.agent_learning")


@dataclass
class AgentExecution:
    """Record of a single agent execution for learning analysis."""
    id: str = field(default_factory=lambda: f"exec-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_name: str = ""
    task_type: str = ""
    status: str = "completed"  # completed, failed
    score: Optional[float] = None
    verdict: Optional[str] = None
    tokens_used: int = 0
    latency_ms: float = 0.0
    findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    recommendations_count: int = 0
    input_summary: str = ""
    output_summary: str = ""
    session_id: Optional[str] = None  # collaboration session if applicable
    project: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LearningInsight:
    """An insight derived from analyzing agent execution history."""
    id: str = field(default_factory=lambda: f"insight-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_name: str = ""
    task_type: str = ""
    insight_type: str = ""  # performance_trend, failure_pattern, success_pattern, prompt_improvement, score_regression
    description: str = ""
    data: dict = field(default_factory=dict)
    confidence: float = 0.5
    actionable: bool = False
    recommendation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PromptOptimization:
    """A suggested prompt optimization for an agent."""
    id: str = field(default_factory=lambda: f"prompt-opt-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_name: str = ""
    task_type: str = ""
    current_issue: str = ""
    suggested_improvement: str = ""
    evidence: str = ""  # what data supports this suggestion
    confidence: float = 0.5
    applied: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class AgentLearningLoop:
    """
    Learns from agent execution history and generates insights
    for continuous improvement.
    """

    def __init__(self, max_executions: int = 5000, max_insights: int = 500):
        self._executions: deque = deque(maxlen=max_executions)
        self._insights: list[LearningInsight] = []
        self._prompt_opts: list[PromptOptimization] = []
        self._max_insights = max_insights
        self._lock = threading.Lock()

        # Per-agent running stats
        self._agent_stats: dict[str, dict] = defaultdict(lambda: {
            "total": 0, "completed": 0, "failed": 0,
            "scores": [], "latencies": [], "tokens": [],
            "go_count": 0, "nogo_count": 0,
            "recent_scores": deque(maxlen=20),  # last 20 for trend
        })

        # Per task-type stats
        self._task_stats: dict[str, dict] = defaultdict(lambda: {
            "total": 0, "completed": 0, "failed": 0,
            "scores": [], "avg_score": 0.0,
        })

    def record_execution(self, execution: AgentExecution) -> None:
        """Record an agent execution for learning analysis."""
        with self._lock:
            self._executions.append(execution)

            # Update agent stats
            stats = self._agent_stats[execution.agent_name]
            stats["total"] += 1
            if execution.status == "completed":
                stats["completed"] += 1
            else:
                stats["failed"] += 1
            if execution.score is not None:
                stats["scores"].append(execution.score)
                stats["recent_scores"].append(execution.score)
            if execution.latency_ms:
                stats["latencies"].append(execution.latency_ms)
            if execution.tokens_used:
                stats["tokens"].append(execution.tokens_used)
            if execution.verdict == "GO":
                stats["go_count"] += 1
            elif execution.verdict == "NO-GO":
                stats["nogo_count"] += 1

            # Update task stats
            tstats = self._task_stats[execution.task_type]
            tstats["total"] += 1
            if execution.status == "completed":
                tstats["completed"] += 1
            else:
                tstats["failed"] += 1
            if execution.score is not None:
                tstats["scores"].append(execution.score)
                if tstats["scores"]:
                    tstats["avg_score"] = round(statistics.mean(tstats["scores"]), 2)

        logger.info("execution_recorded", agent=execution.agent_name,
                     task=execution.task_type, score=execution.score)

    def analyze(self) -> list[LearningInsight]:
        """Analyze execution history and generate insights."""
        insights: list[LearningInsight] = []

        if len(self._executions) < 3:
            return insights  # Not enough data

        # 1. Performance trend analysis per agent
        for agent_name, stats in self._agent_stats.items():
            if len(stats["recent_scores"]) >= 3:
                recent = list(stats["recent_scores"])
                early = recent[:len(recent)//2]
                late = recent[len(recent)//2:]
                if early and late:
                    early_avg = statistics.mean(early)
                    late_avg = statistics.mean(late)
                    delta = late_avg - early_avg

                    if delta > 0.5:
                        insights.append(LearningInsight(
                            agent_name=agent_name,
                            insight_type="performance_trend",
                            description=f"{agent_name} improving: early avg {early_avg:.1f} → recent avg {late_avg:.1f} (+{delta:.1f})",
                            data={"early_avg": early_avg, "late_avg": late_avg, "delta": delta},
                            confidence=min(0.9, 0.5 + len(recent) * 0.05),
                            actionable=False,
                            recommendation="Continue current approach — performance is improving.",
                        ))
                    elif delta < -0.5:
                        insights.append(LearningInsight(
                            agent_name=agent_name,
                            insight_type="score_regression",
                            description=f"{agent_name} regressing: early avg {early_avg:.1f} → recent avg {late_avg:.1f} ({delta:.1f})",
                            data={"early_avg": early_avg, "late_avg": late_avg, "delta": delta},
                            confidence=min(0.9, 0.5 + len(recent) * 0.05),
                            actionable=True,
                            recommendation=f"Review {agent_name} recent inputs — score is declining. Consider prompt refinement.",
                        ))

        # 2. Failure pattern detection
        for agent_name, stats in self._agent_stats.items():
            if stats["total"] >= 5:
                failure_rate = stats["failed"] / stats["total"]
                if failure_rate > 0.3:
                    insights.append(LearningInsight(
                        agent_name=agent_name,
                        insight_type="failure_pattern",
                        description=f"{agent_name} has high failure rate: {failure_rate*100:.0f}% ({stats['failed']}/{stats['total']})",
                        data={"failure_rate": failure_rate, "total": stats["total"], "failed": stats["failed"]},
                        confidence=0.8,
                        actionable=True,
                        recommendation=f"Investigate {agent_name} failure cases — failure rate above 30%.",
                    ))

        # 3. Token efficiency analysis
        for agent_name, stats in self._agent_stats.items():
            if len(stats["tokens"]) >= 3:
                avg_tokens = statistics.mean(stats["tokens"])
                recent_tokens = list(stats["tokens"])[-5:]
                recent_avg = statistics.mean(recent_tokens) if recent_tokens else avg_tokens
                if recent_avg > avg_tokens * 1.5:
                    insights.append(LearningInsight(
                        agent_name=agent_name,
                        insight_type="token_inefficiency",
                        description=f"{agent_name} token usage increasing: avg {avg_tokens:.0f} → recent {recent_avg:.0f}",
                        data={"avg_tokens": avg_tokens, "recent_avg": recent_avg},
                        confidence=0.7,
                        actionable=True,
                        recommendation=f"Review {agent_name} prompts — token usage is increasing. Consider tightening prompt scope.",
                    ))

        # 4. Verdict distribution analysis
        for agent_name, stats in self._agent_stats.items():
            total_verdicts = stats["go_count"] + stats["nogo_count"]
            if total_verdicts >= 5:
                go_rate = stats["go_count"] / total_verdicts
                if go_rate > 0.95:
                    insights.append(LearningInsight(
                        agent_name=agent_name,
                        insight_type="success_pattern",
                        description=f"{agent_name} always returns GO ({go_rate*100:.0f}%) — may be too lenient",
                        data={"go_rate": go_rate, "total": total_verdicts},
                        confidence=0.6,
                        actionable=True,
                        recommendation=f"{agent_name} may need stricter review criteria — {go_rate*100:.0f}% GO rate.",
                    ))
                elif go_rate < 0.2:
                    insights.append(LearningInsight(
                        agent_name=agent_name,
                        insight_type="failure_pattern",
                        description=f"{agent_name} rarely gives GO ({go_rate*100:.0f}%) — may be too strict",
                        data={"go_rate": go_rate, "total": total_verdicts},
                        confidence=0.6,
                        actionable=True,
                        recommendation=f"{agent_name} may need relaxed criteria — only {go_rate*100:.0f}% GO rate.",
                    ))

        # 5. Prompt optimization suggestions
        for agent_name, stats in self._agent_stats.items():
            if len(stats["scores"]) >= 5:
                avg_score = statistics.mean(stats["scores"])
                if avg_score < 7.0:
                    self._prompt_opts.append(PromptOptimization(
                        agent_name=agent_name,
                        current_issue=f"Average score {avg_score:.1f}/10 is below threshold",
                        suggested_improvement=f"Add more specific review criteria to {agent_name} system prompt. Include domain-specific checklists.",
                        evidence=f"Based on {len(stats['scores'])} executions, avg={avg_score:.1f}",
                        confidence=0.7,
                    ))
                elif avg_score > 8.5 and stats["nogo_count"] == 0:
                    self._prompt_opts.append(PromptOptimization(
                        agent_name=agent_name,
                        current_issue=f"Agent consistently scores {avg_score:.1f} with 0 NO-GO verdicts — may lack critical analysis",
                        suggested_improvement=f"Add adversarial review criteria. Challenge the agent to find at least one issue per review.",
                        evidence=f"Based on {len(stats['scores'])} executions, avg={avg_score:.1f}, 0 NO-GO",
                        confidence=0.6,
                    ))

        # Store insights
        with self._lock:
            self._insights.extend(insights)
            if len(self._insights) > self._max_insights:
                self._insights = self._insights[-self._max_insights:]

        logger.info("learning_analysis_complete", new_insights=len(insights), total=len(self._insights))
        return insights

    def get_insights(self, agent_name: str = None, insight_type: str = None,
                     limit: int = 50) -> list[LearningInsight]:
        """Get insights, optionally filtered."""
        insights = self._insights
        if agent_name:
            insights = [i for i in insights if i.agent_name == agent_name]
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        return list(reversed(insights))[:limit]

    def get_prompt_optimizations(self, agent_name: str = None,
                                  limit: int = 20) -> list[PromptOptimization]:
        """Get prompt optimization suggestions."""
        opts = self._prompt_opts
        if agent_name:
            opts = [o for o in opts if o.agent_name == agent_name]
        return list(reversed(opts))[:limit]

    def get_agent_performance(self, agent_name: str) -> dict:
        """Get performance metrics for a specific agent."""
        stats = self._agent_stats.get(agent_name, {})
        if not stats:
            return {"agent_name": agent_name, "total": 0}

        scores = stats.get("scores", [])
        latencies = stats.get("latencies", [])
        tokens = stats.get("tokens", [])

        return {
            "agent_name": agent_name,
            "total_executions": stats["total"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "success_rate": round(stats["completed"] / max(stats["total"], 1) * 100, 1),
            "avg_score": round(statistics.mean(scores), 2) if scores else 0,
            "median_score": statistics.median(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "recent_trend": list(stats.get("recent_scores", [])),
            "avg_latency_ms": round(statistics.mean(latencies), 1) if latencies else 0,
            "avg_tokens": round(statistics.mean(tokens), 0) if tokens else 0,
            "go_count": stats["go_count"],
            "nogo_count": stats["nogo_count"],
            "go_rate": round(stats["go_count"] / max(stats["go_count"] + stats["nogo_count"], 1) * 100, 1),
        }

    def get_all_performance(self) -> list[dict]:
        """Get performance metrics for all agents."""
        return [self.get_agent_performance(name) for name in self._agent_stats.keys()]

    def get_learning_summary(self) -> dict:
        """Get a summary of the learning system state."""
        return {
            "total_executions": len(self._executions),
            "total_insights": len(self._insights),
            "total_prompt_opts": len(self._prompt_opts),
            "agents_tracked": len(self._agent_stats),
            "task_types_tracked": len(self._task_stats),
            "actionable_insights": sum(1 for i in self._insights if i.actionable),
            "insight_types": list(set(i.insight_type for i in self._insights)),
            "task_performance": {
                task: {"avg_score": s["avg_score"], "total": s["total"],
                       "success_rate": round(s["completed"]/max(s["total"],1)*100, 1)}
                for task, s in self._task_stats.items()
            },
        }

    def get_feedback_for_agent(self, agent_name: str, task_type: str = None) -> dict:
        """
        Get learning feedback to inject into an agent's next execution.
        This is the core of the learning loop — past performance informs future calls.
        """
        stats = self._agent_stats.get(agent_name, {})
        if not stats or stats["total"] < 2:
            return {"feedback": "Insufficient history for learning feedback.", "applied": False}

        feedback_parts = []
        scores = stats.get("scores", [])

        if scores:
            avg = statistics.mean(scores)
            recent = list(stats.get("recent_scores", []))
            if len(recent) >= 3:
                recent_avg = statistics.mean(recent)
                if recent_avg > avg:
                    feedback_parts.append(f"Your recent performance ({recent_avg:.1f}) is above your average ({avg:.1f}). Keep up the good work.")
                elif recent_avg < avg:
                    feedback_parts.append(f"Your recent performance ({recent_avg:.1f}) is below your average ({avg:.1f}). Focus on thoroughness.")

            if avg < 7.0:
                feedback_parts.append(f"Your average score is {avg:.1f}/10. Be more thorough and look for issues you might be missing.")
            elif avg > 8.5 and stats["nogo_count"] == 0:
                feedback_parts.append("You have a perfect GO rate. Challenge yourself to find at least one improvement per review.")

        # Failure rate feedback
        failure_rate = stats["failed"] / max(stats["total"], 1)
        if failure_rate > 0.2:
            feedback_parts.append(f"Your failure rate is {failure_rate*100:.0f}%. Pay attention to input format and requirements.")

        # Token efficiency
        tokens = stats.get("tokens", [])
        if len(tokens) >= 3:
            avg_tokens = statistics.mean(tokens)
            feedback_parts.append(f"Average token usage: {avg_tokens:.0f}. Be concise but thorough.")

        # Past insights for this agent
        agent_insights = [i for i in self._insights if i.agent_name == agent_name]
        if agent_insights:
            recent_insight = agent_insights[-1]
            feedback_parts.append(f"Past insight: {recent_insight.description}")

        return {
            "feedback": " ".join(feedback_parts) if feedback_parts else "No specific feedback — perform as trained.",
            "applied": len(feedback_parts) > 0,
            "stats": {
                "total_executions": stats["total"],
                "avg_score": round(statistics.mean(scores), 2) if scores else 0,
                "go_rate": round(stats["go_count"] / max(stats["go_count"] + stats["nogo_count"], 1) * 100, 1),
            },
        }

    def clear(self):
        """Clear all learning data (for testing)."""
        with self._lock:
            self._executions.clear()
            self._insights.clear()
            self._prompt_opts.clear()
            self._agent_stats.clear()
            self._task_stats.clear()


# Singleton
_service: Optional[AgentLearningLoop] = None


def get_learning_loop() -> AgentLearningLoop:
    global _service
    if _service is None:
        _service = AgentLearningLoop()
    return _service

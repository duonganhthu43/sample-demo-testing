"""
Quality Reviewer Agent
Reviews research outputs and provides feedback for refinement
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config
from ..utils.prompts import QUALITY_REVIEWER_SYSTEM


@dataclass
class QualityScore:
    """Quality assessment scores"""
    completeness: float = 0.0  # 0-1 scale
    accuracy: float = 0.0
    depth: float = 0.0
    relevance: float = 0.0
    clarity: float = 0.0
    overall: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "depth": self.depth,
            "relevance": self.relevance,
            "clarity": self.clarity,
            "overall": self.overall
        }


@dataclass
class QualityReview:
    """Quality review result with feedback"""
    passed: bool
    scores: QualityScore
    gaps: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    feedback: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    requires_refinement: bool = False
    refinement_areas: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "passed": self.passed,
            "scores": self.scores.to_dict(),
            "gaps": self.gaps,
            "strengths": self.strengths,
            "feedback": self.feedback,
            "recommendations": self.recommendations,
            "requires_refinement": self.requires_refinement,
            "refinement_areas": self.refinement_areas,
            "timestamp": self.timestamp
        }


class QualityReviewerAgent:
    """
    Agent that reviews research quality and provides feedback
    """

    def __init__(self, config: Optional[Any] = None, quality_threshold: float = 0.7):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="quality_reviewer_agent")
        self.llm_params = self.config.get_llm_params()
        self.quality_threshold = quality_threshold

        print("QualityReviewerAgent initialized")

    def review_research(
        self,
        company_name: str,
        objectives: List[str],
        research_results: List[Dict[str, Any]],
        analysis_results: List[Dict[str, Any]],
        specialized_results: Optional[List[Dict[str, Any]]] = None
    ) -> QualityReview:
        """
        Review the quality of research outputs

        Args:
            company_name: Company being researched
            objectives: Original research objectives
            research_results: Results from research agents
            analysis_results: Results from analysis agents
            specialized_results: Results from specialized agents

        Returns:
            Quality review with feedback
        """
        start_time = time.time()
        print(f"Starting: quality_reviewer_agent - Reviewing research for {company_name}")

        # Prepare summary of results
        results_summary = self._summarize_results(
            research_results,
            analysis_results,
            specialized_results or []
        )

        prompt = f"""Review the quality of this market research project.

Company: {company_name}

Original Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Research Output Summary:
{results_summary}

Evaluate the research quality on these dimensions (score 0-1):
1. Completeness: Are all objectives addressed?
2. Accuracy: Is the information credible and well-sourced?
3. Depth: Is the analysis sufficiently deep and insightful?
4. Relevance: Is the content relevant to objectives?
5. Clarity: Is the output clear and well-organized?

Identify:
- Gaps (missing information or analysis)
- Strengths (what was done well)
- Specific feedback for improvement
- Recommendations for next steps
- Whether refinement is needed

Return as JSON:
{{
    "scores": {{
        "completeness": 0.85,
        "accuracy": 0.90,
        "depth": 0.75,
        "relevance": 0.95,
        "clarity": 0.88,
        "overall": 0.86
    }},
    "gaps": ["gap1", "gap2", ...],
    "strengths": ["strength1", "strength2", ...],
    "feedback": ["feedback1", "feedback2", ...],
    "recommendations": ["rec1", "rec2", ...],
    "requires_refinement": true/false,
    "refinement_areas": ["area1", "area2", ...]
}}"""

        messages = [
            {"role": "system", "content": QUALITY_REVIEWER_SYSTEM},
            {"role": "user", "content": prompt}
        ]

        # Call LLM
        if self.config.llm.provider == "openai":
            response = self.llm_client.chat.completions.create(
                messages=messages,
                **self.llm_params
            )
            content = response.choices[0].message.content

        elif self.config.llm.provider == "anthropic":
            response = self.llm_client.messages.create(
                system=QUALITY_REVIEWER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        review_data = self._parse_json_response(content)

        # Build quality scores
        scores_data = review_data.get("scores", {})
        scores = QualityScore(
            completeness=scores_data.get("completeness", 0.7),
            accuracy=scores_data.get("accuracy", 0.7),
            depth=scores_data.get("depth", 0.7),
            relevance=scores_data.get("relevance", 0.7),
            clarity=scores_data.get("clarity", 0.7),
            overall=scores_data.get("overall", 0.7)
        )

        # Determine if passed
        passed = scores.overall >= self.quality_threshold

        review = QualityReview(
            passed=passed,
            scores=scores,
            gaps=review_data.get("gaps", []),
            strengths=review_data.get("strengths", []),
            feedback=review_data.get("feedback", []),
            recommendations=review_data.get("recommendations", []),
            requires_refinement=review_data.get("requires_refinement", not passed),
            refinement_areas=review_data.get("refinement_areas", []),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        duration = time.time() - start_time
        print(f"Complete: quality_reviewer_agent - {duration:.2f}s")
        print(f"Quality Score: {scores.overall:.2f} ({'PASSED' if passed else 'NEEDS REFINEMENT'})")

        return review

    def review_report(
        self,
        report_content: str,
        objectives: List[str]
    ) -> QualityReview:
        """
        Review the quality of a generated report

        Args:
            report_content: The report content to review
            objectives: Original research objectives

        Returns:
            Quality review of the report
        """
        start_time = time.time()
        print("Starting: quality_reviewer_agent - Reviewing report quality")

        prompt = f"""Review the quality of this market research report.

Original Objectives:
{chr(10).join(f"- {obj}" for obj in objectives)}

Report Content:
{report_content[:5000]}... (truncated if longer)

Evaluate the report quality on these dimensions (score 0-1):
1. Completeness: Does it cover all objectives?
2. Accuracy: Is information presented accurately?
3. Depth: Is analysis sufficiently detailed?
4. Relevance: Is content relevant and valuable?
5. Clarity: Is it well-written and organized?

Provide feedback and recommendations for improvement.

Return as JSON with same structure as before."""

        messages = [
            {"role": "system", "content": QUALITY_REVIEWER_SYSTEM},
            {"role": "user", "content": prompt}
        ]

        # Call LLM
        if self.config.llm.provider == "openai":
            response = self.llm_client.chat.completions.create(
                messages=messages,
                **self.llm_params
            )
            content = response.choices[0].message.content

        elif self.config.llm.provider == "anthropic":
            response = self.llm_client.messages.create(
                system=QUALITY_REVIEWER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse and build review (similar to review_research)
        review_data = self._parse_json_response(content)

        scores_data = review_data.get("scores", {})
        scores = QualityScore(
            completeness=scores_data.get("completeness", 0.7),
            accuracy=scores_data.get("accuracy", 0.7),
            depth=scores_data.get("depth", 0.7),
            relevance=scores_data.get("relevance", 0.7),
            clarity=scores_data.get("clarity", 0.7),
            overall=scores_data.get("overall", 0.7)
        )

        passed = scores.overall >= self.quality_threshold

        review = QualityReview(
            passed=passed,
            scores=scores,
            gaps=review_data.get("gaps", []),
            strengths=review_data.get("strengths", []),
            feedback=review_data.get("feedback", []),
            recommendations=review_data.get("recommendations", []),
            requires_refinement=review_data.get("requires_refinement", not passed),
            refinement_areas=review_data.get("refinement_areas", []),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        duration = time.time() - start_time
        print(f"Complete: quality_reviewer_agent - {duration:.2f}s")

        return review

    def _summarize_results(
        self,
        research_results: List[Dict[str, Any]],
        analysis_results: List[Dict[str, Any]],
        specialized_results: List[Dict[str, Any]]
    ) -> str:
        """Summarize all results for review"""
        summary_parts = []

        if research_results:
            summary_parts.append(f"Research Results ({len(research_results)} items):")
            for r in research_results[:3]:  # Sample first 3
                result_type = r.get("research_type", "unknown")
                summary_parts.append(f"  - {result_type}")

        if analysis_results:
            summary_parts.append(f"\nAnalysis Results ({len(analysis_results)} items):")
            for a in analysis_results[:3]:
                analysis_type = a.get("analysis_type", "unknown")
                summary_parts.append(f"  - {analysis_type}")

        if specialized_results:
            summary_parts.append(f"\nSpecialized Analysis ({len(specialized_results)} items):")
            for s in specialized_results[:3]:
                agent_type = s.get("agent_type", "unknown")
                summary_parts.append(f"  - {agent_type}")

        return "\n".join(summary_parts)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            print("Warning: Could not parse JSON response, using defaults")
            return {
                "scores": {
                    "completeness": 0.7,
                    "accuracy": 0.7,
                    "depth": 0.7,
                    "relevance": 0.7,
                    "clarity": 0.7,
                    "overall": 0.7
                },
                "gaps": [],
                "strengths": [],
                "feedback": [],
                "recommendations": [],
                "requires_refinement": False,
                "refinement_areas": []
            }

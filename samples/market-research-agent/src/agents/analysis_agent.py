"""
Analysis Agent - FLATTENED (Deterministic Execution)
Performs strategic analysis on research data
NO internal agentic loop - only deterministic execution for speed
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config
from ..tools import create_swot_visualization


@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    analysis_type: str
    subject: str
    insights: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_type": self.analysis_type,
            "subject": self.subject,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class AnalysisAgent:
    """
    Agent specialized in strategic business analysis
    FLATTENED: No internal agentic loop - deterministic execution
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="analysis_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"AnalysisAgent initialized (deterministic mode - FAST)")

    def perform_swot_analysis(self, company_name: str, research_data: Dict[str, Any]) -> AnalysisResult:
        """
        Perform SWOT analysis (DETERMINISTIC - ONE LLM CALL)

        Args:
            company_name: Company to analyze
            research_data: Research data from ResearchAgent

        Returns:
            AnalysisResult with SWOT insights
        """
        start_time = time.time()
        print(f"\n📊 AnalysisAgent - SWOT: {company_name}")

        # Perform analysis with ONE LLM call
        prompt = f"""Perform a comprehensive SWOT analysis for: {company_name}

Research Data:
{json.dumps(research_data, indent=2)[:4000]}

Provide a detailed SWOT analysis in JSON format:
{{
  "strengths": [
    {{"strength": "specific strength", "evidence": "supporting evidence from data"}},
    ...
  ],
  "weaknesses": [
    {{"weakness": "specific weakness", "evidence": "supporting evidence"}},
    ...
  ],
  "opportunities": [
    {{"opportunity": "market opportunity", "potential": "growth potential"}},
    ...
  ],
  "threats": [
    {{"threat": "external threat", "impact": "potential impact"}},
    ...
  ],
  "strategic_recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2",
    ...
  ],
  "confidence": 0.8
}}

Be specific and evidence-based. Minimum 3 items per category."""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strategic business analyst expert in SWOT analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ AnalysisAgent SWOT complete - {duration:.2f}s (1 LLM call)\n")

            return AnalysisResult(
                analysis_type="swot",
                subject=company_name,
                insights=result,
                recommendations=result.get("strategic_recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"method": "deterministic"}
            )

        except Exception as e:
            print(f"⚠️ SWOT analysis failed: {e}")
            return AnalysisResult(
                analysis_type="swot",
                subject=company_name,
                insights={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

    def perform_competitive_analysis(self, company_name: str, research_data: Dict[str, Any]) -> AnalysisResult:
        """
        Perform competitive analysis (DETERMINISTIC - ONE LLM CALL)

        Args:
            company_name: Company to analyze
            research_data: Research data including competitor information

        Returns:
            AnalysisResult with competitive insights
        """
        start_time = time.time()
        print(f"\n📊 AnalysisAgent - Competitive: {company_name}")

        prompt = f"""Perform a competitive analysis for: {company_name}

Research Data:
{json.dumps(research_data, indent=2)[:4000]}

Provide a comprehensive competitive analysis in JSON format:
{{
  "competitive_position": "Overall market position summary",
  "key_competitors": [
    {{"name": "Competitor A", "strengths": "their strengths", "weaknesses": "their weaknesses"}},
    ...
  ],
  "competitive_advantages": [
    {{"advantage": "specific advantage", "impact": "why it matters"}},
    ...
  ],
  "competitive_gaps": [
    {{"gap": "area where company lags", "recommendation": "how to address"}},
    ...
  ],
  "market_share_insights": "Market share and positioning insights",
  "strategic_recommendations": [
    "Actionable competitive strategy 1",
    ...
  ],
  "confidence": 0.8
}}

Be specific about competitive dynamics."""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a competitive strategy analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ AnalysisAgent Competitive complete - {duration:.2f}s (1 LLM call)\n")

            return AnalysisResult(
                analysis_type="competitive",
                subject=company_name,
                insights=result,
                recommendations=result.get("strategic_recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"method": "deterministic"}
            )

        except Exception as e:
            print(f"⚠️ Competitive analysis failed: {e}")
            return AnalysisResult(
                analysis_type="competitive",
                subject=company_name,
                insights={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

    def perform_trend_analysis(self, company_name: str, industry: str, research_data: Dict[str, Any]) -> AnalysisResult:
        """
        Perform trend analysis (DETERMINISTIC - ONE LLM CALL)

        Args:
            company_name: Company to analyze
            industry: Industry context
            research_data: Research data

        Returns:
            AnalysisResult with trend insights
        """
        start_time = time.time()
        print(f"\n📊 AnalysisAgent - Trends: {company_name} ({industry})")

        prompt = f"""Perform a trend analysis for: {company_name} in {industry}

Research Data:
{json.dumps(research_data, indent=2)[:4000]}

Provide a comprehensive trend analysis in JSON format:
{{
  "market_trends": [
    {{"trend": "major market trend", "impact": "impact on company", "timeline": "short/medium/long term"}},
    ...
  ],
  "technology_trends": [
    {{"trend": "tech trend", "relevance": "how it affects the company"}},
    ...
  ],
  "consumer_trends": [
    {{"trend": "consumer behavior trend", "opportunity": "business opportunity"}},
    ...
  ],
  "emerging_opportunities": [
    {{"opportunity": "emerging opportunity", "strategic_fit": "alignment with company"}},
    ...
  ],
  "potential_disruptions": [
    {{"disruption": "potential threat", "mitigation": "how to prepare"}},
    ...
  ],
  "strategic_recommendations": [
    "Trend-based recommendation 1",
    ...
  ],
  "confidence": 0.8
}}

Focus on actionable trend insights."""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a market trend analyst and futurist."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ AnalysisAgent Trends complete - {duration:.2f}s (1 LLM call)\n")

            return AnalysisResult(
                analysis_type="trend",
                subject=company_name,
                insights=result,
                recommendations=result.get("strategic_recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"industry": industry, "method": "deterministic"}
            )

        except Exception as e:
            print(f"⚠️ Trend analysis failed: {e}")
            return AnalysisResult(
                analysis_type="trend",
                subject=company_name,
                insights={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

"""
Analysis Agent
Performs strategic analysis on research data
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config
from ..utils.prompts import ANALYSIS_AGENT_SYSTEM, get_analysis_prompt
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
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="analysis_agent")
        self.llm_params = self.config.get_llm_params()

        print("AnalysisAgent initialized")

    def perform_swot_analysis(self, company_name: str, research_data: Dict[str, Any]) -> AnalysisResult:
        """
        Perform SWOT analysis

        Args:
            company_name: Company to analyze
            research_data: Research data from ResearchAgent

        Returns:
            AnalysisResult with SWOT insights
        """
        start_time = time.time()
        print(f"Starting: AnalysisAgent - SWOT analysis for {company_name}")

        # Prepare research context
        context = self._format_research_data(research_data)

        # Get SWOT analysis prompt
        prompt = get_analysis_prompt(
            "swot",
            company_name=company_name,
            research_data=context
        )

        # Call LLM for analysis
        messages = [
            {"role": "system", "content": ANALYSIS_AGENT_SYSTEM},
            {"role": "user", "content": f"{prompt}\n\nReturn JSON with keys: strengths (list), weaknesses (list), opportunities (list), threats (list), strategic_implications (string), confidence (0-1)."}
        ]

        print("Performing SWOT analysis with LLM...")
        swot_data = self._call_llm_for_analysis(messages)


        # Create visualization
        viz = create_swot_visualization({
            "strengths": swot_data.get("strengths", []),
            "weaknesses": swot_data.get("weaknesses", []),
            "opportunities": swot_data.get("opportunities", []),
            "threats": swot_data.get("threats", [])
        })

        # Build result
        result = AnalysisResult(
            analysis_type="swot",
            subject=company_name,
            insights={
                "strengths": swot_data.get("strengths", []),
                "weaknesses": swot_data.get("weaknesses", []),
                "opportunities": swot_data.get("opportunities", []),
                "threats": swot_data.get("threats", []),
                "strategic_implications": swot_data.get("strategic_implications", ""),
                "visualization": viz
            },
            recommendations=self._generate_swot_recommendations(swot_data),
            confidence=swot_data.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "duration_seconds": time.time() - start_time
            }
        )

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s")

        return result

    def perform_competitive_analysis(
        self,
        company_name: str,
        research_data: Dict[str, Any],
        competitor_data: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Perform competitive analysis

        Args:
            company_name: Company to analyze
            research_data: Research data
            competitor_data: Optional competitor research data

        Returns:
            AnalysisResult with competitive insights
        """
        start_time = time.time()
        print(f"Starting: AnalysisAgent - Competitive analysis for {company_name}")

        # Prepare context
        context = self._format_research_data(research_data)
        if competitor_data:
            context += "\n\n=== Competitor Data ===\n" + self._format_research_data(competitor_data)

        # Get competitive analysis prompt
        prompt = get_analysis_prompt(
            "competitive",
            company_name=company_name,
            research_data=context
        )

        messages = [
            {"role": "system", "content": ANALYSIS_AGENT_SYSTEM},
            {"role": "user", "content": f"{prompt}\n\nReturn JSON with keys: competitive_position (string), key_competitors (list of dicts), market_gaps (list), competitive_advantages (list), threats (list), recommendations (list), confidence (0-1)."}
        ]

        print("Performing competitive analysis with LLM...")
        analysis_data = self._call_llm_for_analysis(messages)

        num_competitors = len(analysis_data.get("key_competitors", []))

        result = AnalysisResult(
            analysis_type="competitive",
            subject=company_name,
            insights={
                "competitive_position": analysis_data.get("competitive_position", ""),
                "key_competitors": analysis_data.get("key_competitors", []),
                "market_gaps": analysis_data.get("market_gaps", []),
                "competitive_advantages": analysis_data.get("competitive_advantages", []),
                "threats": analysis_data.get("threats", [])
            },
            recommendations=analysis_data.get("recommendations", []),
            confidence=analysis_data.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "duration_seconds": time.time() - start_time,
                "num_competitors_analyzed": num_competitors
            }
        )

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s")

        return result

    def perform_trend_analysis(
        self,
        company_name: str,
        industry: str,
        research_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Perform trend analysis

        Args:
            company_name: Company to analyze
            industry: Industry context
            research_data: Research data

        Returns:
            AnalysisResult with trend insights
        """
        start_time = time.time()
        print(f"Starting: AnalysisAgent - Trend analysis for {company_name} in {industry}")

        # Prepare context
        context = self._format_research_data(research_data)

        # Get trend analysis prompt
        prompt = get_analysis_prompt(
            "trends",
            company_name=company_name,
            industry=industry,
            research_data=context
        )

        messages = [
            {"role": "system", "content": ANALYSIS_AGENT_SYSTEM},
            {"role": "user", "content": f"{prompt}\n\nReturn JSON with keys: current_trends (list of dicts with 'trend', 'impact', 'timeline'), emerging_trends (list), trend_drivers (list), strategic_implications (list), recommendations (list), confidence (0-1)."}
        ]

        print("Performing trend analysis with LLM...")
        trend_data = self._call_llm_for_analysis(messages)

        # Categorize trends by priority
        trends_by_priority = self._prioritize_trends(trend_data.get("current_trends", []))


        result = AnalysisResult(
            analysis_type="trends",
            subject=f"{company_name} in {industry}",
            insights={
                "current_trends": trend_data.get("current_trends", []),
                "emerging_trends": trend_data.get("emerging_trends", []),
                "trend_drivers": trend_data.get("trend_drivers", []),
                "trends_by_priority": trends_by_priority,
                "strategic_implications": trend_data.get("strategic_implications", [])
            },
            recommendations=trend_data.get("recommendations", []),
            confidence=trend_data.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "duration_seconds": time.time() - start_time,
                "industry": industry
            }
        )

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s")

        return result

    def _call_llm_for_analysis(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call LLM for analysis and parse JSON response"""
        start_time = time.time()

        if self.config.llm.provider == "openai":
            response = self.llm_client.chat.completions.create(
                messages=messages,
                **self.llm_params
            )
            content = response.choices[0].message.content

        elif self.config.llm.provider == "anthropic":
            system_msg = messages[0]["content"] if messages[0]["role"] == "system" else ANALYSIS_AGENT_SYSTEM
            user_messages = [m for m in messages if m["role"] != "system"]

            response = self.llm_client.messages.create(
                system=system_msg,
                messages=user_messages,
                **self.llm_params
            )
            content = response.content[0].text

        # Parse JSON
        return self._parse_json_response(content)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            print(f"Failed to parse JSON response: {str(e)}")
            return {
                "error": "Failed to parse response",
                "raw_content": content[:500],
                "confidence": 0.3
            }

    def _format_research_data(self, research_data: Dict[str, Any]) -> str:
        """Format research data for LLM consumption"""
        if isinstance(research_data, str):
            return research_data

        formatted_parts = []

        # Handle ResearchResult objects
        if "summary" in research_data:
            formatted_parts.append(f"Summary: {research_data['summary']}")

        if "findings" in research_data:
            formatted_parts.append("\nKey Findings:")
            for finding in research_data["findings"]:
                if isinstance(finding, dict):
                    category = finding.get("category", "General")
                    details = finding.get("details", str(finding))
                    formatted_parts.append(f"- {category}: {details}")
                else:
                    formatted_parts.append(f"- {finding}")

        if "sources" in research_data:
            formatted_parts.append(f"\nSources: {len(research_data['sources'])} sources")

        # If no specific formatting matched, use JSON
        if not formatted_parts:
            return json.dumps(research_data, indent=2)

        return "\n".join(formatted_parts)

    def _generate_swot_recommendations(self, swot_data: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations from SWOT analysis"""
        recommendations = []

        # Leverage strengths
        if swot_data.get("strengths"):
            recommendations.append(
                f"Leverage key strengths: Focus on {swot_data['strengths'][0] if swot_data['strengths'] else 'core competencies'}"
            )

        # Address weaknesses
        if swot_data.get("weaknesses"):
            recommendations.append(
                f"Address critical weakness: Prioritize improving {swot_data['weaknesses'][0] if swot_data['weaknesses'] else 'identified gaps'}"
            )

        # Capitalize on opportunities
        if swot_data.get("opportunities"):
            recommendations.append(
                f"Capitalize on opportunity: {swot_data['opportunities'][0] if swot_data['opportunities'] else 'market trends'}"
            )

        # Mitigate threats
        if swot_data.get("threats"):
            recommendations.append(
                f"Mitigate threat: Develop strategy for {swot_data['threats'][0] if swot_data['threats'] else 'competitive pressures'}"
            )

        return recommendations

    def _prioritize_trends(self, trends: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Prioritize trends by impact and timeline"""
        prioritized = {
            "high": [],
            "medium": [],
            "low": []
        }

        for trend in trends:
            # Safely extract impact and timeline values
            impact_raw = trend.get("impact", "")
            timeline_raw = trend.get("timeline", "")

            # Convert to string if dict or other type
            if isinstance(impact_raw, dict):
                impact = str(impact_raw.get("level", impact_raw.get("value", ""))).lower()
            elif isinstance(impact_raw, str):
                impact = impact_raw.lower()
            else:
                impact = str(impact_raw).lower()

            if isinstance(timeline_raw, dict):
                timeline = str(timeline_raw.get("period", timeline_raw.get("value", ""))).lower()
            elif isinstance(timeline_raw, str):
                timeline = timeline_raw.lower()
            else:
                timeline = str(timeline_raw).lower()

            # High priority: high impact and near-term
            if "high" in impact or "short" in timeline or "immediate" in timeline:
                prioritized["high"].append(trend)
            # Low priority: low impact or long-term
            elif "low" in impact or "long" in timeline:
                prioritized["low"].append(trend)
            # Medium: everything else
            else:
                prioritized["medium"].append(trend)

        return prioritized

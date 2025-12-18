"""
Specialized Agents - FLATTENED (Deterministic Execution)
Financial, Technology, Market Sizing, Sentiment, and Regulatory agents
NO internal agentic loops - only deterministic execution for speed
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config
from ..utils.schemas import (
    get_response_format,
    FINANCIAL_ANALYSIS_SCHEMA,
    TECHNOLOGY_ANALYSIS_SCHEMA,
    MARKET_SIZING_SCHEMA,
    SENTIMENT_ANALYSIS_SCHEMA,
    REGULATORY_ANALYSIS_SCHEMA,
)


@dataclass
class SpecializedResult:
    """Result from specialized analysis"""
    agent_type: str
    subject: str
    findings: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type,
            "subject": self.subject,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class FinancialAgent:
    """
    Financial analysis agent
    FLATTENED: No internal agentic loop - ONE LLM call
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="financial_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"FinancialAgent initialized (deterministic mode - FAST)")

    def analyze_financials(self, company_name: str, context: Dict[str, Any]) -> SpecializedResult:
        """
        Perform financial analysis (DETERMINISTIC - ONE LLM CALL)

        Args:
            company_name: Company to analyze
            context: Research and analysis context

        Returns:
            SpecializedResult with financial insights
        """
        start_time = time.time()
        print(f"\n💰 FinancialAgent - {company_name}")

        prompt = f"""Perform comprehensive financial analysis for: {company_name}

Context Data:
{json.dumps(context, indent=2)[:4000]}

Provide detailed financial analysis in JSON format:
{{
  "revenue_model": {{
    "description": "How the company makes money",
    "revenue_streams": ["stream 1", "stream 2", ...],
    "sustainability": "Assessment of revenue model sustainability"
  }},
  "funding_history": {{
    "total_raised": "Total funding amount",
    "key_investors": ["investor 1", "investor 2", ...],
    "funding_rounds": ["Series A details", "Series B details", ...]
  }},
  "financial_health": {{
    "assessment": "Overall financial health",
    "revenue_growth": "Revenue growth trends",
    "profitability": "Profitability status and trends",
    "burn_rate": "Cash burn assessment if applicable"
  }},
  "financial_risks": [
    {{"risk": "specific financial risk", "severity": "high/medium/low", "mitigation": "mitigation strategy"}},
    ...
  ],
  "recommendations": ["Financial recommendation 1", ...],
  "confidence": 0.8
}}

Be specific and data-driven where possible."""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a financial analyst expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("financial_analysis", FINANCIAL_ANALYSIS_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ FinancialAgent complete - {duration:.2f}s (1 LLM call)\n")

            return SpecializedResult(
                agent_type="financial",
                subject=company_name,
                findings=result,
                recommendations=result.get("recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"method": "deterministic"}
            )

        except Exception as e:
            print(f"⚠️ Financial analysis failed: {e}")
            return SpecializedResult(
                agent_type="financial",
                subject=company_name,
                findings={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )


class TechnologyAgent:
    """
    Technology analysis agent
    FLATTENED: No internal agentic loop - ONE LLM call
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="technology_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"TechnologyAgent initialized (deterministic mode - FAST)")

    def analyze_technology(self, company_name: str, context: Dict[str, Any]) -> SpecializedResult:
        """
        Perform technology analysis (DETERMINISTIC - ONE LLM CALL)
        """
        start_time = time.time()
        print(f"\n⚙️ TechnologyAgent - {company_name}")

        prompt = f"""Perform technology analysis for: {company_name}

Context Data:
{json.dumps(context, indent=2)[:4000]}

Provide technology analysis in JSON format:
{{
  "tech_stack": {{
    "core_technologies": ["tech 1", "tech 2", ...],
    "infrastructure": "Infrastructure description",
    "differentiation": "What makes their tech unique"
  }},
  "innovation_capability": {{
    "assessment": "Overall innovation assessment",
    "r_and_d_focus": "R&D focus areas",
    "innovation_examples": ["example 1", "example 2", ...]
  }},
  "ip_portfolio": {{
    "patents": "Patent portfolio summary",
    "proprietary_tech": "Proprietary technologies",
    "competitive_moat": "Technical competitive advantages"
  }},
  "technical_advantages": [
    {{"advantage": "specific technical edge", "impact": "business impact"}},
    ...
  ],
  "recommendations": ["Technology recommendation 1", ...],
  "confidence": 0.8
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a technology analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("technology_analysis", TECHNOLOGY_ANALYSIS_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ TechnologyAgent complete - {duration:.2f}s (1 LLM call)\n")

            return SpecializedResult(
                agent_type="technology",
                subject=company_name,
                findings=result,
                recommendations=result.get("recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

        except Exception as e:
            print(f"⚠️ Technology analysis failed: {e}")
            return SpecializedResult(
                agent_type="technology",
                subject=company_name,
                findings={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )


class MarketSizingAgent:
    """
    Market sizing agent
    FLATTENED: No internal agentic loop - ONE LLM call
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="market_sizing_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"MarketSizingAgent initialized (deterministic mode - FAST)")

    def analyze_market_size(self, company_name: str, industry: str, context: Dict[str, Any]) -> SpecializedResult:
        """
        Perform market sizing analysis (DETERMINISTIC - ONE LLM CALL)
        """
        start_time = time.time()
        print(f"\n📏 MarketSizingAgent - {company_name} ({industry})")

        prompt = f"""Perform market sizing analysis for: {company_name} in {industry}

Context Data:
{json.dumps(context, indent=2)[:4000]}

Provide market sizing analysis in JSON format:
{{
  "tam": {{
    "value": "Total Addressable Market size",
    "rationale": "How TAM was calculated",
    "sources": "Data sources"
  }},
  "sam": {{
    "value": "Serviceable Addressable Market",
    "rationale": "How SAM was calculated"
  }},
  "som": {{
    "value": "Serviceable Obtainable Market",
    "rationale": "Realistic near-term capture"
  }},
  "market_segments": [
    {{"segment": "segment name", "size": "segment size", "growth": "growth rate"}},
    ...
  ],
  "market_growth": {{
    "historical_cagr": "Past growth rate",
    "projected_cagr": "Future growth projection",
    "growth_drivers": ["driver 1", "driver 2", ...]
  }},
  "recommendations": ["Market opportunity recommendation 1", ...],
  "confidence": 0.7
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a market sizing analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("market_sizing", MARKET_SIZING_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ MarketSizingAgent complete - {duration:.2f}s (1 LLM call)\n")

            return SpecializedResult(
                agent_type="market_sizing",
                subject=company_name,
                findings=result,
                recommendations=result.get("recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"industry": industry}
            )

        except Exception as e:
            print(f"⚠️ Market sizing failed: {e}")
            return SpecializedResult(
                agent_type="market_sizing",
                subject=company_name,
                findings={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )


class SentimentAgent:
    """
    Sentiment analysis agent
    FLATTENED: No internal agentic loop - ONE LLM call
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="sentiment_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"SentimentAgent initialized (deterministic mode - FAST)")

    def analyze_sentiment(self, company_name: str, context: Dict[str, Any]) -> SpecializedResult:
        """
        Perform sentiment analysis (DETERMINISTIC - ONE LLM CALL)
        """
        start_time = time.time()
        print(f"\n😊 SentimentAgent - {company_name}")

        prompt = f"""Perform sentiment analysis for: {company_name}

Context Data:
{json.dumps(context, indent=2)[:4000]}

Provide sentiment analysis in JSON format:
{{
  "customer_sentiment": {{
    "overall": "positive/neutral/negative",
    "score": 0.7,
    "evidence": ["evidence 1", "evidence 2", ...]
  }},
  "brand_perception": {{
    "assessment": "Brand perception summary",
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", ...]
  }},
  "sentiment_themes": [
    {{"theme": "common sentiment theme", "frequency": "high/medium/low", "impact": "impact on business"}},
    ...
  ],
  "competitor_comparison": {{
    "vs_competitors": "How sentiment compares to competitors",
    "differentiation": "Sentiment differentiators"
  }},
  "recommendations": ["Sentiment-based recommendation 1", ...],
  "confidence": 0.7
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("sentiment_analysis", SENTIMENT_ANALYSIS_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ SentimentAgent complete - {duration:.2f}s (1 LLM call)\n")

            return SpecializedResult(
                agent_type="sentiment",
                subject=company_name,
                findings=result,
                recommendations=result.get("recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

        except Exception as e:
            print(f"⚠️ Sentiment analysis failed: {e}")
            return SpecializedResult(
                agent_type="sentiment",
                subject=company_name,
                findings={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )


class RegulatoryAgent:
    """
    Regulatory analysis agent
    FLATTENED: No internal agentic loop - ONE LLM call
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="regulatory_agent")
        self.llm_params = self.config.get_llm_params()

        print(f"RegulatoryAgent initialized (deterministic mode - FAST)")

    def analyze_regulatory(self, company_name: str, industry: str, context: Dict[str, Any]) -> SpecializedResult:
        """
        Perform regulatory analysis (DETERMINISTIC - ONE LLM CALL)
        """
        start_time = time.time()
        print(f"\n⚖️ RegulatoryAgent - {company_name} ({industry})")

        prompt = f"""Perform regulatory analysis for: {company_name} in {industry}

Context Data:
{json.dumps(context, indent=2)[:4000]}

Provide regulatory analysis in JSON format:
{{
  "key_regulations": [
    {{"regulation": "regulation name", "impact": "impact on company", "compliance_status": "compliant/at-risk/unknown"}},
    ...
  ],
  "compliance_status": {{
    "overall": "Overall compliance assessment",
    "certifications": ["certification 1", ...],
    "compliance_challenges": ["challenge 1", ...]
  }},
  "regulatory_risks": [
    {{"risk": "specific regulatory risk", "severity": "high/medium/low", "mitigation": "mitigation approach"}},
    ...
  ],
  "policy_changes": [
    {{"change": "upcoming policy change", "timeline": "when it takes effect", "impact": "business impact"}},
    ...
  ],
  "recommendations": ["Regulatory recommendation 1", ...],
  "confidence": 0.7
}}"""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a regulatory analyst."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("regulatory_analysis", REGULATORY_ANALYSIS_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)

            duration = time.time() - start_time
            print(f"✅ RegulatoryAgent complete - {duration:.2f}s (1 LLM call)\n")

            return SpecializedResult(
                agent_type="regulatory",
                subject=company_name,
                findings=result,
                recommendations=result.get("recommendations", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"industry": industry}
            )

        except Exception as e:
            print(f"⚠️ Regulatory analysis failed: {e}")
            return SpecializedResult(
                agent_type="regulatory",
                subject=company_name,
                findings={},
                recommendations=[],
                confidence=0.3,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )

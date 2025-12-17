"""
Specialized Sub-Agents
Deep-dive experts for specific research domains
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.config import get_config
from ..utils.prompts import (
    FINANCIAL_AGENT_SYSTEM,
    TECHNOLOGY_AGENT_SYSTEM,
    MARKET_SIZING_AGENT_SYSTEM,
    SENTIMENT_AGENT_SYSTEM,
    REGULATORY_AGENT_SYSTEM
)


@dataclass
class SpecializedResult:
    """Result from specialized agent"""
    agent_type: str
    company_name: str
    findings: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.8
    sources: List[str] = field(default_factory=list)
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_type": self.agent_type,
            "company_name": self.company_name,
            "findings": self.findings,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class FinancialAgent:
    """
    Specialized agent for financial analysis
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="financial_agent")
        self.llm_params = self.config.get_llm_params()

        print("FinancialAgent initialized")

    def analyze_financials(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform deep financial analysis

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Financial analysis results
        """
        start_time = time.time()
        print(f"Starting: financial_agent - Analyzing financials for {company_name}")

        prompt = f"""Analyze the financial aspects of {company_name}.

Context:
{json.dumps(context, indent=2)}

Provide a comprehensive financial analysis covering:
1. Revenue model and monetization strategy
2. Funding history and current valuation
3. Financial health indicators
4. Business model sustainability
5. Key financial risks and opportunities

Return as JSON:
{{
    "findings": {{
        "revenue_model": "description",
        "funding_status": "details",
        "financial_health": "assessment",
        "valuation": "estimate or info"
    }},
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["rec 1", "rec 2", ...],
    "confidence": 0.85
}}"""

        messages = [
            {"role": "system", "content": FINANCIAL_AGENT_SYSTEM},
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
                system=FINANCIAL_AGENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        data = self._parse_json_response(content)

        result = SpecializedResult(
            agent_type="financial_analysis",
            company_name=company_name,
            findings=data.get("findings", {}),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            confidence=data.get("confidence", 0.8),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"duration_seconds": time.time() - start_time}
        )

        duration = time.time() - start_time
        print(f"Complete: financial_agent - {duration:.2f}s")

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}


class TechnologyAgent:
    """
    Specialized agent for technology analysis
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="technology_agent")
        self.llm_params = self.config.get_llm_params()

        print("TechnologyAgent initialized")

    def analyze_technology(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform deep technology analysis

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Technology analysis results
        """
        start_time = time.time()
        print(f"Starting: technology_agent - Analyzing technology for {company_name}")

        prompt = f"""Analyze the technology aspects of {company_name}.

Context:
{json.dumps(context, indent=2)}

Provide a comprehensive technology analysis covering:
1. Core technology stack and infrastructure
2. R&D capabilities and innovation track record
3. Patents and intellectual property
4. Technical differentiation and advantages
5. Technology risks and opportunities

Return as JSON:
{{
    "findings": {{
        "tech_stack": "description",
        "innovation": "assessment",
        "ip_portfolio": "details",
        "technical_edge": "analysis"
    }},
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["rec 1", "rec 2", ...],
    "confidence": 0.85
}}"""

        messages = [
            {"role": "system", "content": TECHNOLOGY_AGENT_SYSTEM},
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
                system=TECHNOLOGY_AGENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        data = self._parse_json_response(content)

        result = SpecializedResult(
            agent_type="technology_analysis",
            company_name=company_name,
            findings=data.get("findings", {}),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            confidence=data.get("confidence", 0.8),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"duration_seconds": time.time() - start_time}
        )

        duration = time.time() - start_time
        print(f"Complete: technology_agent - {duration:.2f}s")

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}


class MarketSizingAgent:
    """
    Specialized agent for market sizing analysis
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="market_sizing_agent")
        self.llm_params = self.config.get_llm_params()

        print("MarketSizingAgent initialized")

    def analyze_market_size(
        self,
        company_name: str,
        industry: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform market sizing analysis

        Args:
            company_name: Company to analyze
            industry: Industry context
            context: Research context and data

        Returns:
            Market sizing results
        """
        start_time = time.time()
        print(f"Starting: market_sizing_agent - Analyzing market size for {company_name}")

        prompt = f"""Analyze the market size and opportunity for {company_name} in the {industry} industry.

Context:
{json.dumps(context, indent=2)}

Provide a comprehensive market sizing analysis covering:
1. TAM (Total Addressable Market)
2. SAM (Serviceable Addressable Market)
3. SOM (Serviceable Obtainable Market)
4. Market segmentation breakdown
5. Growth projections and trends

Return as JSON:
{{
    "findings": {{
        "tam": "estimate with reasoning",
        "sam": "estimate with reasoning",
        "som": "estimate with reasoning",
        "segments": {{"segment1": "size", "segment2": "size"}},
        "growth_rate": "projected growth"
    }},
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["rec 1", "rec 2", ...],
    "confidence": 0.75
}}"""

        messages = [
            {"role": "system", "content": MARKET_SIZING_AGENT_SYSTEM},
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
                system=MARKET_SIZING_AGENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        data = self._parse_json_response(content)

        result = SpecializedResult(
            agent_type="market_sizing",
            company_name=company_name,
            findings=data.get("findings", {}),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            confidence=data.get("confidence", 0.75),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"duration_seconds": time.time() - start_time}
        )

        duration = time.time() - start_time
        print(f"Complete: market_sizing_agent - {duration:.2f}s")

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}


class SentimentAgent:
    """
    Specialized agent for sentiment analysis
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="sentiment_agent")
        self.llm_params = self.config.get_llm_params()

        print("SentimentAgent initialized")

    def analyze_sentiment(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform sentiment analysis

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Sentiment analysis results
        """
        start_time = time.time()
        print(f"Starting: sentiment_agent - Analyzing sentiment for {company_name}")

        prompt = f"""Analyze customer sentiment and public perception of {company_name}.

Context:
{json.dumps(context, indent=2)}

Provide a comprehensive sentiment analysis covering:
1. Overall sentiment score and trend
2. Customer satisfaction indicators
3. Brand perception and reputation
4. Key themes in feedback (positive and negative)
5. Comparison to competitors

Return as JSON:
{{
    "findings": {{
        "overall_sentiment": "positive/negative/neutral with score",
        "satisfaction_level": "assessment",
        "brand_perception": "analysis",
        "key_themes": ["theme1", "theme2", ...]
    }},
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["rec 1", "rec 2", ...],
    "confidence": 0.80
}}"""

        messages = [
            {"role": "system", "content": SENTIMENT_AGENT_SYSTEM},
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
                system=SENTIMENT_AGENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        data = self._parse_json_response(content)

        result = SpecializedResult(
            agent_type="sentiment_analysis",
            company_name=company_name,
            findings=data.get("findings", {}),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            confidence=data.get("confidence", 0.8),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"duration_seconds": time.time() - start_time}
        )

        duration = time.time() - start_time
        print(f"Complete: sentiment_agent - {duration:.2f}s")

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}


class RegulatoryAgent:
    """
    Specialized agent for regulatory analysis
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="regulatory_agent")
        self.llm_params = self.config.get_llm_params()

        print("RegulatoryAgent initialized")

    def analyze_regulatory(
        self,
        company_name: str,
        industry: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform regulatory analysis

        Args:
            company_name: Company to analyze
            industry: Industry context
            context: Research context and data

        Returns:
            Regulatory analysis results
        """
        start_time = time.time()
        print(f"Starting: regulatory_agent - Analyzing regulatory aspects for {company_name}")

        prompt = f"""Analyze the regulatory and compliance aspects of {company_name} in the {industry} industry.

Context:
{json.dumps(context, indent=2)}

Provide a comprehensive regulatory analysis covering:
1. Key regulations and compliance requirements
2. Regulatory risks and challenges
3. Licensing and certification status
4. Recent or pending policy changes
5. Compliance track record

Return as JSON:
{{
    "findings": {{
        "key_regulations": ["reg1", "reg2", ...],
        "compliance_status": "assessment",
        "regulatory_risks": ["risk1", "risk2", ...],
        "policy_changes": "recent updates"
    }},
    "insights": ["insight 1", "insight 2", ...],
    "recommendations": ["rec 1", "rec 2", ...],
    "confidence": 0.80
}}"""

        messages = [
            {"role": "system", "content": REGULATORY_AGENT_SYSTEM},
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
                system=REGULATORY_AGENT_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                **self.llm_params
            )
            content = response.content[0].text

        # Parse response
        data = self._parse_json_response(content)

        result = SpecializedResult(
            agent_type="regulatory_analysis",
            company_name=company_name,
            findings=data.get("findings", {}),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            confidence=data.get("confidence", 0.8),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"duration_seconds": time.time() - start_time}
        )

        duration = time.time() - start_time
        print(f"Complete: regulatory_agent - {duration:.2f}s")

        return result

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

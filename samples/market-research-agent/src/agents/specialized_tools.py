"""
Specialized Tools for Agentic Specialized Agents
Defines domain-specific tools for financial, technology, market sizing, sentiment, and regulatory analysis
"""

from typing import Dict, List, Any
import json

# ==================== FINANCIAL ANALYSIS TOOLS ====================

FINANCIAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_revenue_model",
            "description": "Analyze the company's revenue model and monetization strategy. Use this to understand how the company makes money.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_funding_history",
            "description": "Analyze the company's funding history, investors, and capital structure. Use this to understand financial backing.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_financial_health",
            "description": "Assess the company's financial health and sustainability. Use this to evaluate financial metrics and stability.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_financial_risks",
            "description": "Identify financial risks and vulnerabilities. Use this to spot potential financial challenges.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# ==================== TECHNOLOGY ANALYSIS TOOLS ====================

TECHNOLOGY_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_tech_stack",
            "description": "Analyze the company's technology stack and infrastructure. Use this to understand technical architecture.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_innovation_capability",
            "description": "Evaluate R&D capabilities and innovation track record. Use this to assess technical innovation.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_ip_portfolio",
            "description": "Assess intellectual property portfolio including patents and proprietary technology. Use this to understand IP assets.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_technical_advantages",
            "description": "Identify technical differentiation and competitive advantages. Use this to find unique technical capabilities.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# ==================== MARKET SIZING TOOLS ====================

MARKET_SIZING_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_tam",
            "description": "Calculate Total Addressable Market (TAM). Use this to estimate the total market opportunity.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_sam",
            "description": "Calculate Serviceable Addressable Market (SAM). Use this to estimate the reachable market segment.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_som",
            "description": "Calculate Serviceable Obtainable Market (SOM). Use this to estimate the realistically capturable market.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_market_segments",
            "description": "Analyze market segmentation and breakdown. Use this to understand different market segments and their sizes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "project_market_growth",
            "description": "Project market growth rates and future trends. Use this to estimate market expansion.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# ==================== SENTIMENT ANALYSIS TOOLS ====================

SENTIMENT_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_customer_sentiment",
            "description": "Analyze overall customer sentiment and satisfaction. Use this to gauge customer feelings.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_brand_perception",
            "description": "Analyze brand perception and reputation. Use this to understand public opinion of the brand.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_sentiment_themes",
            "description": "Identify key themes in customer feedback (positive and negative). Use this to find common sentiment patterns.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_competitor_sentiment",
            "description": "Compare sentiment with competitors. Use this to benchmark against competition.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# ==================== REGULATORY ANALYSIS TOOLS ====================

REGULATORY_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "identify_key_regulations",
            "description": "Identify key regulations and compliance requirements. Use this to understand regulatory landscape.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_compliance_status",
            "description": "Assess current compliance status and track record. Use this to evaluate regulatory adherence.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_regulatory_risks",
            "description": "Identify regulatory risks and potential compliance challenges. Use this to spot regulatory threats.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_policy_changes",
            "description": "Analyze recent and pending policy/regulatory changes. Use this to understand evolving regulations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# ==================== TOOL EXECUTORS ====================

class SpecializedToolExecutor:
    """
    Base executor for specialized domain analysis tools
    """

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any], agent_label: str):
        """
        Initialize with analysis context

        Args:
            context: Research/analysis context data
            llm_client: LLM client for tool execution
            llm_params: LLM parameters
            agent_label: Agent label for system prompts
        """
        self.context = context
        self.llm_client = llm_client
        self.llm_params = llm_params
        self.agent_label = agent_label
        self.findings = {}

    def _call_llm_for_analysis(self, tool_name: str, prompt: str) -> Dict[str, Any]:
        """Call LLM for specific analysis"""
        messages = [
            {
                "role": "system",
                "content": f"You are an expert {self.agent_label}. Analyze the provided data and return structured insights in JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.llm_client.chat.completions.create(
            messages=messages,
            **self.llm_params
        )

        content = response.choices[0].message.content

        # Parse JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            return {"analysis": content, "error": f"Failed to parse: {str(e)}"}

    def _format_context(self) -> str:
        """Format context for LLM consumption"""
        if isinstance(self.context, str):
            return self.context

        formatted = json.dumps(self.context, indent=2)
        if len(formatted) > 3000:
            formatted = formatted[:3000] + "\n... (truncated)"
        return formatted

    def get_findings(self) -> Dict[str, Any]:
        """Get accumulated findings"""
        return self.findings


class FinancialToolExecutor(SpecializedToolExecutor):
    """Executor for financial analysis tools"""

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        super().__init__(context, llm_client, llm_params, "financial analyst")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute financial analysis tool"""
        try:
            if tool_name == "analyze_revenue_model":
                return self._analyze_revenue_model()
            elif tool_name == "analyze_funding_history":
                return self._analyze_funding_history()
            elif tool_name == "assess_financial_health":
                return self._assess_financial_health()
            elif tool_name == "identify_financial_risks":
                return self._identify_financial_risks()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_revenue_model(self) -> Dict[str, Any]:
        prompt = f"""Analyze the revenue model and monetization strategy from the context.

Context:
{self._format_context()}

Return JSON with: revenue_model (description), revenue_streams (list), sustainability (assessment)"""

        result = self._call_llm_for_analysis("revenue_model", prompt)
        self.findings["revenue_model"] = result
        return {"success": True, **result}

    def _analyze_funding_history(self) -> Dict[str, Any]:
        prompt = f"""Analyze the funding history and capital structure from the context.

Context:
{self._format_context()}

Return JSON with: funding_rounds (list), total_raised (estimate), key_investors (list), valuation (estimate)"""

        result = self._call_llm_for_analysis("funding_history", prompt)
        self.findings["funding_history"] = result
        return {"success": True, **result}

    def _assess_financial_health(self) -> Dict[str, Any]:
        prompt = f"""Assess the financial health and sustainability from the context.

Context:
{self._format_context()}

Return JSON with: health_score (assessment), key_metrics (dict), burn_rate (estimate if applicable), runway (estimate if applicable)"""

        result = self._call_llm_for_analysis("financial_health", prompt)
        self.findings["financial_health"] = result
        return {"success": True, **result}

    def _identify_financial_risks(self) -> Dict[str, Any]:
        prompt = f"""Identify financial risks and vulnerabilities from the context.

Context:
{self._format_context()}

Return JSON with: risks (list of dicts with 'risk' and 'severity'), mitigation_strategies (list)"""

        result = self._call_llm_for_analysis("financial_risks", prompt)
        self.findings["financial_risks"] = result
        return {"success": True, **result}


class TechnologyToolExecutor(SpecializedToolExecutor):
    """Executor for technology analysis tools"""

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        super().__init__(context, llm_client, llm_params, "technology analyst")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute technology analysis tool"""
        try:
            if tool_name == "analyze_tech_stack":
                return self._analyze_tech_stack()
            elif tool_name == "evaluate_innovation_capability":
                return self._evaluate_innovation_capability()
            elif tool_name == "assess_ip_portfolio":
                return self._assess_ip_portfolio()
            elif tool_name == "identify_technical_advantages":
                return self._identify_technical_advantages()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_tech_stack(self) -> Dict[str, Any]:
        prompt = f"""Analyze the technology stack and infrastructure from the context.

Context:
{self._format_context()}

Return JSON with: tech_stack (dict), infrastructure (description), scalability (assessment)"""

        result = self._call_llm_for_analysis("tech_stack", prompt)
        self.findings["tech_stack"] = result
        return {"success": True, **result}

    def _evaluate_innovation_capability(self) -> Dict[str, Any]:
        prompt = f"""Evaluate R&D capabilities and innovation track record from the context.

Context:
{self._format_context()}

Return JSON with: innovation_score (assessment), rd_investment (info), recent_innovations (list)"""

        result = self._call_llm_for_analysis("innovation", prompt)
        self.findings["innovation"] = result
        return {"success": True, **result}

    def _assess_ip_portfolio(self) -> Dict[str, Any]:
        prompt = f"""Assess intellectual property portfolio from the context.

Context:
{self._format_context()}

Return JSON with: patents (count/list), proprietary_tech (list), ip_strength (assessment)"""

        result = self._call_llm_for_analysis("ip_portfolio", prompt)
        self.findings["ip_portfolio"] = result
        return {"success": True, **result}

    def _identify_technical_advantages(self) -> Dict[str, Any]:
        prompt = f"""Identify technical differentiation and competitive advantages from the context.

Context:
{self._format_context()}

Return JSON with: advantages (list), differentiators (list), technical_moat (assessment)"""

        result = self._call_llm_for_analysis("technical_advantages", prompt)
        self.findings["technical_advantages"] = result
        return {"success": True, **result}


class MarketSizingToolExecutor(SpecializedToolExecutor):
    """Executor for market sizing analysis tools"""

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        super().__init__(context, llm_client, llm_params, "market sizing analyst")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market sizing analysis tool"""
        try:
            if tool_name == "calculate_tam":
                return self._calculate_tam()
            elif tool_name == "calculate_sam":
                return self._calculate_sam()
            elif tool_name == "calculate_som":
                return self._calculate_som()
            elif tool_name == "analyze_market_segments":
                return self._analyze_market_segments()
            elif tool_name == "project_market_growth":
                return self._project_market_growth()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_tam(self) -> Dict[str, Any]:
        prompt = f"""Calculate Total Addressable Market (TAM) from the context.

Context:
{self._format_context()}

Return JSON with: tam (estimate with currency), methodology (explanation), data_sources (list)"""

        result = self._call_llm_for_analysis("tam", prompt)
        self.findings["tam"] = result
        return {"success": True, **result}

    def _calculate_sam(self) -> Dict[str, Any]:
        prompt = f"""Calculate Serviceable Addressable Market (SAM) from the context.

Context:
{self._format_context()}

Return JSON with: sam (estimate with currency), methodology (explanation), constraints (list)"""

        result = self._call_llm_for_analysis("sam", prompt)
        self.findings["sam"] = result
        return {"success": True, **result}

    def _calculate_som(self) -> Dict[str, Any]:
        prompt = f"""Calculate Serviceable Obtainable Market (SOM) from the context.

Context:
{self._format_context()}

Return JSON with: som (estimate with currency), market_share_assumption (percentage), timeframe (years)"""

        result = self._call_llm_for_analysis("som", prompt)
        self.findings["som"] = result
        return {"success": True, **result}

    def _analyze_market_segments(self) -> Dict[str, Any]:
        prompt = f"""Analyze market segmentation from the context.

Context:
{self._format_context()}

Return JSON with: segments (dict with segment names and sizes), fastest_growing (segment name), most_valuable (segment name)"""

        result = self._call_llm_for_analysis("segments", prompt)
        self.findings["segments"] = result
        return {"success": True, **result}

    def _project_market_growth(self) -> Dict[str, Any]:
        prompt = f"""Project market growth rates from the context.

Context:
{self._format_context()}

Return JSON with: cagr (percentage), growth_drivers (list), projections (dict with years and estimates)"""

        result = self._call_llm_for_analysis("growth", prompt)
        self.findings["growth"] = result
        return {"success": True, **result}


class SentimentToolExecutor(SpecializedToolExecutor):
    """Executor for sentiment analysis tools"""

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        super().__init__(context, llm_client, llm_params, "sentiment analyst")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sentiment analysis tool"""
        try:
            if tool_name == "analyze_customer_sentiment":
                return self._analyze_customer_sentiment()
            elif tool_name == "analyze_brand_perception":
                return self._analyze_brand_perception()
            elif tool_name == "identify_sentiment_themes":
                return self._identify_sentiment_themes()
            elif tool_name == "compare_competitor_sentiment":
                return self._compare_competitor_sentiment()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_customer_sentiment(self) -> Dict[str, Any]:
        prompt = f"""Analyze overall customer sentiment from the context.

Context:
{self._format_context()}

Return JSON with: sentiment_score (positive/neutral/negative with numeric score), satisfaction_level (high/medium/low), trend (improving/stable/declining)"""

        result = self._call_llm_for_analysis("customer_sentiment", prompt)
        self.findings["customer_sentiment"] = result
        return {"success": True, **result}

    def _analyze_brand_perception(self) -> Dict[str, Any]:
        prompt = f"""Analyze brand perception and reputation from the context.

Context:
{self._format_context()}

Return JSON with: brand_strength (assessment), reputation_score (description), key_associations (list)"""

        result = self._call_llm_for_analysis("brand_perception", prompt)
        self.findings["brand_perception"] = result
        return {"success": True, **result}

    def _identify_sentiment_themes(self) -> Dict[str, Any]:
        prompt = f"""Identify key themes in sentiment/feedback from the context.

Context:
{self._format_context()}

Return JSON with: positive_themes (list), negative_themes (list), emerging_issues (list)"""

        result = self._call_llm_for_analysis("sentiment_themes", prompt)
        self.findings["sentiment_themes"] = result
        return {"success": True, **result}

    def _compare_competitor_sentiment(self) -> Dict[str, Any]:
        prompt = f"""Compare sentiment with competitors from the context.

Context:
{self._format_context()}

Return JSON with: relative_position (better/similar/worse), competitive_advantages (list), areas_to_improve (list)"""

        result = self._call_llm_for_analysis("competitor_sentiment", prompt)
        self.findings["competitor_sentiment"] = result
        return {"success": True, **result}


class RegulatoryToolExecutor(SpecializedToolExecutor):
    """Executor for regulatory analysis tools"""

    def __init__(self, context: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        super().__init__(context, llm_client, llm_params, "regulatory analyst")

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute regulatory analysis tool"""
        try:
            if tool_name == "identify_key_regulations":
                return self._identify_key_regulations()
            elif tool_name == "assess_compliance_status":
                return self._assess_compliance_status()
            elif tool_name == "identify_regulatory_risks":
                return self._identify_regulatory_risks()
            elif tool_name == "analyze_policy_changes":
                return self._analyze_policy_changes()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _identify_key_regulations(self) -> Dict[str, Any]:
        prompt = f"""Identify key regulations and compliance requirements from the context.

Context:
{self._format_context()}

Return JSON with: regulations (list of dicts with 'name' and 'description'), jurisdictions (list), compliance_burden (high/medium/low)"""

        result = self._call_llm_for_analysis("key_regulations", prompt)
        self.findings["key_regulations"] = result
        return {"success": True, **result}

    def _assess_compliance_status(self) -> Dict[str, Any]:
        prompt = f"""Assess compliance status and track record from the context.

Context:
{self._format_context()}

Return JSON with: compliance_level (excellent/good/fair/poor), certifications (list), violations (list if any)"""

        result = self._call_llm_for_analysis("compliance_status", prompt)
        self.findings["compliance_status"] = result
        return {"success": True, **result}

    def _identify_regulatory_risks(self) -> Dict[str, Any]:
        prompt = f"""Identify regulatory risks and challenges from the context.

Context:
{self._format_context()}

Return JSON with: risks (list of dicts with 'risk' and 'severity'), potential_penalties (description), mitigation_needs (list)"""

        result = self._call_llm_for_analysis("regulatory_risks", prompt)
        self.findings["regulatory_risks"] = result
        return {"success": True, **result}

    def _analyze_policy_changes(self) -> Dict[str, Any]:
        prompt = f"""Analyze recent and pending policy/regulatory changes from the context.

Context:
{self._format_context()}

Return JSON with: recent_changes (list), pending_changes (list), impact_assessment (description)"""

        result = self._call_llm_for_analysis("policy_changes", prompt)
        self.findings["policy_changes"] = result
        return {"success": True, **result}

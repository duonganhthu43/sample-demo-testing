"""
Analysis Tools for Agentic Analysis Agent
Defines analytical tools available to the LLM for strategic analysis
"""

from typing import Dict, List, Any

# Tool definitions for OpenAI function calling
ANALYSIS_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "identify_strengths",
            "description": "Identify and analyze company strengths from research data. Use this to find competitive advantages, core competencies, and positive attributes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus on (e.g., 'technology', 'brand', 'operations')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_weaknesses",
            "description": "Identify and analyze company weaknesses from research data. Use this to find areas needing improvement, vulnerabilities, and limitations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific areas to focus on (e.g., 'resources', 'capabilities', 'market position')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_opportunities",
            "description": "Identify and analyze market opportunities from research data. Use this to find growth potential, market gaps, and favorable trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_horizon": {
                        "type": "string",
                        "description": "Time horizon for opportunities (short-term, medium-term, long-term)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_threats",
            "description": "Identify and analyze threats from research data. Use this to find competitive pressures, market risks, and challenges.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threat_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of threats to focus on (e.g., 'competitive', 'regulatory', 'technological')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_competitive_positioning",
            "description": "Analyze competitive positioning and market dynamics. Use this to understand how the company compares to competitors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "competitors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific competitors to analyze"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dimensions to compare (e.g., 'pricing', 'features', 'market share')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_market_trends",
            "description": "Identify and analyze market and industry trends. Use this to understand macro trends, emerging patterns, and market dynamics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trend_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Categories of trends (e.g., 'technology', 'consumer behavior', 'regulatory')"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_strategic_recommendations",
            "description": "Generate strategic recommendations based on analysis findings. Use this after gathering analytical insights to provide actionable advice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_area": {
                        "type": "string",
                        "description": "Area to focus recommendations on (e.g., 'growth', 'competitive strategy', 'risk mitigation')"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level for recommendations (high, medium, low)"
                    }
                },
                "required": []
            }
        }
    }
]


class AnalysisToolExecutor:
    """
    Executes analysis tool calls from LLM function calling
    Uses the research_data context to perform analytical operations
    """

    def __init__(self, research_data: Dict[str, Any], llm_client, llm_params: Dict[str, Any]):
        """
        Initialize with research data and LLM client

        Args:
            research_data: Research data to analyze
            llm_client: LLM client for analytical calls
            llm_params: LLM parameters
        """
        self.research_data = research_data
        self.llm_client = llm_client
        self.llm_params = llm_params
        self.analysis_context = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "competitive_insights": [],
            "trends": [],
            "recommendations": []
        }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an analysis tool call

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            if tool_name == "identify_strengths":
                return self._identify_strengths(arguments)

            elif tool_name == "identify_weaknesses":
                return self._identify_weaknesses(arguments)

            elif tool_name == "identify_opportunities":
                return self._identify_opportunities(arguments)

            elif tool_name == "identify_threats":
                return self._identify_threats(arguments)

            elif tool_name == "analyze_competitive_positioning":
                return self._analyze_competitive_positioning(arguments)

            elif tool_name == "identify_market_trends":
                return self._identify_market_trends(arguments)

            elif tool_name == "generate_strategic_recommendations":
                return self._generate_recommendations(arguments)

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _identify_strengths(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Identify company strengths"""
        focus_areas = arguments.get("focus_areas", [])

        prompt = f"""Analyze the research data and identify company strengths.

Research Data:
{self._format_research_data()}

Focus Areas: {', '.join(focus_areas) if focus_areas else 'All areas'}

Identify 3-5 key strengths. Return JSON with:
- strengths: list of dicts with 'strength' (name) and 'evidence' (supporting data)"""

        result = self._call_llm_for_analysis(prompt)
        strengths = result.get("strengths", [])

        # Store in context
        self.analysis_context["strengths"].extend(strengths)

        return {
            "success": True,
            "strengths": strengths,
            "count": len(strengths)
        }

    def _identify_weaknesses(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Identify company weaknesses"""
        focus_areas = arguments.get("focus_areas", [])

        prompt = f"""Analyze the research data and identify company weaknesses.

Research Data:
{self._format_research_data()}

Focus Areas: {', '.join(focus_areas) if focus_areas else 'All areas'}

Identify 3-5 key weaknesses. Return JSON with:
- weaknesses: list of dicts with 'weakness' (name) and 'impact' (potential impact)"""

        result = self._call_llm_for_analysis(prompt)
        weaknesses = result.get("weaknesses", [])

        self.analysis_context["weaknesses"].extend(weaknesses)

        return {
            "success": True,
            "weaknesses": weaknesses,
            "count": len(weaknesses)
        }

    def _identify_opportunities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Identify market opportunities"""
        time_horizon = arguments.get("time_horizon", "medium-term")

        prompt = f"""Analyze the research data and identify market opportunities.

Research Data:
{self._format_research_data()}

Time Horizon: {time_horizon}

Identify 3-5 key opportunities. Return JSON with:
- opportunities: list of dicts with 'opportunity' (name) and 'potential' (growth potential)"""

        result = self._call_llm_for_analysis(prompt)
        opportunities = result.get("opportunities", [])

        self.analysis_context["opportunities"].extend(opportunities)

        return {
            "success": True,
            "opportunities": opportunities,
            "count": len(opportunities)
        }

    def _identify_threats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Identify threats"""
        threat_types = arguments.get("threat_types", [])

        prompt = f"""Analyze the research data and identify threats.

Research Data:
{self._format_research_data()}

Threat Types: {', '.join(threat_types) if threat_types else 'All types'}

Identify 3-5 key threats. Return JSON with:
- threats: list of dicts with 'threat' (name) and 'severity' (risk level)"""

        result = self._call_llm_for_analysis(prompt)
        threats = result.get("threats", [])

        self.analysis_context["threats"].extend(threats)

        return {
            "success": True,
            "threats": threats,
            "count": len(threats)
        }

    def _analyze_competitive_positioning(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitive positioning"""
        competitors = arguments.get("competitors", [])
        dimensions = arguments.get("dimensions", [])

        prompt = f"""Analyze competitive positioning from the research data.

Research Data:
{self._format_research_data()}

Competitors: {', '.join(competitors) if competitors else 'From data'}
Dimensions: {', '.join(dimensions) if dimensions else 'All relevant dimensions'}

Analyze competitive position. Return JSON with:
- position: overall competitive position
- advantages: list of competitive advantages
- gaps: list of competitive gaps"""

        result = self._call_llm_for_analysis(prompt)

        self.analysis_context["competitive_insights"].append(result)

        return {
            "success": True,
            **result
        }

    def _identify_market_trends(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Identify market trends"""
        trend_categories = arguments.get("trend_categories", [])

        prompt = f"""Identify market and industry trends from the research data.

Research Data:
{self._format_research_data()}

Trend Categories: {', '.join(trend_categories) if trend_categories else 'All categories'}

Identify key trends. Return JSON with:
- trends: list of dicts with 'trend' (name), 'impact' (high/medium/low), 'timeline' (short/medium/long-term)"""

        result = self._call_llm_for_analysis(prompt)
        trends = result.get("trends", [])

        self.analysis_context["trends"].extend(trends)

        return {
            "success": True,
            "trends": trends,
            "count": len(trends)
        }

    def _generate_recommendations(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic recommendations"""
        focus_area = arguments.get("focus_area", "general strategy")
        priority = arguments.get("priority", "high")

        # Include previous analysis findings
        findings_summary = self._summarize_findings()

        prompt = f"""Generate strategic recommendations based on the analysis.

Research Data:
{self._format_research_data()}

Analysis Findings:
{findings_summary}

Focus Area: {focus_area}
Priority Level: {priority}

Generate 3-5 actionable recommendations. Return JSON with:
- recommendations: list of dicts with 'recommendation' (text) and 'rationale' (reasoning)"""

        result = self._call_llm_for_analysis(prompt)
        recommendations = result.get("recommendations", [])

        self.analysis_context["recommendations"].extend(recommendations)

        return {
            "success": True,
            "recommendations": recommendations,
            "count": len(recommendations)
        }

    def _call_llm_for_analysis(self, prompt: str) -> Dict[str, Any]:
        """Call LLM for analysis"""
        import json

        messages = [
            {
                "role": "system",
                "content": "You are an expert business analyst. Analyze the provided data and return structured insights in JSON format."
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
            return {"error": f"Failed to parse: {str(e)}"}

    def _format_research_data(self) -> str:
        """Format research data for LLM consumption"""
        import json

        if isinstance(self.research_data, str):
            return self.research_data

        # Limit size for LLM context
        formatted = json.dumps(self.research_data, indent=2)
        if len(formatted) > 4000:
            formatted = formatted[:4000] + "\n... (truncated)"

        return formatted

    def _summarize_findings(self) -> str:
        """Summarize accumulated analysis findings"""
        summary_parts = []

        if self.analysis_context["strengths"]:
            summary_parts.append(f"Strengths identified: {len(self.analysis_context['strengths'])}")
        if self.analysis_context["weaknesses"]:
            summary_parts.append(f"Weaknesses identified: {len(self.analysis_context['weaknesses'])}")
        if self.analysis_context["opportunities"]:
            summary_parts.append(f"Opportunities identified: {len(self.analysis_context['opportunities'])}")
        if self.analysis_context["threats"]:
            summary_parts.append(f"Threats identified: {len(self.analysis_context['threats'])}")
        if self.analysis_context["trends"]:
            summary_parts.append(f"Trends identified: {len(self.analysis_context['trends'])}")

        return "\n".join(summary_parts) if summary_parts else "No findings yet"

    def get_context(self) -> Dict[str, Any]:
        """Get accumulated analysis context"""
        return self.analysis_context

    def clear_context(self):
        """Clear accumulated context"""
        self.analysis_context = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
            "competitive_insights": [],
            "trends": [],
            "recommendations": []
        }

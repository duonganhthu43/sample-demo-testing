"""
Tool Definitions and Executor for LLM Function Calling
Defines all available tools that agents can use via LLM function calling
"""

from typing import Dict, List, Any, Optional, Callable
import json


# Tool definitions for OpenAI function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "research_company",
            "description": "Research a specific company to gather comprehensive information including overview, products, business model, key metrics, and recent developments",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The name of the company to research"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "description": "Depth of research: quick (basic info), standard (comprehensive), deep (exhaustive)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_market",
            "description": "Research a market or industry to understand size, trends, growth drivers, and key players",
            "parameters": {
                "type": "object",
                "properties": {
                    "market_or_industry": {
                        "type": "string",
                        "description": "The market or industry to research (e.g., 'Fintech', 'Cloud Computing', 'E-commerce')"
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "deep"],
                        "description": "Depth of research"
                    }
                },
                "required": ["market_or_industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_competitors",
            "description": "Identify and analyze competitors for a company in a specific industry",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to find competitors for"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry context"
                    }
                },
                "required": ["company_name", "industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "perform_swot_analysis",
            "description": "Perform SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis for a company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "perform_competitive_analysis",
            "description": "Analyze competitive positioning and dynamics for a company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "perform_trend_analysis",
            "description": "Identify and analyze market trends affecting a company or industry",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry context"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name", "industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_financials",
            "description": "Deep-dive financial analysis including revenue models, funding, valuation, and financial health",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_technology",
            "description": "Analyze technology stack, R&D capabilities, patents, and innovation",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_market_size",
            "description": "Calculate TAM/SAM/SOM and analyze market opportunity",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry context"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name", "industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment",
            "description": "Analyze customer sentiment, brand perception, and reputation",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_regulatory",
            "description": "Analyze regulatory landscape, compliance requirements, and legal risks",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company to analyze"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry context"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context from previous research (optional)"
                    }
                },
                "required": ["company_name", "industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_research_quality",
            "description": "Review the quality of research conducted so far and provide feedback on completeness, accuracy, depth, relevance, and clarity. Use this to ensure high-quality deliverables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company being researched"
                    },
                    "objectives": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The research objectives to evaluate against"
                    }
                },
                "required": ["company_name", "objectives"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Generate a comprehensive market research report based on all gathered information. This should typically be called as the final step after all research is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "The company the report is about"
                    },
                    "industry": {
                        "type": "string",
                        "description": "The industry context"
                    }
                },
                "required": ["company_name"]
            }
        }
    }
]


class ToolExecutor:
    """
    Executes tool calls requested by the LLM
    """

    def __init__(self, config):
        """Initialize with agents that provide tool implementations"""
        self.config = config

        # Lazy-initialize agents
        self._research_agent = None
        self._analysis_agent = None
        self._report_agent = None
        self._financial_agent = None
        self._technology_agent = None
        self._market_sizing_agent = None
        self._sentiment_agent = None
        self._regulatory_agent = None
        self._quality_reviewer_agent = None

        # Store context accumulated across tool calls
        self.context = {
            "research": [],
            "analysis": [],
            "specialized": [],
            "quality_reviews": []
        }

    def _get_research_agent(self):
        """Lazy initialize research agent"""
        if self._research_agent is None:
            from .research_agent import ResearchAgent
            self._research_agent = ResearchAgent(self.config)
        return self._research_agent

    def _get_analysis_agent(self):
        """Lazy initialize analysis agent"""
        if self._analysis_agent is None:
            from .analysis_agent import AnalysisAgent
            self._analysis_agent = AnalysisAgent(self.config)
        return self._analysis_agent

    def _get_report_agent(self):
        """Lazy initialize report agent"""
        if self._report_agent is None:
            from .report_agent import ReportAgent
            self._report_agent = ReportAgent(self.config)
        return self._report_agent

    def _get_financial_agent(self):
        """Lazy initialize financial agent"""
        if self._financial_agent is None:
            from .specialized_agents import FinancialAgent
            self._financial_agent = FinancialAgent(self.config)
        return self._financial_agent

    def _get_technology_agent(self):
        """Lazy initialize technology agent"""
        if self._technology_agent is None:
            from .specialized_agents import TechnologyAgent
            self._technology_agent = TechnologyAgent(self.config)
        return self._technology_agent

    def _get_market_sizing_agent(self):
        """Lazy initialize market sizing agent"""
        if self._market_sizing_agent is None:
            from .specialized_agents import MarketSizingAgent
            self._market_sizing_agent = MarketSizingAgent(self.config)
        return self._market_sizing_agent

    def _get_sentiment_agent(self):
        """Lazy initialize sentiment agent"""
        if self._sentiment_agent is None:
            from .specialized_agents import SentimentAgent
            self._sentiment_agent = SentimentAgent(self.config)
        return self._sentiment_agent

    def _get_regulatory_agent(self):
        """Lazy initialize regulatory agent"""
        if self._regulatory_agent is None:
            from .specialized_agents import RegulatoryAgent
            self._regulatory_agent = RegulatoryAgent(self.config)
        return self._regulatory_agent

    def _get_quality_reviewer_agent(self):
        """Lazy initialize quality reviewer agent"""
        if self._quality_reviewer_agent is None:
            from .quality_reviewer import QualityReviewerAgent
            self._quality_reviewer_agent = QualityReviewerAgent(self.config)
        return self._quality_reviewer_agent

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from the LLM

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Tool execution result
        """
        print(f"  🔧 Executing tool: {tool_name}")
        print(f"     Arguments: {arguments}")

        try:
            if tool_name == "research_company":
                agent = self._get_research_agent()
                result = agent.research_company(
                    company_name=arguments["company_name"],
                    depth=arguments.get("depth", "standard")
                )
                self.context["research"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "research_market":
                agent = self._get_research_agent()
                result = agent.research_market(
                    market_or_industry=arguments["market_or_industry"],
                    depth=arguments.get("depth", "standard")
                )
                self.context["research"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "research_competitors":
                agent = self._get_research_agent()
                result = agent.research_competitors(
                    company_name=arguments["company_name"],
                    industry=arguments["industry"]
                )
                self.context["research"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "perform_swot_analysis":
                agent = self._get_analysis_agent()
                context = arguments.get("context", {})
                result = agent.perform_swot_analysis(
                    company_name=arguments["company_name"],
                    research_data=context
                )
                self.context["analysis"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "perform_competitive_analysis":
                agent = self._get_analysis_agent()
                context = arguments.get("context", {})
                result = agent.perform_competitive_analysis(
                    company_name=arguments["company_name"],
                    research_data=context
                )
                self.context["analysis"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "perform_trend_analysis":
                agent = self._get_analysis_agent()
                context = arguments.get("context", {})
                result = agent.perform_trend_analysis(
                    company_name=arguments["company_name"],
                    industry=arguments["industry"],
                    research_data=context
                )
                self.context["analysis"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_financials":
                agent = self._get_financial_agent()
                context = {
                    "research": self.context["research"],
                    "analysis": self.context["analysis"]
                }
                result = agent.analyze_financials(
                    company_name=arguments["company_name"],
                    context=context
                )
                self.context["specialized"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_technology":
                agent = self._get_technology_agent()
                context = {
                    "research": self.context["research"],
                    "analysis": self.context["analysis"]
                }
                result = agent.analyze_technology(
                    company_name=arguments["company_name"],
                    context=context
                )
                self.context["specialized"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_market_size":
                agent = self._get_market_sizing_agent()
                context = {
                    "research": self.context["research"],
                    "analysis": self.context["analysis"]
                }
                result = agent.analyze_market_size(
                    company_name=arguments["company_name"],
                    industry=arguments["industry"],
                    context=context
                )
                self.context["specialized"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_sentiment":
                agent = self._get_sentiment_agent()
                context = {
                    "research": self.context["research"],
                    "analysis": self.context["analysis"]
                }
                result = agent.analyze_sentiment(
                    company_name=arguments["company_name"],
                    context=context
                )
                self.context["specialized"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_regulatory":
                agent = self._get_regulatory_agent()
                context = {
                    "research": self.context["research"],
                    "analysis": self.context["analysis"]
                }
                result = agent.analyze_regulatory(
                    company_name=arguments["company_name"],
                    industry=arguments["industry"],
                    context=context
                )
                self.context["specialized"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "review_research_quality":
                agent = self._get_quality_reviewer_agent()
                result = agent.review_research(
                    company_name=arguments["company_name"],
                    objectives=arguments["objectives"],
                    research_results=self.context["research"],
                    analysis_results=self.context["analysis"],
                    specialized_results=self.context["specialized"]
                )
                self.context["quality_reviews"].append(result.to_dict())
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "generate_report":
                agent = self._get_report_agent()
                result = agent.generate_full_report(
                    company_name=arguments["company_name"],
                    industry=arguments.get("industry", "General"),
                    research_results=self.context["research"],
                    analysis_results=self.context["analysis"],
                    specialized_results=self.context["specialized"] if self.context["specialized"] else None
                )
                return {"success": True, "result": result.to_dict()}

            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

        except Exception as e:
            print(f"     ❌ Error executing {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_context(self) -> Dict[str, Any]:
        """Get accumulated context from all tool calls"""
        return self.context

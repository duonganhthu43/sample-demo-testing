"""
Tool Definitions and Executor for Travel Planning Agent
Defines all tools available to the LLM and routes tool calls to agents
"""

from typing import Dict, List, Any, Optional
import json

from ..utils.config import get_config


# Tool definitions for LLM function calling (OpenAI format)
TOOL_DEFINITIONS = [
    # Research Tools
    {
        "type": "function",
        "function": {
            "name": "research_destination",
            "description": "Get comprehensive information about a travel destination including visa requirements, culture, best time to visit, and practical tips",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Name of the destination city or country"
                    }
                },
                "required": ["destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_flights",
            "description": "Search for available flights between two cities on specific dates",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Departure city or airport"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Arrival city or airport"
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Departure date in YYYY-MM-DD format"
                    },
                    "return_date": {
                        "type": "string",
                        "description": "Return date in YYYY-MM-DD format (optional for one-way)"
                    },
                    "max_budget": {
                        "type": "number",
                        "description": "Maximum budget per person per flight in USD"
                    },
                    "prefer_direct": {
                        "type": "boolean",
                        "description": "Whether to prefer direct flights"
                    }
                },
                "required": ["origin", "destination", "departure_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_accommodations",
            "description": "Search for hotels and accommodations at a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "City or area to search for accommodations"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "max_budget_per_night": {
                        "type": "number",
                        "description": "Maximum budget per night in USD"
                    },
                    "prefer_near_transport": {
                        "type": "boolean",
                        "description": "Whether to prefer hotels near public transport"
                    }
                },
                "required": ["destination", "check_in", "check_out"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_activities",
            "description": "Search for activities, attractions, and things to do at a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "City or area to search for activities"
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of interest categories (e.g., Cultural, Food, Nature, Shopping)"
                    },
                    "max_budget_per_activity": {
                        "type": "number",
                        "description": "Maximum budget per activity in USD"
                    }
                },
                "required": ["destination"]
            }
        }
    },

    # Analysis Tools
    {
        "type": "function",
        "function": {
            "name": "analyze_itinerary_feasibility",
            "description": "Analyze if a proposed itinerary is feasible given time constraints and logistics",
            "parameters": {
                "type": "object",
                "properties": {
                    "itinerary": {
                        "type": "object",
                        "description": "Proposed itinerary with activities and schedule"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "User constraints including budget, time, and preferences"
                    }
                },
                "required": ["itinerary", "constraints"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_cost_breakdown",
            "description": "Analyze detailed cost breakdown of the trip",
            "parameters": {
                "type": "object",
                "properties": {
                    "flights": {
                        "type": "object",
                        "description": "Selected flight information"
                    },
                    "hotels": {
                        "type": "object",
                        "description": "Selected hotel information"
                    },
                    "activities": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of planned activities"
                    },
                    "budget": {
                        "type": "number",
                        "description": "Total budget in USD"
                    },
                    "num_days": {
                        "type": "integer",
                        "description": "Number of days"
                    }
                },
                "required": ["budget"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_schedule_optimization",
            "description": "Optimize the activity schedule to minimize travel time and maximize experiences",
            "parameters": {
                "type": "object",
                "properties": {
                    "activities": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of planned activities"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "User preferences for scheduling"
                    },
                    "num_days": {
                        "type": "integer",
                        "description": "Number of days available"
                    }
                },
                "required": ["activities", "num_days"]
            }
        }
    },

    # Specialized Tools
    {
        "type": "function",
        "function": {
            "name": "optimize_budget",
            "description": "Find budget-friendly alternatives and optimize selections to fit within budget",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_selections": {
                        "type": "object",
                        "description": "Current flight, hotel, and activity selections"
                    },
                    "budget_limit": {
                        "type": "number",
                        "description": "Maximum budget in USD"
                    },
                    "priorities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "What to prioritize (e.g., accommodation, experiences)"
                    }
                },
                "required": ["current_selections", "budget_limit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_weather",
            "description": "Get weather forecast and packing recommendations for the trip dates",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Destination city"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Trip start date in YYYY-MM-DD format"
                    },
                    "num_days": {
                        "type": "integer",
                        "description": "Number of days to forecast"
                    }
                },
                "required": ["destination", "start_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_safety",
            "description": "Get safety information, tips, and warnings for the destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Destination city or country"
                    }
                },
                "required": ["destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_local_transport",
            "description": "Get information about local transportation options at the destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "Destination city"
                    }
                },
                "required": ["destination"]
            }
        }
    },

    # Output Tools
    {
        "type": "function",
        "function": {
            "name": "generate_itinerary",
            "description": "Generate a comprehensive day-by-day travel itinerary from all gathered information",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_details": {
                        "type": "boolean",
                        "description": "Whether to include detailed timing and costs"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_summary",
            "description": "Generate an executive summary of the trip plan",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_checklist": {
                        "type": "boolean",
                        "description": "Whether to include preparation checklist"
                    }
                },
                "required": []
            }
        }
    }
]


class ToolExecutor:
    """
    Executes tool calls by routing to appropriate agents
    Maintains context across tool calls
    """

    def __init__(self, config=None):
        self.config = config or get_config()

        # Lazy-initialized agents
        self._research_agent = None
        self._analysis_agent = None
        self._budget_agent = None
        self._weather_agent = None
        self._safety_agent = None
        self._transport_agent = None
        self._itinerary_agent = None

        # Context accumulation
        self.context = {
            "destination": None,
            "travel_dates": None,
            "num_days": 5,
            "constraints": {},
            "research": [],
            "analysis": [],
            "specialized": [],
            "itinerary": None
        }

    # Lazy agent initialization
    def _get_research_agent(self):
        if self._research_agent is None:
            from .research_agent import ResearchAgent
            self._research_agent = ResearchAgent(self.config)
        return self._research_agent

    def _get_analysis_agent(self):
        if self._analysis_agent is None:
            from .analysis_agent import AnalysisAgent
            self._analysis_agent = AnalysisAgent(self.config)
        return self._analysis_agent

    def _get_budget_agent(self):
        if self._budget_agent is None:
            from .specialized_agents import BudgetAgent
            self._budget_agent = BudgetAgent(self.config)
        return self._budget_agent

    def _get_weather_agent(self):
        if self._weather_agent is None:
            from .specialized_agents import WeatherAgent
            self._weather_agent = WeatherAgent(self.config)
        return self._weather_agent

    def _get_safety_agent(self):
        if self._safety_agent is None:
            from .specialized_agents import SafetyAgent
            self._safety_agent = SafetyAgent(self.config)
        return self._safety_agent

    def _get_transport_agent(self):
        if self._transport_agent is None:
            from .specialized_agents import TransportAgent
            self._transport_agent = TransportAgent(self.config)
        return self._transport_agent

    def _get_itinerary_agent(self):
        if self._itinerary_agent is None:
            from .itinerary_agent import ItineraryAgent
            self._itinerary_agent = ItineraryAgent(self.config)
        return self._itinerary_agent

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call and return the result

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Dictionary with tool result
        """
        print(f"Executing tool: {tool_name}")

        try:
            # Research Tools
            if tool_name == "research_destination":
                agent = self._get_research_agent()
                result = agent.research_destination(**arguments)
                self.context["destination"] = arguments.get("destination")
                self.context["research"].append({"type": "destination", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "research_flights":
                agent = self._get_research_agent()
                result = agent.research_flights(**arguments)
                self.context["research"].append({"type": "flights", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "research_accommodations":
                agent = self._get_research_agent()
                result = agent.research_accommodations(**arguments)
                self.context["research"].append({"type": "accommodations", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "research_activities":
                agent = self._get_research_agent()
                result = agent.research_activities(**arguments)
                self.context["research"].append({"type": "activities", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            # Analysis Tools
            elif tool_name == "analyze_itinerary_feasibility":
                agent = self._get_analysis_agent()
                result = agent.analyze_itinerary_feasibility(**arguments)
                self.context["analysis"].append({"type": "feasibility", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_cost_breakdown":
                agent = self._get_analysis_agent()
                # Get context data if not provided
                flights = arguments.get("flights", self._get_flights_from_context())
                hotels = arguments.get("hotels", self._get_hotels_from_context())
                activities = arguments.get("activities", self._get_activities_from_context())

                result = agent.analyze_cost_breakdown(
                    flights=flights,
                    hotels=hotels,
                    activities=activities,
                    budget=arguments.get("budget", 1500),
                    num_days=arguments.get("num_days", self.context.get("num_days", 5))
                )
                self.context["analysis"].append({"type": "cost", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_schedule_optimization":
                agent = self._get_analysis_agent()
                activities = arguments.get("activities", self._get_activities_from_context())
                result = agent.analyze_schedule_optimization(
                    activities=activities,
                    preferences=arguments.get("preferences", []),
                    num_days=arguments.get("num_days", self.context.get("num_days", 5))
                )
                self.context["analysis"].append({"type": "schedule", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            # Specialized Tools
            elif tool_name == "optimize_budget":
                agent = self._get_budget_agent()
                result = agent.optimize_budget(**arguments)
                self.context["specialized"].append({"type": "budget", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_weather":
                agent = self._get_weather_agent()
                result = agent.analyze_weather(**arguments)
                self.context["weather"] = result.to_dict()
                self.context["specialized"].append({"type": "weather", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_safety":
                agent = self._get_safety_agent()
                result = agent.analyze_safety(**arguments)
                self.context["specialized"].append({"type": "safety", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "analyze_local_transport":
                agent = self._get_transport_agent()
                result = agent.analyze_local_transport(**arguments)
                self.context["specialized"].append({"type": "transport", **result.to_dict()})
                return {"success": True, "result": result.to_dict()}

            # Output Tools
            elif tool_name == "generate_itinerary":
                agent = self._get_itinerary_agent()
                result = agent.generate_itinerary(self.context)
                self.context["itinerary"] = result.to_dict()
                return {"success": True, "result": result.to_dict()}

            elif tool_name == "generate_summary":
                agent = self._get_itinerary_agent()
                itinerary = self.context.get("itinerary", {})
                result = agent.generate_summary(itinerary, self.context)
                return {"success": True, "result": result.to_dict()}

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            print(f"Tool execution error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_flights_from_context(self) -> Dict:
        """Extract flight data from context"""
        for item in self.context["research"]:
            if item.get("type") == "flights":
                return item
        return {}

    def _get_hotels_from_context(self) -> Dict:
        """Extract hotel data from context"""
        for item in self.context["research"]:
            if item.get("type") == "accommodations":
                return item
        return {}

    def _get_activities_from_context(self) -> List[Dict]:
        """Extract activities from context"""
        for item in self.context["research"]:
            if item.get("type") == "activities":
                return item.get("activities", [])
        return []

    def set_context(self, key: str, value: Any):
        """Set a context value"""
        self.context[key] = value

    def get_context(self) -> Dict[str, Any]:
        """Get the full context"""
        return self.context

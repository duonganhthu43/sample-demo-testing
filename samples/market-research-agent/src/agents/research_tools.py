"""
Research Tools for Agentic Research Agent
Defines tools available to the LLM for conducting research
"""

from typing import Dict, List, Any

# Tool definitions for OpenAI function calling
RESEARCH_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Use this to find relevant sources, articles, and data about companies, markets, or industries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_from_url",
            "description": "Extract and retrieve content from a specific URL. Use this to get detailed information from web pages found in search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract content from"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_company_info",
            "description": "Extract structured company information (founded year, headquarters, employees, revenue, funding) from text. Use this after extracting content to parse specific company data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text containing company information"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_key_metrics",
            "description": "Extract key business metrics (market share, growth rate, valuation) from text. Use this to parse quantitative business data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text containing business metrics"
                    }
                },
                "required": ["text"]
            }
        }
    }
]


class ResearchToolExecutor:
    """
    Executes research tool calls from LLM function calling
    """

    def __init__(self, web_search_tool, data_extractor):
        """
        Initialize with tool instances

        Args:
            web_search_tool: WebSearchTool instance
            data_extractor: DataExtractor instance
        """
        self.web_search_tool = web_search_tool
        self.data_extractor = data_extractor
        self.context = {
            "search_results": [],
            "extracted_content": [],
            "structured_data": []
        }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a research tool call

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            if tool_name == "web_search":
                return self._execute_web_search(arguments)

            elif tool_name == "extract_from_url":
                return self._execute_extract_from_url(arguments)

            elif tool_name == "extract_company_info":
                return self._execute_extract_company_info(arguments)

            elif tool_name == "extract_key_metrics":
                return self._execute_extract_key_metrics(arguments)

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

    def _execute_web_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search"""
        query = arguments["query"]
        num_results = arguments.get("num_results", 10)

        results = self.web_search_tool.search(query, num_results)

        # Store in context
        self.context["search_results"].extend(results)

        # Return formatted results
        results_list = [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source
            }
            for r in results
        ]

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results_list
        }

    def _execute_extract_from_url(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from URL"""
        url = arguments["url"]

        extracted = self.data_extractor.extract_from_url(url)

        # Store in context
        self.context["extracted_content"].append(extracted)

        return {
            "success": True,
            "url": url,
            "title": extracted.get("title", ""),
            "description": extracted.get("description", ""),
            "text": extracted.get("text", "")[:2000],  # Limit to 2000 chars for LLM
            "word_count": extracted.get("word_count", 0),
            "domain": extracted.get("domain", "")
        }

    def _execute_extract_company_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured company info from text"""
        text = arguments["text"]

        company_info = self.data_extractor.extract_company_info(text)

        # Store in context
        self.context["structured_data"].append({
            "type": "company_info",
            "data": company_info
        })

        return {
            "success": True,
            "company_info": company_info,
            "fields_found": list(company_info.keys())
        }

    def _execute_extract_key_metrics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key business metrics from text"""
        text = arguments["text"]

        metrics = self.data_extractor.extract_key_metrics(text)

        # Store in context
        self.context["structured_data"].append({
            "type": "metrics",
            "data": metrics
        })

        return {
            "success": True,
            "metrics": metrics,
            "metrics_found": list(metrics.keys())
        }

    def get_context(self) -> Dict[str, Any]:
        """Get accumulated research context"""
        return self.context

    def clear_context(self):
        """Clear accumulated context"""
        self.context = {
            "search_results": [],
            "extracted_content": [],
            "structured_data": []
        }

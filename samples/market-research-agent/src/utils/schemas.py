"""
JSON Schema definitions for Structured Outputs

These schemas are used with OpenAI's structured outputs feature to ensure
the LLM always returns valid, schema-compliant JSON responses.

Reference: https://platform.openai.com/docs/guides/structured-outputs
"""

from typing import Dict, Any


def get_response_format(schema_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a response_format dict for structured outputs.

    Args:
        schema_name: Name identifier for the schema
        schema: JSON schema definition

    Returns:
        response_format dict for OpenAI API
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True
        }
    }


# ============================================================================
# Financial Agent Schema
# ============================================================================

FINANCIAL_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "revenue_model": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "revenue_streams": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "sustainability": {"type": "string"}
            },
            "required": ["description", "revenue_streams", "sustainability"],
            "additionalProperties": False
        },
        "funding_history": {
            "type": "object",
            "properties": {
                "total_raised": {"type": "string"},
                "key_investors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "funding_rounds": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["total_raised", "key_investors", "funding_rounds"],
            "additionalProperties": False
        },
        "financial_health": {
            "type": "object",
            "properties": {
                "assessment": {"type": "string"},
                "revenue_growth": {"type": "string"},
                "profitability": {"type": "string"},
                "burn_rate": {"type": "string"}
            },
            "required": ["assessment", "revenue_growth", "profitability", "burn_rate"],
            "additionalProperties": False
        },
        "financial_risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "mitigation": {"type": "string"}
                },
                "required": ["risk", "severity", "mitigation"],
                "additionalProperties": False
            }
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["revenue_model", "funding_history", "financial_health", "financial_risks", "recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Technology Agent Schema
# ============================================================================

TECHNOLOGY_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "tech_stack": {
            "type": "object",
            "properties": {
                "core_technologies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "infrastructure": {"type": "string"},
                "differentiation": {"type": "string"}
            },
            "required": ["core_technologies", "infrastructure", "differentiation"],
            "additionalProperties": False
        },
        "innovation_capability": {
            "type": "object",
            "properties": {
                "assessment": {"type": "string"},
                "r_and_d_focus": {"type": "string"},
                "innovation_examples": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["assessment", "r_and_d_focus", "innovation_examples"],
            "additionalProperties": False
        },
        "ip_portfolio": {
            "type": "object",
            "properties": {
                "patents": {"type": "string"},
                "proprietary_tech": {"type": "string"},
                "competitive_moat": {"type": "string"}
            },
            "required": ["patents", "proprietary_tech", "competitive_moat"],
            "additionalProperties": False
        },
        "technical_advantages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "advantage": {"type": "string"},
                    "impact": {"type": "string"}
                },
                "required": ["advantage", "impact"],
                "additionalProperties": False
            }
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["tech_stack", "innovation_capability", "ip_portfolio", "technical_advantages", "recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Market Sizing Agent Schema
# ============================================================================

MARKET_SIZING_SCHEMA = {
    "type": "object",
    "properties": {
        "tam": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "rationale": {"type": "string"},
                "sources": {"type": "string"}
            },
            "required": ["value", "rationale", "sources"],
            "additionalProperties": False
        },
        "sam": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "rationale": {"type": "string"}
            },
            "required": ["value", "rationale"],
            "additionalProperties": False
        },
        "som": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "rationale": {"type": "string"}
            },
            "required": ["value", "rationale"],
            "additionalProperties": False
        },
        "market_segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment": {"type": "string"},
                    "size": {"type": "string"},
                    "growth": {"type": "string"}
                },
                "required": ["segment", "size", "growth"],
                "additionalProperties": False
            }
        },
        "market_growth": {
            "type": "object",
            "properties": {
                "historical_cagr": {"type": "string"},
                "projected_cagr": {"type": "string"},
                "growth_drivers": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["historical_cagr", "projected_cagr", "growth_drivers"],
            "additionalProperties": False
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["tam", "sam", "som", "market_segments", "market_growth", "recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Sentiment Agent Schema
# ============================================================================

SENTIMENT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_sentiment": {
            "type": "object",
            "properties": {
                "overall": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                "score": {"type": "number"},
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["overall", "score", "evidence"],
            "additionalProperties": False
        },
        "brand_perception": {
            "type": "object",
            "properties": {
                "assessment": {"type": "string"},
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "weaknesses": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["assessment", "strengths", "weaknesses"],
            "additionalProperties": False
        },
        "sentiment_themes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "frequency": {"type": "string", "enum": ["high", "medium", "low"]},
                    "impact": {"type": "string"}
                },
                "required": ["theme", "frequency", "impact"],
                "additionalProperties": False
            }
        },
        "competitor_comparison": {
            "type": "object",
            "properties": {
                "vs_competitors": {"type": "string"},
                "differentiation": {"type": "string"}
            },
            "required": ["vs_competitors", "differentiation"],
            "additionalProperties": False
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["customer_sentiment", "brand_perception", "sentiment_themes", "competitor_comparison", "recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Regulatory Agent Schema
# ============================================================================

REGULATORY_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "key_regulations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "regulation": {"type": "string"},
                    "impact": {"type": "string"},
                    "compliance_status": {"type": "string", "enum": ["compliant", "at-risk", "unknown"]}
                },
                "required": ["regulation", "impact", "compliance_status"],
                "additionalProperties": False
            }
        },
        "compliance_status": {
            "type": "object",
            "properties": {
                "overall": {"type": "string"},
                "certifications": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "compliance_challenges": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["overall", "certifications", "compliance_challenges"],
            "additionalProperties": False
        },
        "regulatory_risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "mitigation": {"type": "string"}
                },
                "required": ["risk", "severity", "mitigation"],
                "additionalProperties": False
            }
        },
        "policy_changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "change": {"type": "string"},
                    "timeline": {"type": "string"},
                    "impact": {"type": "string"}
                },
                "required": ["change", "timeline", "impact"],
                "additionalProperties": False
            }
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["key_regulations", "compliance_status", "regulatory_risks", "policy_changes", "recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# SWOT Analysis Schema
# ============================================================================

SWOT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "strengths": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "strength": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": ["strength", "evidence"],
                "additionalProperties": False
            }
        },
        "weaknesses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "weakness": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": ["weakness", "evidence"],
                "additionalProperties": False
            }
        },
        "opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "opportunity": {"type": "string"},
                    "potential": {"type": "string"}
                },
                "required": ["opportunity", "potential"],
                "additionalProperties": False
            }
        },
        "threats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "threat": {"type": "string"},
                    "impact": {"type": "string"}
                },
                "required": ["threat", "impact"],
                "additionalProperties": False
            }
        },
        "strategic_recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["strengths", "weaknesses", "opportunities", "threats", "strategic_recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Competitive Analysis Schema
# ============================================================================

COMPETITIVE_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "competitive_position": {"type": "string"},
        "key_competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "strengths": {"type": "string"},
                    "weaknesses": {"type": "string"}
                },
                "required": ["name", "strengths", "weaknesses"],
                "additionalProperties": False
            }
        },
        "competitive_advantages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "advantage": {"type": "string"},
                    "impact": {"type": "string"}
                },
                "required": ["advantage", "impact"],
                "additionalProperties": False
            }
        },
        "competitive_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "gap": {"type": "string"},
                    "recommendation": {"type": "string"}
                },
                "required": ["gap", "recommendation"],
                "additionalProperties": False
            }
        },
        "market_share_insights": {"type": "string"},
        "strategic_recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["competitive_position", "key_competitors", "competitive_advantages", "competitive_gaps", "market_share_insights", "strategic_recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Trend Analysis Schema
# ============================================================================

TREND_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "market_trends": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "trend": {"type": "string"},
                    "impact": {"type": "string"},
                    "timeline": {"type": "string", "enum": ["short", "medium", "long"]}
                },
                "required": ["trend", "impact", "timeline"],
                "additionalProperties": False
            }
        },
        "technology_trends": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "trend": {"type": "string"},
                    "relevance": {"type": "string"}
                },
                "required": ["trend", "relevance"],
                "additionalProperties": False
            }
        },
        "consumer_trends": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "trend": {"type": "string"},
                    "opportunity": {"type": "string"}
                },
                "required": ["trend", "opportunity"],
                "additionalProperties": False
            }
        },
        "emerging_opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "opportunity": {"type": "string"},
                    "strategic_fit": {"type": "string"}
                },
                "required": ["opportunity", "strategic_fit"],
                "additionalProperties": False
            }
        },
        "potential_disruptions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "disruption": {"type": "string"},
                    "mitigation": {"type": "string"}
                },
                "required": ["disruption", "mitigation"],
                "additionalProperties": False
            }
        },
        "strategic_recommendations": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number"}
    },
    "required": ["market_trends", "technology_trends", "consumer_trends", "emerging_opportunities", "potential_disruptions", "strategic_recommendations", "confidence"],
    "additionalProperties": False
}


# ============================================================================
# Research Synthesis Schema
# ============================================================================

RESEARCH_SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "finding": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": ["category", "finding", "evidence"],
                "additionalProperties": False
            }
        },
        "confidence": {"type": "number"}
    },
    "required": ["summary", "findings", "confidence"],
    "additionalProperties": False
}

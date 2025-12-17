"""
Report Generator Agent
Creates comprehensive reports from research and analysis
"""

import time
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from ..utils.config import get_config
from ..utils.prompts import REPORT_AGENT_SYSTEM, get_report_prompt



@dataclass
class Report:
    """Report data structure"""
    title: str
    report_type: str
    content: str
    sections: Dict[str, str]
    metadata: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "report_type": self.report_type,
            "content": self.content,
            "sections": self.sections,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def save(self, filepath: str):
        """Save report to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(self.content)
        print(f"Report saved to: {filepath}")


class ReportAgent:
    """
    Agent specialized in generating professional reports
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="report_agent")
        self.llm_params = self.config.get_llm_params()
        self.output_dir = Path(self.config.app.output_dir) / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("ReportAgent initialized")

    def generate_executive_summary(
        self,
        company_name: str,
        industry: str,
        research_data: Dict[str, Any],
        analysis_data: Dict[str, Any]
    ) -> str:
        """
        Generate an executive summary

        Args:
            company_name: Company being analyzed
            industry: Industry context
            research_data: Research findings
            analysis_data: Analysis insights

        Returns:
            Executive summary text
        """
        start_time = time.time()
        print("Starting: ReportAgent - Generating executive summary")

        # Prepare data
        research_summary = self._format_data(research_data)
        analysis_summary = self._format_data(analysis_data)

        # Get prompt
        prompt = get_report_prompt(
            "executive_summary",
            company_name=company_name,
            industry=industry,
            research_data=research_summary,
            analysis_data=analysis_summary
        )

        messages = [
            {"role": "system", "content": REPORT_AGENT_SYSTEM},
            {"role": "user", "content": prompt}
        ]

        # Generate summary
        print("Generating executive summary with LLM...")
        summary = self._call_llm(messages)

        duration = time.time() - start_time
        print(f"Complete: ReportAgent - {duration:.2f}s")

        return summary

    def generate_full_report(
        self,
        company_name: str,
        industry: str,
        research_results: List[Dict[str, Any]],
        analysis_results: List[Dict[str, Any]]
    ) -> Report:
        """
        Generate a comprehensive research report

        Args:
            company_name: Company being analyzed
            industry: Industry context
            research_results: List of research results
            analysis_results: List of analysis results

        Returns:
            Complete Report object
        """
        start_time = time.time()
        print(f"Starting: ReportAgent - Generating full report for {company_name}")

        # Build report sections incrementally
        sections = {}

        # 1. Executive Summary
        print("Generating executive summary...")
        sections["executive_summary"] = self.generate_executive_summary(
            company_name, industry,
            research_results[0] if research_results else {},
            analysis_results[0] if analysis_results else {}
        )

        # 2. Introduction
        print("Generating introduction...")
        sections["introduction"] = self._generate_introduction(company_name, industry)

        # 3. Company Overview (from research)
        print("Compiling company overview...")
        sections["company_overview"] = self._compile_company_overview(research_results)

        # 4. Market Analysis (from research)
        print("Compiling market analysis...")
        sections["market_analysis"] = self._compile_market_analysis(research_results)

        # 5. Competitive Landscape (from research and analysis)
        print("Compiling competitive landscape...")
        sections["competitive_landscape"] = self._compile_competitive_analysis(
            research_results, analysis_results
        )

        # 6. SWOT Analysis (from analysis)
        print("Compiling SWOT analysis...")
        sections["swot_analysis"] = self._compile_swot_section(analysis_results)

        # 7. Strategic Insights (from analysis)
        print("Generating strategic insights...")
        sections["strategic_insights"] = self._generate_strategic_insights(analysis_results)

        # 8. Recommendations
        print("Generating recommendations...")
        sections["recommendations"] = self._compile_recommendations(analysis_results)

        # 9. Conclusion
        print("Generating conclusion...")
        sections["conclusion"] = self._generate_conclusion(company_name, analysis_results)

        # Assemble full report
        full_content = self._assemble_report(company_name, sections)

        # Create report object
        report = Report(
            title=f"Market Research Report: {company_name}",
            report_type="comprehensive",
            content=full_content,
            sections=sections,
            metadata={
                "company": company_name,
                "industry": industry,
                "num_research_sources": len(research_results),
                "num_analyses": len(analysis_results),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": time.time() - start_time
            },
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save report
        filename = f"{company_name.replace(' ', '_').lower()}_report_{int(time.time())}.md"
        filepath = self.output_dir / filename
        report.save(str(filepath))

        duration = time.time() - start_time
        print(f"Complete: ReportAgent - {duration:.2f}s")

        return report

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call LLM for report generation"""
        start_time = time.time()

        if self.config.llm.provider == "openai":
            response = self.llm_client.chat.completions.create(
                messages=messages,
                **self.llm_params
            )
            content = response.choices[0].message.content

        elif self.config.llm.provider == "anthropic":
            system_msg = messages[0]["content"] if messages[0]["role"] == "system" else REPORT_AGENT_SYSTEM
            user_messages = [m for m in messages if m["role"] != "system"]

            response = self.llm_client.messages.create(
                system=system_msg,
                messages=user_messages,
                **self.llm_params
            )
            content = response.content[0].text

        return content

    def _generate_introduction(self, company_name: str, industry: str) -> str:
        """Generate report introduction"""
        messages = [
            {"role": "system", "content": REPORT_AGENT_SYSTEM},
            {"role": "user", "content": f"Write a professional introduction section for a market research report on {company_name} in the {industry} industry. Include research objectives, scope, and methodology. 2-3 paragraphs."}
        ]
        return self._call_llm(messages)

    def _generate_strategic_insights(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate strategic insights section"""
        # Compile all insights
        all_insights = []
        for analysis in analysis_results:
            if "insights" in analysis:
                all_insights.append(analysis["insights"])

        insights_summary = json.dumps(all_insights, indent=2)

        messages = [
            {"role": "system", "content": REPORT_AGENT_SYSTEM},
            {"role": "user", "content": f"Based on these analysis results:\n{insights_summary}\n\nWrite a Strategic Insights section highlighting the most important findings, critical success factors, risk factors, and growth opportunities. Use professional business language."}
        ]
        return self._call_llm(messages)

    def _generate_conclusion(self, company_name: str, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate conclusion section"""
        # Extract key points
        recommendations = []
        for analysis in analysis_results:
            if "recommendations" in analysis:
                recommendations.extend(analysis["recommendations"])

        rec_summary = "\n".join(f"- {rec}" for rec in recommendations[:5])

        messages = [
            {"role": "system", "content": REPORT_AGENT_SYSTEM},
            {"role": "user", "content": f"Write a conclusion section for a market research report on {company_name}. Key recommendations:\n{rec_summary}\n\nSummarize insights, provide future outlook, and final thoughts. 2-3 paragraphs."}
        ]
        return self._call_llm(messages)

    def _compile_company_overview(self, research_results: List[Dict[str, Any]]) -> str:
        """Compile company overview from research"""
        company_research = [r for r in research_results if r.get("research_type") == "company"]

        if not company_research:
            return "No company research data available."

        data = company_research[0]
        sections = []

        sections.append("## Company Overview\n")

        if "summary" in data:
            sections.append(data["summary"])
            sections.append("\n")

        if "findings" in data:
            sections.append("### Key Information\n")
            for finding in data["findings"]:
                if isinstance(finding, dict):
                    category = finding.get("category", "General")
                    details = finding.get("details", "")
                    sections.append(f"**{category}**: {details}\n")

        return "\n".join(sections)

    def _compile_market_analysis(self, research_results: List[Dict[str, Any]]) -> str:
        """Compile market analysis from research"""
        market_research = [r for r in research_results if r.get("research_type") == "market"]

        if not market_research:
            return "No market research data available."

        data = market_research[0]
        sections = []

        sections.append("## Market Analysis\n")

        if "summary" in data:
            sections.append(data["summary"])
            sections.append("\n")

        if "findings" in data:
            sections.append("### Market Insights\n")
            for finding in data["findings"]:
                sections.append(f"- {finding}\n")

        return "\n".join(sections)

    def _compile_competitive_analysis(
        self,
        research_results: List[Dict[str, Any]],
        analysis_results: List[Dict[str, Any]]
    ) -> str:
        """Compile competitive landscape section"""
        sections = []
        sections.append("## Competitive Landscape\n")

        # Get competitor research
        competitor_research = [r for r in research_results if r.get("research_type") == "competitors"]
        if competitor_research and "summary" in competitor_research[0]:
            sections.append(competitor_research[0]["summary"])
            sections.append("\n")

        # Get competitive analysis
        competitive_analysis = [a for a in analysis_results if a.get("analysis_type") == "competitive"]
        if competitive_analysis:
            insights = competitive_analysis[0].get("insights", {})

            if "competitive_position" in insights:
                sections.append("### Competitive Position\n")
                sections.append(insights["competitive_position"])
                sections.append("\n")

            if "key_competitors" in insights:
                sections.append("### Key Competitors\n")
                for comp in insights["key_competitors"]:
                    if isinstance(comp, dict):
                        name = comp.get("name", "Unknown")
                        sections.append(f"- **{name}**: {comp.get('description', '')}\n")

        return "\n".join(sections)

    def _compile_swot_section(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Compile SWOT analysis section"""
        swot_analysis = [a for a in analysis_results if a.get("analysis_type") == "swot"]

        if not swot_analysis:
            return "No SWOT analysis available."

        insights = swot_analysis[0].get("insights", {})
        sections = []

        sections.append("## SWOT Analysis\n")

        # Include visualization if available
        if "visualization" in insights:
            sections.append(insights["visualization"])
            sections.append("\n")

        # Strategic implications
        if "strategic_implications" in insights:
            sections.append("### Strategic Implications\n")
            sections.append(insights["strategic_implications"])
            sections.append("\n")

        return "\n".join(sections)

    def _compile_recommendations(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Compile recommendations section"""
        all_recommendations = []

        for analysis in analysis_results:
            if "recommendations" in analysis:
                all_recommendations.extend(analysis["recommendations"])

        if not all_recommendations:
            return "No recommendations available."

        sections = []
        sections.append("## Recommendations\n")
        sections.append("### Strategic Recommendations\n")

        for i, rec in enumerate(all_recommendations, 1):
            sections.append(f"{i}. {rec}\n")

        return "\n".join(sections)

    def _assemble_report(self, company_name: str, sections: Dict[str, str]) -> str:
        """Assemble final report from sections"""
        report_parts = []

        # Title and header
        report_parts.append(f"# Market Research Report: {company_name}\n")
        report_parts.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_parts.append("---\n\n")

        # Table of contents
        report_parts.append("## Table of Contents\n")
        report_parts.append("1. Executive Summary\n")
        report_parts.append("2. Introduction\n")
        report_parts.append("3. Company Overview\n")
        report_parts.append("4. Market Analysis\n")
        report_parts.append("5. Competitive Landscape\n")
        report_parts.append("6. SWOT Analysis\n")
        report_parts.append("7. Strategic Insights\n")
        report_parts.append("8. Recommendations\n")
        report_parts.append("9. Conclusion\n\n")
        report_parts.append("---\n\n")

        # Add each section
        section_order = [
            "executive_summary",
            "introduction",
            "company_overview",
            "market_analysis",
            "competitive_landscape",
            "swot_analysis",
            "strategic_insights",
            "recommendations",
            "conclusion"
        ]

        for section_key in section_order:
            if section_key in sections:
                report_parts.append(sections[section_key])
                report_parts.append("\n\n---\n\n")

        return "".join(report_parts)

    def _format_data(self, data: Any) -> str:
        """Format data for LLM consumption"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return json.dumps(data, indent=2)
        elif isinstance(data, list):
            return json.dumps(data, indent=2)
        else:
            return str(data)

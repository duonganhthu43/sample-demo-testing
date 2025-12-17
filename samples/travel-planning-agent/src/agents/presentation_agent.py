"""
Presentation Agent for Travel Planning
Uses LLM to format itinerary data into professional markdown output
"""

import json
from dataclasses import dataclass
from typing import Dict, Any

from ..utils.config import get_config


@dataclass
class PresentationResult:
    """Result from presentation formatting"""
    markdown: str
    format: str = "markdown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "markdown": self.markdown,
            "format": self.format
        }


PRESENTATION_SYSTEM_PROMPT = """You are a professional travel document formatter. Your task is to take raw travel itinerary data and format it into a beautiful, professional markdown document.

## Output Requirements

Create a well-structured markdown document with:

1. **Header Section**
   - Trip title with destination and emoji
   - Travel dates prominently displayed
   - A horizontal rule separator

2. **Trip Overview Table**
   - Duration, total cost, visa requirements
   - Language, local currency
   - Use a clean markdown table format

3. **Flight Details Section**
   - Outbound and return flights in separate subsections
   - Use tables showing: Airline, Price, Departure, Arrival, Duration, Stops
   - Include total flight cost
   - Add collapsible section with alternative flight options if available

4. **Accommodation Section**
   - Recommended hotel with name (linked if URL available)
   - Table with: Location, Price/night, Rating (use ⭐ stars), Near Transport, Distance
   - List amenities
   - Add collapsible section with other hotel options

5. **Day-by-Day Itinerary**
   - Each day as a subsection with day number and theme
   - Daily cost estimate
   - Table format: Time | Activity | Location | Cost
   - Link activities if source URLs available
   - Add tips/notes for each day

6. **Cost Breakdown Table**
   - Category breakdown: Flights, Accommodation, Activities, Food, Transport
   - Total at bottom in bold
   - Add money-saving tips as bullet points

7. **Packing Checklist**
   - Weather summary at top
   - Grouped checklist with categories (Essentials, Clothing, Electronics, Other)
   - Use markdown checkboxes: - [ ] Item

8. **Important Notes**
   - Use appropriate emojis for different note types
   - Visa info, weather warnings, constraints, travel tips

9. **Pre-Trip Checklist**
   - Markdown checkboxes for preparation tasks
   - Include visa, booking, insurance, bank notification, etc.

10. **Footer**
    - Disclaimer about prices/availability
    - Friendly sign-off

## Formatting Guidelines
- Use emojis appropriately (✈️ 🏨 📅 💰 🎒 ⚠️ ✅)
- Use collapsible sections (<details><summary>) for alternative options
- Keep tables clean and aligned
- Use bold for important information
- Use blockquotes for descriptions
- Make it visually appealing and easy to read
"""


class PresentationAgent:
    """
    Agent for formatting travel itineraries using LLM
    """

    def __init__(self, config=None):
        self.config = config or get_config()

    def format_itinerary(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> PresentationResult:
        """
        Format itinerary into professional markdown using LLM

        Args:
            itinerary: Generated itinerary data
            context: All context data

        Returns:
            PresentationResult with formatted markdown
        """
        print("Formatting itinerary with LLM...")

        # Prepare the data for the LLM
        data_summary = self._prepare_data_summary(itinerary, context)

        # Get LLM client
        client = self.config.get_llm_client(label="presentation_agent")

        # Call LLM to format the output
        try:
            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": PRESENTATION_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Please format the following travel itinerary data into a professional markdown document:\n\n{data_summary}"
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent formatting
                max_tokens=4000
            )

            markdown = response.choices[0].message.content
            print("Presentation formatted successfully")

            return PresentationResult(markdown=markdown)

        except Exception as e:
            print(f"LLM formatting failed: {str(e)}")
            # Fallback to basic formatting
            return PresentationResult(
                markdown=self._fallback_format(itinerary, context)
            )

    def _prepare_data_summary(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prepare a structured summary of all data for the LLM"""

        sections = []

        # Basic info
        sections.append("## TRIP DETAILS")
        sections.append(f"Destination: {itinerary.get('destination', 'Unknown')}")
        sections.append(f"Travel Dates: {itinerary.get('travel_dates', 'TBD')}")
        sections.append(f"Total Estimated Cost: ${itinerary.get('total_estimated_cost', 0):,.0f} {itinerary.get('currency', 'USD')}")
        sections.append(f"Number of Days: {len(itinerary.get('days', []))}")

        # Destination info
        dest_info = self._get_from_research(context, "destination")
        if dest_info:
            sections.append("\n## DESTINATION INFO")
            sections.append(f"Visa Requirements: {dest_info.get('visa_requirements', 'Check requirements')}")
            sections.append(f"Language: {dest_info.get('language', 'Local language')}")
            sections.append(f"Currency: {dest_info.get('currency', 'Local currency')}")
            if dest_info.get('culture_tips'):
                sections.append(f"Culture Tips: {', '.join(dest_info.get('culture_tips', [])[:3])}")

        # Flights
        flights = itinerary.get('flights')
        if flights:
            sections.append("\n## FLIGHT DATA")
            sections.append(json.dumps(flights, indent=2, default=str))

        # Accommodation
        accommodation = itinerary.get('accommodation')
        if accommodation:
            sections.append("\n## ACCOMMODATION DATA")
            sections.append(json.dumps(accommodation, indent=2, default=str))

        # Daily itinerary
        days = itinerary.get('days', [])
        if days:
            sections.append("\n## DAILY ITINERARY")
            sections.append(json.dumps(days, indent=2, default=str))

        # Cost analysis
        cost_analysis = self._get_from_analysis(context, "cost")
        if cost_analysis:
            sections.append("\n## COST BREAKDOWN")
            sections.append(f"Breakdown: {json.dumps(cost_analysis.get('breakdown', {}), indent=2)}")
            if cost_analysis.get('cost_saving_tips'):
                sections.append(f"Saving Tips: {cost_analysis.get('cost_saving_tips')}")

        # Weather
        weather = context.get('weather', {})
        if weather:
            sections.append("\n## WEATHER")
            summary = weather.get('summary', {})
            sections.append(f"Average Temperature: {summary.get('average_temp', 'N/A')}°C")
            sections.append(f"Rain Chance: {summary.get('average_rain_chance', 0)}%")
            if weather.get('packing_suggestions'):
                sections.append(f"Packing Suggestions: {weather.get('packing_suggestions')}")

        # Packing list
        packing = itinerary.get('packing_list', [])
        if packing:
            sections.append("\n## PACKING LIST")
            sections.append(str(packing))

        # Important notes
        notes = itinerary.get('important_notes', [])
        if notes:
            sections.append("\n## IMPORTANT NOTES")
            for note in notes:
                sections.append(f"- {note}")

        # Safety info
        safety = self._get_from_specialized(context, "safety")
        if safety:
            sections.append("\n## SAFETY INFO")
            if safety.get('tips'):
                sections.append(f"Tips: {safety.get('tips')[:3]}")
            if safety.get('emergency_contacts'):
                sections.append(f"Emergency: {safety.get('emergency_contacts')}")

        # Constraints
        constraints = context.get('constraints', {})
        if constraints:
            sections.append("\n## USER CONSTRAINTS")
            sections.append(f"Budget: {constraints.get('budget', 'Not specified')}")
            sections.append(f"Preferences: {constraints.get('preferences', [])}")
            sections.append(f"Hard Constraints: {constraints.get('hard_constraints', [])}")

        return "\n".join(sections)

    def _get_from_research(self, context: Dict, type_name: str) -> Dict:
        """Get item from research by type"""
        for item in context.get("research", []):
            if item.get("type") == type_name:
                return item
        return {}

    def _get_from_analysis(self, context: Dict, type_name: str) -> Dict:
        """Get item from analysis by type"""
        for item in context.get("analysis", []):
            if item.get("type") == type_name:
                return item
        return {}

    def _get_from_specialized(self, context: Dict, type_name: str) -> Dict:
        """Get item from specialized by type"""
        for item in context.get("specialized", []):
            if item.get("type") == type_name:
                return item
        return {}

    def _fallback_format(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Basic fallback formatting if LLM fails"""
        destination = itinerary.get('destination', 'Unknown')
        dates = itinerary.get('travel_dates', '')
        total_cost = itinerary.get('total_estimated_cost', 0)

        lines = [
            f"# ✈️ Travel Itinerary: {destination}",
            f"**Travel Dates:** {dates}",
            f"**Estimated Cost:** ${total_cost:,.0f}",
            "",
            "---",
            "",
            "## Summary",
            itinerary.get('summary', ''),
            "",
            "## Itinerary",
        ]

        for day in itinerary.get('days', []):
            lines.append(f"\n### Day {day.get('day')}: {day.get('theme', '')}")
            for item in day.get('schedule', []):
                lines.append(f"- {item.get('time')}: {item.get('activity')} ({item.get('location')})")

        if itinerary.get('packing_list'):
            lines.append("\n## Packing List")
            for item in itinerary.get('packing_list', []):
                lines.append(f"- [ ] {item}")

        if itinerary.get('important_notes'):
            lines.append("\n## Important Notes")
            for note in itinerary.get('important_notes', []):
                lines.append(f"- {note}")

        lines.append("\n---")
        lines.append("*Happy Travels! 🌏*")

        return "\n".join(lines)

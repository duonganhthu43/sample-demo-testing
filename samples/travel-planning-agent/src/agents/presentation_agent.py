"""
Presentation Agent for Travel Planning
Uses LLM to format itinerary data into professional markdown output
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

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


PRESENTATION_SYSTEM_PROMPT = """You are a professional travel document formatter. Your task is to take raw travel itinerary data and format it into a beautiful, professional markdown document with embedded images.

## Output Requirements

Create a well-structured markdown document with:

1. **Header Section**
   - Trip title with destination and emoji
   - Travel dates prominently displayed
   - **IMPORTANT: If a destination hero image (image_base64) is provided, embed it right after the title using:**
     ```
     ![Destination Name](data:image/jpeg;base64,...)
     ```
   - A horizontal rule separator

2. **Trip Overview Table**
   - Duration, total cost, visa requirements
   - Language, local currency
   - Use a clean markdown table format

3. **Flight Details Section**
   - Separate subsections for Outbound and Return flights
   - Show ALL flight options in comparison tables with columns:
     | Airline | Route | Departure | Arrival | Duration | Stops | Price |
   - Mark the recommended/selected option with ✅ or "**Selected**"
   - Include total flight cost (outbound + return)
   - Add a brief note explaining why the selected flights were chosen

4. **Accommodation Section**
   - **IMPORTANT: For each hotel that has image_base64 data, embed the image:**
     ```
     ![Hotel Name](data:image/jpeg;base64,...)
     ```
   - Show ALL hotel options in a comparison table with columns:
     | Hotel | Location | Price/Night | Total | Rating | Near Transport | Amenities |
   - Use ⭐ stars for ratings (e.g., ⭐⭐⭐⭐)
   - Mark the recommended option with ✅ or "**Recommended**"
   - Link hotel names if URLs are available: [Hotel Name](url)
   - Add a brief note explaining why the recommended hotel was chosen

5. **Day-by-Day Itinerary**
   - Each day as a subsection with day number and theme
   - Daily cost estimate
   - **IMPORTANT: For each activity that has image_base64 data, embed the image before or alongside the activity:**
     ```
     ![Activity Name](data:image/jpeg;base64,...)
     ```
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

## Image Embedding Guidelines
- When an item has `has_image: true`, embed it using a PLACEHOLDER syntax:
  ```
  ![Activity Name](IMAGE_PLACEHOLDER:activity_name_here)
  ```
- The placeholder will be replaced with actual image data after formatting
- Include image placeholders for:
  - Destination hero image (at the top, after title): `![Destination](IMAGE_PLACEHOLDER:hero)`
  - Hotel images: `![Hotel Name](IMAGE_PLACEHOLDER:hotel_name)`
  - Activity images: `![Activity Name](IMAGE_PLACEHOLDER:activity_name)`
- Use the exact name from the data as the placeholder key
- Place images prominently to make the document visually engaging

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

        # Ensure inputs are dicts, not None
        itinerary = itinerary or {}
        context = context or {}

        # Build image registry for post-processing (keeps base64 out of LLM context)
        image_registry = self._build_image_registry(context)

        # Prepare the data for the LLM (without base64 data)
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

            # Post-process: Replace IMAGE_PLACEHOLDER with actual base64 data
            markdown = self._replace_image_placeholders(markdown, image_registry)

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

        # Ensure inputs are dicts, not None
        itinerary = itinerary or {}
        context = context or {}

        sections = []

        # Basic info
        sections.append("## TRIP DETAILS")
        sections.append(f"Destination: {itinerary.get('destination', 'Unknown')}")
        sections.append(f"Travel Dates: {itinerary.get('travel_dates', 'TBD')}")
        sections.append(f"Total Estimated Cost: ${itinerary.get('total_estimated_cost', 0):,.0f} {itinerary.get('currency', 'USD')}")
        sections.append(f"Number of Days: {len(itinerary.get('days', []))}")

        # Note if hero image is available (don't pass actual base64 to save tokens)
        if self._get_hero_image(context):
            sections.append(f"\n## DESTINATION HERO IMAGE")
            sections.append(f"has_image: true (use IMAGE_PLACEHOLDER:hero)")

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
            sections.append(json.dumps(self._strip_base64_from_data(flights), indent=2, default=str))

        # Accommodation (strip base64 to save tokens, use has_image flag instead)
        accommodation = itinerary.get('accommodation')
        if accommodation:
            sections.append("\n## ACCOMMODATION DATA")
            sections.append(json.dumps(self._strip_base64_from_data(accommodation), indent=2, default=str))

        # Daily itinerary (strip base64 to save tokens)
        days = itinerary.get('days', [])
        if days:
            sections.append("\n## DAILY ITINERARY")
            sections.append(json.dumps(self._strip_base64_from_data(days), indent=2, default=str))

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
        context = context or {}
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == type_name:
                return item
        return {}

    def _get_from_analysis(self, context: Dict, type_name: str) -> Dict:
        """Get item from analysis by type"""
        context = context or {}
        for item in context.get("analysis") or []:
            if isinstance(item, dict) and item.get("type") == type_name:
                return item
        return {}

    def _get_from_specialized(self, context: Dict, type_name: str) -> Dict:
        """Get item from specialized by type"""
        context = context or {}
        for item in context.get("specialized") or []:
            if isinstance(item, dict) and item.get("type") == type_name:
                return item
        return {}

    def _get_hero_image(self, context: Dict) -> Optional[str]:
        """Get a hero image from activities or hotels for the destination"""
        context = context or {}

        # Try to get from activities first
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "activities":
                activities = item.get("activities", [])
                for activity in activities:
                    if isinstance(activity, dict) and activity.get("image_base64"):
                        return activity["image_base64"]

        # Try hotels next
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "accommodations":
                hotels = item.get("hotels", [])
                for hotel in hotels:
                    if isinstance(hotel, dict) and hotel.get("image_base64"):
                        return hotel["image_base64"]

        return None

    def _build_image_registry(self, context: Dict) -> Dict[str, str]:
        """
        Build a registry of image placeholders to base64 data.
        This keeps the actual base64 data out of the LLM context.
        """
        registry = {}
        context = context or {}

        # Add hero image
        hero = self._get_hero_image(context)
        if hero:
            registry["hero"] = hero

        # Add activity images
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "activities":
                for activity in item.get("activities", []):
                    if isinstance(activity, dict):
                        name = activity.get("name", "")
                        base64 = activity.get("image_base64")
                        if name and base64:
                            # Normalize key for matching
                            key = self._normalize_placeholder_key(name)
                            registry[key] = base64

        # Add hotel images
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "accommodations":
                for hotel in item.get("hotels", []):
                    if isinstance(hotel, dict):
                        name = hotel.get("name", "")
                        base64 = hotel.get("image_base64")
                        if name and base64:
                            key = self._normalize_placeholder_key(name)
                            registry[key] = base64

        print(f"Built image registry with {len(registry)} images")
        return registry

    def _normalize_placeholder_key(self, name: str) -> str:
        """Normalize a name for use as a placeholder key"""
        import re
        # Lowercase, replace spaces with underscores, remove special chars
        key = name.lower().strip()
        key = re.sub(r'[^a-z0-9\s]', '', key)
        key = re.sub(r'\s+', '_', key)
        return key

    def _strip_base64_from_data(self, data: Any) -> Any:
        """
        Recursively strip base64 image data from dicts/lists.
        Replaces image_base64 with has_image: true to save LLM tokens.
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == "image_base64":
                    # Replace base64 with flag
                    if value:
                        result["has_image"] = True
                    continue  # Skip the actual base64 data
                else:
                    result[key] = self._strip_base64_from_data(value)
            return result
        elif isinstance(data, list):
            return [self._strip_base64_from_data(item) for item in data]
        else:
            return data

    def _replace_image_placeholders(self, markdown: str, registry: Dict[str, str]) -> str:
        """
        Replace IMAGE_PLACEHOLDER:key patterns with actual base64 data.
        """
        import re

        def replace_match(match):
            key = match.group(1).lower().strip()
            # Try exact match first
            if key in registry:
                return registry[key]
            # Try normalized match
            normalized = self._normalize_placeholder_key(key)
            if normalized in registry:
                return registry[normalized]
            # Try partial match
            for reg_key, base64 in registry.items():
                if key in reg_key or reg_key in key:
                    return base64
            # No match found, return placeholder as-is
            return match.group(0)

        # Replace all IMAGE_PLACEHOLDER:xxx patterns
        pattern = r'IMAGE_PLACEHOLDER:([^)\s]+)'
        result = re.sub(pattern, replace_match, markdown)

        return result

    def _fallback_format(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Basic fallback formatting if LLM fails"""
        # Ensure inputs are dicts, not None
        itinerary = itinerary or {}
        context = context or {}

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

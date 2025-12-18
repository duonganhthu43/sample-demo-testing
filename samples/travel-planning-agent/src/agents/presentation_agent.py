"""
Presentation Agent for Travel Planning
Uses LLM to format itinerary data into professional markdown output
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

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

        # Build structured content array for better LLM understanding
        user_content = self._build_presentation_content(itinerary, context)

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
                        "content": user_content  # Array of {"type": "text", "text": ...}
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

    def _build_presentation_content(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build structured content array for presentation formatting.

        Returns an array of content parts for better LLM understanding:
        - Separates trip details, itinerary, and context data
        - Uses JSON for structured data
        """
        # Ensure inputs are dicts, not None
        itinerary = itinerary or {}
        context = context or {}

        content_parts = []

        # Part 1: Trip details as JSON
        trip_details = {
            "destination": itinerary.get("destination", "Unknown"),
            "travel_dates": itinerary.get("travel_dates", "TBD"),
            "total_estimated_cost": itinerary.get("total_estimated_cost", 0),
            "currency": itinerary.get("currency", "USD"),
            "num_days": len(itinerary.get("days", []))
        }
        # Note if hero image is available
        if self._get_hero_image(context):
            trip_details["has_hero_image"] = True
            trip_details["hero_image_placeholder"] = "IMAGE_PLACEHOLDER:hero"

        content_parts.append({
            "type": "text",
            "text": f"## Trip Details\n\n```json\n{json.dumps(trip_details, indent=2)}\n```"
        })

        # Part 2: Destination info
        dest_info = self._get_from_research(context, "destination")
        if dest_info:
            dest_data = {
                "visa_requirements": dest_info.get("visa_requirements", "Check requirements"),
                "language": dest_info.get("language", "Local language"),
                "currency": dest_info.get("currency", "Local currency"),
                "culture_tips": dest_info.get("culture_tips", [])[:3]
            }
            content_parts.append({
                "type": "text",
                "text": f"## Destination Info\n\n```json\n{json.dumps(dest_data, indent=2)}\n```"
            })

        # Part 3: Flights
        flights = itinerary.get("flights")
        if flights:
            content_parts.append({
                "type": "text",
                "text": f"## Flight Data\n\n```json\n{json.dumps(self._strip_base64_from_data(flights), indent=2, default=str)}\n```"
            })

        # Part 4: Accommodation
        accommodation = itinerary.get("accommodation")
        if accommodation:
            content_parts.append({
                "type": "text",
                "text": f"## Accommodation Data\n\n```json\n{json.dumps(self._strip_base64_from_data(accommodation), indent=2, default=str)}\n```"
            })

        # Part 5: Daily itinerary
        days = itinerary.get("days", [])
        if days:
            content_parts.append({
                "type": "text",
                "text": f"## Daily Itinerary\n\n```json\n{json.dumps(self._strip_base64_from_data(days), indent=2, default=str)}\n```"
            })

        # Part 6: Cost analysis
        cost_analysis = self._get_from_analysis(context, "cost")
        if cost_analysis:
            cost_data = {
                "breakdown": cost_analysis.get("breakdown", {}),
                "cost_saving_tips": cost_analysis.get("cost_saving_tips", [])
            }
            content_parts.append({
                "type": "text",
                "text": f"## Cost Breakdown\n\n```json\n{json.dumps(cost_data, indent=2, default=str)}\n```"
            })

        # Part 7: Weather
        weather = context.get("weather", {})
        if weather:
            summary = weather.get("summary", {})
            weather_data = {
                "average_temp": summary.get("average_temp", "N/A"),
                "rain_chance": summary.get("average_rain_chance", 0),
                "packing_suggestions": weather.get("packing_suggestions", [])
            }
            content_parts.append({
                "type": "text",
                "text": f"## Weather\n\n```json\n{json.dumps(weather_data, indent=2)}\n```"
            })

        # Part 8: Packing list & notes
        extras = {}
        packing = itinerary.get("packing_list", [])
        if packing:
            extras["packing_list"] = packing
        notes = itinerary.get("important_notes", [])
        if notes:
            extras["important_notes"] = notes
        if extras:
            content_parts.append({
                "type": "text",
                "text": f"## Additional Info\n\n```json\n{json.dumps(extras, indent=2)}\n```"
            })

        # Part 9: Safety info
        safety = self._get_from_specialized(context, "safety")
        if safety:
            safety_data = {
                "tips": safety.get("tips", [])[:3],
                "emergency_contacts": safety.get("emergency_contacts", {})
            }
            content_parts.append({
                "type": "text",
                "text": f"## Safety Info\n\n```json\n{json.dumps(safety_data, indent=2)}\n```"
            })

        # Part 10: Constraints
        constraints = context.get("constraints", {})
        if constraints:
            constraint_data = {
                "budget": constraints.get("budget", "Not specified"),
                "preferences": constraints.get("preferences", []),
                "hard_constraints": constraints.get("hard_constraints", [])
            }
            content_parts.append({
                "type": "text",
                "text": f"## User Constraints\n\n```json\n{json.dumps(constraint_data, indent=2)}\n```"
            })

        # Part 11: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nFormat the travel itinerary data above into a professional markdown document."
        })

        return content_parts

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

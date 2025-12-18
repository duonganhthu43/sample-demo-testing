"""
Presentation Agent for Travel Planning
Uses LLM to format itinerary data into professional markdown output
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from ..utils.config import get_config
from ..tools.image_utils import create_placeholder_svg


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
   - **IMPORTANT: If a destination hero image is provided, embed it using the placeholder:**
     ```
     ![Destination Name](IMAGE_PLACEHOLDER:hero)
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
   - **IMPORTANT: For each hotel that has image data, embed using its placeholder:**
     ```
     ![Hotel Name](IMAGE_PLACEHOLDER:hotel_name)
     ```
   - Show ALL hotel options in a comparison table with columns:
     | Hotel | Location | Price/Night | Total | Rating | Near Transport | Amenities |
   - Use ⭐ stars for ratings (e.g., ⭐⭐⭐⭐)
   - Mark the recommended option with ✅ or "**Recommended**"
   - Link hotel names if URLs are available: [Hotel Name](url)
   - Add a brief note explaining why the recommended hotel was chosen

5. **Day-by-Day Itinerary** (DETAILED FORMAT)
   - Each day as a subsection with day number and theme
   - Daily cost estimate prominently displayed

   **For EACH activity, use this detailed format (NOT a table):**

   ```markdown
   #### ⏰ 09:00 - 11:00 | Activity Name
   📍 **Location:** Location Name | 💰 **Cost:** $25

   ![Activity Name](IMAGE_PLACEHOLDER:activity_key)

   > Description paragraph from the activity data. This should be 2-3 sentences
   > describing what visitors will experience, historical significance, and practical tips.

   **💡 Tips:** Any helpful notes for this activity

   ---
   ```

   **IMPORTANT for Day-by-Day:**
   - Use the `description` field from each schedule item - it contains detailed info
   - **IMAGES**: If a schedule item has `image_placeholder`, copy it EXACTLY into the markdown:
     `![Activity Name](IMAGE_PLACEHOLDER:xxx)` where xxx is the key from image_placeholder
   - For flights: include arrival time, duration, and transportation options in the description
   - For meals: use 🍳 (breakfast), 🍜 (lunch), 🍽️ (dinner) icons and show:
     - Restaurant name and location
     - Recommended dishes
     - Price per person
     - Reservation info
   - Use blockquotes (>) for the description text to make it stand out
   - Add horizontal rules (---) between activities for visual separation
   - Link activities if source URLs available: [Activity Name](url)

   **Example meal format:**
   ```markdown
   #### 🍜 12:30 - 13:30 | Lunch at Tsukiji Outer Market
   📍 **Location:** Tsukiji, Tokyo | 💰 **Cost:** ~$25/person

   > Fresh sushi and seafood at Tokyo's famous fish market. Try the signature
   > omakase sushi at Sushi Dai or grab tamagoyaki from street vendors.
   > 5-min walk from previous activity. No reservation needed, expect 30-min queue.

   **🍣 Try:** Omakase sushi, Sea urchin (uni), Tamagoyaki

   ---
   ```

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

## Image Embedding Guidelines - CRITICAL

**YOU MUST EMBED ALL AVAILABLE IMAGES.** Images make the document visually engaging and professional.

### How to embed images:
1. Look for items with `"has_image": true` AND `"image_placeholder"` field
2. Copy the EXACT `image_placeholder` value (e.g., `IMAGE_PLACEHOLDER:best_western`)
3. Use it in markdown: `![Display Name](IMAGE_PLACEHOLDER:best_western)`

### Required image placements:
- **Hero image**: Always include `![Destination](IMAGE_PLACEHOLDER:hero)` after the title
- **Hotels**: For EACH hotel with `has_image: true`, embed its image above or beside its entry
- **Activities**: For EACH activity with `has_image: true`, embed its image in the day-by-day section
- **Top attractions**: Feature images prominently for must-see attractions

### Example - If hotel data shows:
```json
{"name": "Best Western", "has_image": true, "image_placeholder": "IMAGE_PLACEHOLDER:best_western"}
```
Then add in Accommodation section:
```markdown
![Best Western](IMAGE_PLACEHOLDER:best_western)
```

**IMPORTANT**:
- Use the EXACT placeholder value - do not modify it!
- **DO NOT add "data:image/jpeg;base64," prefix** - just use the raw placeholder
- The placeholder will be automatically replaced with the full data URI after formatting
- More images = better document quality
- Aim for at least 5-10 embedded images if available

**CORRECT**: `![Best Western](IMAGE_PLACEHOLDER:best_western)`
**WRONG**: `![Best Western](data:image/jpeg;base64,IMAGE_PLACEHOLDER:best_western)`

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

        # Use external image registry from ImageAgent if available,
        # otherwise build from research results (legacy behavior)
        external_registry = context.get("image_registry", {})
        if external_registry:
            image_registry = external_registry
            print(f"Using {len(image_registry)} images from ImageAgent")
        else:
            # Fallback to building registry from research results
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

            # Strip markdown code fence wrapper if LLM added it
            markdown = self._strip_code_fences(markdown)

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
        Creates multiple aliases for better matching.
        """
        registry = {}
        context = context or {}

        # Add hero image
        hero = self._get_hero_image(context)
        if hero:
            registry["hero"] = hero

        # Add activity images with multiple aliases
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "activities":
                for activity in item.get("activities", []):
                    if isinstance(activity, dict):
                        name = activity.get("name", "")
                        description = activity.get("description", "")
                        base64 = activity.get("image_base64")
                        if name and base64:
                            # Add multiple alias keys for the same image
                            # Include description for better attraction name extraction
                            self._add_image_aliases(registry, name, base64, description)

        # Add hotel images with multiple aliases
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "accommodations":
                for hotel in item.get("hotels", []):
                    if isinstance(hotel, dict):
                        name = hotel.get("name", "")
                        base64 = hotel.get("image_base64")
                        if name and base64:
                            self._add_image_aliases(registry, name, base64)

        # Add common attraction keyword mappings
        # This helps match itinerary-style keys (e.g., "sensoji_temple") to activity images
        self._add_common_attraction_aliases(registry)

        print(f"Built image registry with {len(registry)} keys")
        return registry

    def _add_common_attraction_aliases(self, registry: Dict[str, str]) -> None:
        """
        Add common attraction name variations as aliases.
        Maps various spellings/names to existing images.
        """
        # Find images that might be generic "attractions" or "things to do" images
        # and map common attraction names to them
        generic_activity_keys = []
        for key in registry:
            if any(term in key for term in ['attractions', 'things_to_do', 'places_to_visit', 'bucket_list']):
                generic_activity_keys.append(key)

        # Common Tokyo attraction name variations
        attraction_aliases = {
            # Temple/Shrine variations
            'sensoji': ['sensoji_temple', 'senso_ji', 'asakusa_temple', 'senso_ji_temple'],
            'meiji': ['meiji_shrine', 'meiji_jingu', 'meiji_temple'],
            'tokyo_tower': ['tokyo_tower', 'tokyotower'],
            'skytree': ['tokyo_skytree', 'skytree', 'sky_tree'],
            'imperial_palace': ['imperial_palace', 'tokyo_imperial_palace', 'palace'],
            'shibuya': ['shibuya_crossing', 'shibuya', 'shibuya_scramble'],
            'shinjuku': ['shinjuku', 'shinjuku_gyoen', 'omoide_yokocho'],
            'ueno': ['ueno_park', 'ueno', 'ueno_zoo'],
            'tsukiji': ['tsukiji', 'tsukiji_market', 'tsukiji_outer_market'],
            'akihabara': ['akihabara', 'akihabara_district', 'electric_town'],
            'harajuku': ['harajuku', 'takeshita_street', 'takeshita'],
            'ginza': ['ginza', 'ginza_district'],
            'roppongi': ['roppongi', 'roppongi_hills'],
            'odaiba': ['odaiba', 'teamlab', 'teamlab_borderless'],
            'asakusa': ['asakusa', 'asakusa_district', 'nakamise'],
        }

        # If we have a generic activity image, add aliases for common attractions
        if generic_activity_keys:
            fallback_image = registry[generic_activity_keys[0]]
            for primary, aliases in attraction_aliases.items():
                for alias in aliases:
                    if alias not in registry:
                        registry[alias] = fallback_image

    def _add_image_aliases(
        self,
        registry: Dict[str, str],
        name: str,
        base64: str,
        description: str = ""
    ) -> None:
        """Add multiple alias keys for better placeholder matching"""
        # Primary key (normalized full name)
        primary_key = self._normalize_placeholder_key(name)
        registry[primary_key] = base64

        # Extract meaningful keywords from name and add as aliases
        keywords = self._extract_semantic_keywords(name)
        for keyword in keywords:
            if keyword not in registry:  # Don't overwrite existing
                registry[keyword] = base64

        # Extract attraction names from description (these are the actual place names)
        if description:
            attraction_names = self._extract_attraction_names(description)
            for attraction in attraction_names:
                normalized = self._normalize_placeholder_key(attraction)
                if normalized and normalized not in registry:
                    registry[normalized] = base64

    def _extract_semantic_keywords(self, name: str) -> List[str]:
        """
        Extract meaningful keywords from a name for alias matching.
        Uses dynamic extraction that works for any destination.
        """
        import re
        keywords = []
        name_lower = name.lower()

        # 1. Add individual significant words (>3 chars, not stop words)
        stop_words = {
            'the', 'and', 'for', 'with', 'from', 'best', 'top', 'must', 'see',
            'visit', 'guide', 'tour', 'review', 'tourist', 'attractions',
            'things', 'japan', 'china', 'korea', 'france', 'italy', 'spain'
        }
        words = self._normalize_placeholder_key(name).split('_')
        for word in words:
            if len(word) > 3 and word not in stop_words:
                keywords.append(word)

        # 2. Create compound keys from significant word combinations
        significant_words = [w for w in words if len(w) > 3 and w not in stop_words]
        if len(significant_words) >= 2:
            # Add pairs of significant words
            for i in range(len(significant_words) - 1):
                compound = f"{significant_words[i]}_{significant_words[i+1]}"
                keywords.append(compound)

        # 3. Handle hyphenated names (e.g., "senso-ji" -> "sensoji", "senso_ji")
        if '-' in name_lower:
            # Replace hyphens with nothing and underscore
            no_hyphen = name_lower.replace('-', '')
            underscore = name_lower.replace('-', '_')
            keywords.append(self._normalize_placeholder_key(no_hyphen))
            keywords.append(self._normalize_placeholder_key(underscore))

        # 4. Add type suffixes as separate keywords for matching
        # e.g., "Tokyo Tower" -> also index as "tower"
        type_suffixes = ['temple', 'shrine', 'museum', 'palace', 'park', 'tower',
                        'castle', 'market', 'district', 'garden', 'bridge', 'station']
        for suffix in type_suffixes:
            if suffix in name_lower:
                # Add the word before the suffix + suffix (e.g., "tokyo_tower")
                pattern = rf'(\w+)\s+{suffix}'
                match = re.search(pattern, name_lower)
                if match:
                    keywords.append(f"{match.group(1)}_{suffix}")

        return list(set(keywords))

    def _normalize_placeholder_key(self, name: str) -> str:
        """Normalize a name for use as a placeholder key"""
        import re
        # Lowercase, replace spaces with underscores, remove special chars
        key = name.lower().strip()
        key = re.sub(r'[^a-z0-9\s]', '', key)
        key = re.sub(r'\s+', '_', key)
        return key

    def _strip_code_fences(self, text: str) -> str:
        """
        Strip markdown code fence wrapper if LLM added it.
        LLMs sometimes wrap output in ```markdown ... ``` which breaks rendering.
        """
        import re
        text = text.strip()

        # Remove opening code fence (```markdown, ```md, or just ```)
        text = re.sub(r'^```(?:markdown|md)?\s*\n?', '', text)

        # Remove closing code fence
        text = re.sub(r'\n?```\s*$', '', text)

        return text.strip()

    def _extract_attraction_names(self, text: str) -> List[str]:
        """
        Extract attraction/landmark names from text content.
        Looks for proper nouns that are likely place names.
        """
        import re
        attractions = []

        # Pattern 1: Names with landmark suffixes (Temple, Shrine, Museum, etc.)
        # e.g., "Sensoji Temple", "Meiji Shrine", "Tokyo Tower"
        landmark_pattern = r'([A-Z][a-z]+(?:[-\s][A-Z]?[a-z]+)*)\s+(Temple|Shrine|Museum|Palace|Park|Tower|Castle|Market|Garden|Bridge|Station|Gyoen|Jingu|Imperial)'
        for match in re.findall(landmark_pattern, text):
            name = f"{match[0]} {match[1]}".strip()
            if len(name) > 5:
                attractions.append(name)
                # Also add without suffix for flexible matching
                attractions.append(match[0])

        # Pattern 2: Japanese romanized names with suffixes
        # e.g., "Senso-ji", "Meiji-jingu", "Shinjuku-gyoen"
        japanese_pattern = r'([A-Z][a-z]+(?:-[a-z]+)?(?:\s+[A-Z][a-z]+)*)'
        for match in re.findall(japanese_pattern, text):
            if any(s in match.lower() for s in ['-ji', '-jingu', '-dera', '-koen', '-en', 'gyoen']):
                attractions.append(match)
                # Also add without hyphen
                attractions.append(match.replace('-', ''))

        # Pattern 3: Well-known district/area names
        # e.g., "Shibuya", "Shinjuku", "Asakusa", "Harajuku"
        district_pattern = r'\b(Shibuya|Shinjuku|Asakusa|Harajuku|Ginza|Akihabara|Ueno|Roppongi|Odaiba|Ikebukuro|Omoide Yokocho|Omoide|Yokocho)\b'
        for match in re.findall(district_pattern, text, re.IGNORECASE):
            attractions.append(match)

        # Pattern 4: Specific landmark names commonly mentioned
        specific_pattern = r'\b(Sensoji|Senso-ji|Meiji|Tokyo Tower|Skytree|Imperial Palace|Tsukiji|Shibuya Crossing|Takeshita|Nakamise)\b'
        for match in re.findall(specific_pattern, text, re.IGNORECASE):
            attractions.append(match)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for a in attractions:
            a_lower = a.lower().replace('-', '').replace(' ', '')
            if a_lower not in seen and len(a) > 3:
                seen.add(a_lower)
                unique.append(a)

        return unique

    def _strip_base64_from_data(self, data: Any) -> Any:
        """
        Recursively strip base64 image data from dicts/lists.
        Replaces image_base64 with has_image: true and adds image_placeholder
        to tell the LLM exactly what placeholder key to use.

        Also converts image_suggestion (from itinerary schedule items) to
        image_placeholder format for consistent handling by the LLM.
        """
        if isinstance(data, dict):
            result = {}
            has_base64 = False
            name_value = None
            image_suggestion_value = None

            # First pass: check for image_base64, name, and image_suggestion
            for key, value in data.items():
                if key == "image_base64" and value:
                    has_base64 = True
                elif key == "name":
                    name_value = value
                elif key == "image_suggestion" and value:
                    image_suggestion_value = value

            # Second pass: build result
            for key, value in data.items():
                if key == "image_base64":
                    # Replace base64 with flag and placeholder key
                    if has_base64:
                        result["has_image"] = True
                        if name_value:
                            # Include the exact placeholder key the LLM should use
                            placeholder_key = self._normalize_placeholder_key(name_value)
                            result["image_placeholder"] = f"IMAGE_PLACEHOLDER:{placeholder_key}"
                    continue  # Skip the actual base64 data
                elif key == "image_suggestion":
                    # Convert image_suggestion to image_placeholder format
                    # This allows schedule items to have consistent image handling
                    if image_suggestion_value:
                        placeholder_key = self._normalize_placeholder_key(image_suggestion_value)
                        result["image_placeholder"] = f"IMAGE_PLACEHOLDER:{placeholder_key}"
                    continue  # Replace image_suggestion with image_placeholder
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
        Uses multiple matching strategies and falls back to SVG placeholder.
        """
        import re

        matched_count = 0
        unmatched_keys = []

        # Pre-compute word sets for registry keys (for faster matching)
        registry_word_sets = {}
        for reg_key in registry:
            words = set(reg_key.split('_'))
            # Filter out very short words
            registry_word_sets[reg_key] = {w for w in words if len(w) > 2}

        def replace_match(match):
            nonlocal matched_count, unmatched_keys
            raw_key = match.group(1)
            key = raw_key.lower().strip()

            # Strategy 1: Exact match
            if key in registry:
                matched_count += 1
                return registry[key]

            # Strategy 2: Normalized match
            normalized = self._normalize_placeholder_key(key)
            if normalized in registry:
                matched_count += 1
                return registry[normalized]

            # Strategy 3: Stripped match (remove all underscores/hyphens for comparison)
            # e.g., "sensojitemple" should match "sensoji_temple"
            stripped_key = normalized.replace('_', '').replace('-', '')
            for reg_key, base64_data in registry.items():
                stripped_reg = reg_key.replace('_', '').replace('-', '')
                if stripped_key == stripped_reg:
                    matched_count += 1
                    return base64_data
                # Also check if one contains the other (for cases like "visitsensojitemple" vs "sensoji_temple")
                if stripped_key in stripped_reg or stripped_reg in stripped_key:
                    matched_count += 1
                    return base64_data

            # Strategy 4: Partial match (key contains registry key or vice versa)
            for reg_key, base64_data in registry.items():
                if key in reg_key or reg_key in key:
                    matched_count += 1
                    return base64_data

            # Strategy 4: Word overlap matching with scoring
            key_words = set(normalized.split('_'))
            key_words = {w for w in key_words if len(w) > 2}  # Filter short words

            best_match = None
            best_score = 0

            for reg_key, base64_data in registry.items():
                reg_words = registry_word_sets.get(reg_key, set())

                # Calculate overlap score
                overlap = key_words & reg_words
                if overlap:
                    # Score: number of matching chars in overlapping words
                    score = sum(len(w) for w in overlap)
                    # Bonus for matching significant words (>4 chars)
                    score += sum(2 for w in overlap if len(w) > 4)

                    if score > best_score:
                        best_score = score
                        best_match = base64_data

            # Require minimum score to accept match (at least one 4+ char word)
            if best_match and best_score >= 4:
                matched_count += 1
                return best_match

            # Strategy 5: Fuzzy single-word match for compound keys
            # e.g., "sensoji_temple" should match registry key "sensoji"
            for key_word in key_words:
                if len(key_word) >= 4:  # Only match on significant words
                    for reg_key, base64_data in registry.items():
                        if key_word == reg_key or key_word in reg_key:
                            matched_count += 1
                            return base64_data

            # No match found - create a placeholder SVG
            unmatched_keys.append(raw_key)
            label = raw_key.replace('_', ' ').title()
            return create_placeholder_svg(label, width=400, height=250)

        # First, fix any cases where LLM added data URI prefix before placeholder
        # e.g., "data:image/jpeg;base64,IMAGE_PLACEHOLDER:hero" -> "IMAGE_PLACEHOLDER:hero"
        markdown = re.sub(
            r'data:image/[a-z]+;base64,\s*(IMAGE_PLACEHOLDER:)',
            r'\1',
            markdown
        )

        # Replace all IMAGE_PLACEHOLDER:xxx patterns
        pattern = r'IMAGE_PLACEHOLDER:([^)\s]+)'
        result = re.sub(pattern, replace_match, markdown)

        # Debug logging
        if matched_count > 0:
            print(f"  Replaced {matched_count} image placeholders with actual images")
        if unmatched_keys:
            print(f"  Warning: {len(unmatched_keys)} placeholders not matched: {unmatched_keys[:5]}")
            print(f"  Available registry keys (sample): {list(registry.keys())[:10]}")

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

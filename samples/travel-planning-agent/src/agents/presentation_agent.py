"""
Presentation Agent for Travel Planning
Uses LLM to format itinerary data into professional markdown output
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from ..utils.config import get_config
from ..tools.image_utils import create_placeholder_svg, normalize_image_key


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

   **CRITICAL - IMAGES FOR EVERY ACTIVITY:**
   - **EVERY schedule item that has `image_placeholder` MUST have an image embedded!**
   - Copy the `image_placeholder` value EXACTLY as the image src:
     `![Activity Name](IMAGE_PLACEHOLDER:xxx)` where IMAGE_PLACEHOLDER:xxx is from the data
   - Example: if data has `"image_placeholder": "IMAGE_PLACEHOLDER:sensoji_temple"`, write:
     `![Sensoji Temple](IMAGE_PLACEHOLDER:sensoji_temple)`
   - Only skip images for Flight/Transport category items
   - Use the `description` field from each schedule item - it contains detailed info
   - For flights: include arrival time, duration, and transportation options in the description
   - For meals: use 🍳 (breakfast), 🍜 (lunch), 🍽️ (dinner) icons and show:
     - Restaurant name and location
     - Recommended dishes
     - Price per person
     - Reservation info
   - Use blockquotes (>) for the description text to make it stand out
   - Add horizontal rules (---) between activities for visual separation
   - Link activities if source URLs available: [Activity Name](url)

   **Example meal format (with image):**
   ```markdown
   #### 🍜 12:30 - 13:30 | Lunch at Tsukiji Outer Market
   📍 **Location:** Tsukiji, Tokyo | 💰 **Cost:** ~$25/person

   ![Tsukiji Outer Market](IMAGE_PLACEHOLDER:tsukiji_outer_market)

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

7. **Budget Optimization Section** (if budget data provided)
   - Show original vs optimized total with 💰 savings
   - List top 3-5 recommendations for saving money
   - Show budget-friendly alternatives if available
   - Use a clear format like:
     ```
     ## 💰 Budget Optimization

     | | Amount |
     |---|---|
     | Original Estimate | $X,XXX |
     | Optimized | $X,XXX |
     | **Potential Savings** | **$XXX** |

     ### Recommendations
     - ✅ Recommendation 1
     - ✅ Recommendation 2
     ```

8. **Packing Checklist**
   - Weather summary at top
   - Grouped checklist with categories (Essentials, Clothing, Electronics, Other)
   - Use markdown checkboxes: - [ ] Item

9. **Local Transport Section** (if transport data provided)
   - 🚇 Recommended transport passes (e.g., JR Pass, Metro cards)
   - ✈️ Airport transfer options with prices
   - 🚌 Main transport options with approximate costs
   - 💡 Transport tips and recommendations

10. **Important Notes**
    - Use appropriate emojis for different note types
    - Visa info, weather warnings, constraints, travel tips

11. **Pre-Trip Checklist**
    - Markdown checkboxes for preparation tasks
    - Include visa, booking, insurance, bank notification, etc.

12. **Footer**
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

        # Build image registry from research results (activities, hotels, restaurants)
        # then merge with ImageAgent's external registry if available
        image_registry = self._build_image_registry(context)

        # Merge external registry from ImageAgent (takes precedence for duplicate keys)
        external_registry = context.get("image_registry", {})
        if external_registry:
            image_registry.update(external_registry)
            print(f"Using {len(external_registry)} images from ImageAgent, {len(image_registry)} total")

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
        # Get travel_dates from itinerary, context, or constraints as fallback
        travel_dates = itinerary.get("travel_dates") or ""
        if not travel_dates:
            travel_dates = context.get("travel_dates") or ""
        if not travel_dates:
            travel_dates = context.get("constraints", {}).get("travel_dates", "")
        trip_details = {
            "destination": itinerary.get("destination", "Unknown"),
            "travel_dates": travel_dates if travel_dates else "TBD",
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

        # Part 5: Daily itinerary (with auto-generated image placeholders)
        days = itinerary.get("days", [])
        if days:
            # Process days to ensure image placeholders for activities
            processed_days = self._add_itinerary_image_placeholders(days, accommodation)
            content_parts.append({
                "type": "text",
                "text": f"## Daily Itinerary\n\n```json\n{json.dumps(self._strip_base64_from_data(processed_days), indent=2, default=str)}\n```"
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

        # Part 10: Budget optimization
        budget = self._get_from_specialized(context, "budget")
        if budget:
            budget_data = {
                "original_total": budget.get("original_total", 0),
                "optimized_total": budget.get("optimized_total", 0),
                "savings": budget.get("savings", 0),
                "recommendations": budget.get("recommendations", [])[:5],
                "budget_friendly_alternatives": budget.get("budget_friendly_alternatives", [])[:3]
            }
            content_parts.append({
                "type": "text",
                "text": f"## Budget Optimization\n\n```json\n{json.dumps(budget_data, indent=2)}\n```"
            })

        # Part 11: Transport info
        transport = self._get_from_specialized(context, "transport")
        if transport:
            transport_data = {
                "transport_options": transport.get("transport_options", [])[:4],
                "recommended_passes": transport.get("recommended_passes", [])[:3],
                "airport_transfer": transport.get("airport_transfer", {}),
                "tips": transport.get("tips", [])[:4]
            }
            content_parts.append({
                "type": "text",
                "text": f"## Local Transport\n\n```json\n{json.dumps(transport_data, indent=2)}\n```"
            })

        # Part 12: Constraints
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

        # Part 13: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nFormat the travel itinerary data above into a professional markdown document."
        })

        return content_parts

    def _add_itinerary_image_placeholders(
        self,
        days: List[Dict],
        accommodation: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Process itinerary days to ensure every activity has an image placeholder.
        Skips transport/flight items as specified in the schema.
        Adds hotel images and address for check-in activities.
        """
        import copy
        import re

        # Extract hotel info for check-in matching
        hotel_name = None
        hotel_image_key = None
        hotel_address = None
        hotel_location = None
        if accommodation:
            recommended = accommodation.get("recommended", {})
            if recommended:
                hotel_name = recommended.get("name", "")
                hotel_address = recommended.get("address", "")
                hotel_location = recommended.get("location", "")
                if hotel_name:
                    # Create image key from hotel name
                    hotel_image_key = re.sub(r'[^a-z0-9\s]', '', hotel_name.lower())
                    hotel_image_key = re.sub(r'\s+', '_', hotel_image_key.strip())

        processed_days = []
        for day in days:
            processed_day = copy.deepcopy(day)
            schedule = processed_day.get("schedule", [])

            for item in schedule:
                # Skip if already has image_suggestion or image_placeholder
                if item.get("image_suggestion") or item.get("image_placeholder"):
                    continue

                # Skip transport-related activities
                category = (item.get("category") or "").lower()
                activity = (item.get("activity") or "").lower()

                if category in ["flight", "transport"] or "flight" in activity:
                    continue

                # Check for hotel check-in/check-out activities
                if hotel_image_key and any(kw in activity for kw in ["check in", "check-in", "checkin", "hotel"]):
                    item["image_suggestion"] = hotel_image_key
                    # Add hotel address to the item for taxi booking/directions
                    if hotel_address or hotel_location:
                        address_info = hotel_address or hotel_location
                        existing_location = item.get("location", "")
                        if address_info and address_info not in existing_location:
                            item["location"] = address_info
                        # Also add to notes/description if not present
                        if not item.get("hotel_address"):
                            item["hotel_address"] = address_info
                    continue

                # Generate image placeholder from activity name
                activity_name = item.get("activity", "")
                if activity_name:
                    # Extract venue/attraction name from activity description
                    key = self._extract_venue_name(activity_name)
                    if key:
                        item["image_suggestion"] = key

            processed_days.append(processed_day)

        return processed_days

    # Class-level cache for LLM venue extractions to avoid redundant API calls
    _venue_extraction_cache: Dict[str, str] = {}

    def _extract_venue_name(self, activity: str) -> str:
        """
        Hybrid venue extraction: regex first, LLM fallback for complex cases.
        Works for any destination worldwide.

        Examples:
        - "Watch a Kabuki performance at Kabukiza Theater" → "kabukiza_theater"
        - "Visit the Eiffel Tower" → "eiffel_tower"
        - "Lunch at Bistro du Nord" → "bistro_du_nord"
        """
        # Try regex-based extraction first
        venue_key = self._extract_venue_regex(activity)

        # Check if result needs LLM fallback
        # Fallback conditions: key too long (>40 chars), too generic, or contains action words
        needs_llm = False
        if venue_key:
            # Too long suggests we couldn't extract a clean venue name
            if len(venue_key) > 40:
                needs_llm = True
            # Contains action words that shouldn't be in a venue name
            action_words = ['watch', 'take', 'enjoy', 'try', 'have', 'experience', 'class', 'performance', 'show']
            if any(word in venue_key for word in action_words):
                needs_llm = True
        else:
            needs_llm = True

        # Use LLM fallback if needed
        if needs_llm:
            llm_venue = self._extract_venue_llm(activity)
            if llm_venue:
                return llm_venue

        return venue_key

    def _extract_venue_regex(self, activity: str) -> str:
        """
        Regex-based venue extraction. Fast and deterministic.
        """
        import re

        activity_lower = activity.lower()

        # Pattern 1: "X at Y" - extract Y (the venue after "at")
        at_match = re.search(r'\bat\s+(.+)$', activity, re.IGNORECASE)
        if at_match:
            venue = at_match.group(1).strip()
            venue = re.sub(r'\s*\([^)]*\)\s*$', '', venue)  # Remove parenthetical
            venue = re.sub(r'\s*[-–]\s+.+$', '', venue)  # Remove dash suffix
            if venue and len(venue) > 3:
                return self._normalize_placeholder_key(venue)

        # Pattern 2: "X in/around Y" - extract Y for location-based activities
        location_match = re.search(r'\b(?:in|around)\s+([A-Z][a-zA-Z\s\']+)$', activity)
        if location_match:
            venue = location_match.group(1).strip()
            if venue and len(venue) > 3:
                return self._normalize_placeholder_key(venue)

        # Pattern 3: "Visit/Explore/See [the] X" - extract X (after action verb)
        action_match = re.search(
            r'^(?:visit|explore|see|tour|experience|discover|walk\s+(?:through|around)|stroll\s+(?:through|around))\s+(?:the\s+)?(.+)$',
            activity,
            re.IGNORECASE
        )
        if action_match:
            venue = action_match.group(1).strip()
            venue = re.sub(r'\s+(?:in the|during|for|and|with)\s+.+$', '', venue, flags=re.IGNORECASE)
            if venue and len(venue) > 3:
                return self._normalize_placeholder_key(venue)

        # Pattern 4: Meal patterns - "Breakfast/Lunch/Dinner at X"
        meal_match = re.search(
            r'^(?:breakfast|lunch|dinner|brunch|meal)\s+at\s+(.+)$',
            activity,
            re.IGNORECASE
        )
        if meal_match:
            venue = meal_match.group(1).strip()
            if venue and len(venue) > 3:
                return self._normalize_placeholder_key(venue)

        # Pattern 5: Look for proper nouns with landmark suffixes (universal)
        landmark_suffixes = (
            'Temple|Shrine|Museum|Palace|Park|Tower|Castle|Market|Garden|'
            'Theater|Theatre|Station|District|Crossing|Bridge|Square|Plaza|'
            'Cathedral|Church|Basilica|Mosque|Monument|Memorial|Gallery|'
            'Beach|Island|Mountain|Lake|River|Falls|House|Hall|Center|Centre|'
            'Stadium|Arena|Zoo|Aquarium|Pier|Harbor|Harbour|Bay|Fort|Fortress|'
            'Abbey|Chapel|Library|University|Campus|Airport|Terminal|Port'
        )
        landmark_match = re.search(
            rf'([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z]?[a-zA-Z\'\-]+)*)\s+({landmark_suffixes})',
            activity
        )
        if landmark_match:
            venue = f"{landmark_match.group(1)} {landmark_match.group(2)}"
            return self._normalize_placeholder_key(venue)

        # Pattern 6: "The X" pattern for famous landmarks
        the_match = re.search(r'\bthe\s+([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z]?[a-zA-Z\'\-]+)*)(?:\s|$|,)', activity)
        if the_match:
            venue = the_match.group(1).strip()
            if venue and len(venue) > 3:
                return self._normalize_placeholder_key(venue)

        # Fallback: Use full activity name but strip common action verbs
        key = re.sub(r'[^a-z0-9\s]', '', activity_lower)
        key = re.sub(r'\s+', '_', key.strip())

        prefixes_to_remove = [
            'visit_the_', 'visit_', 'explore_the_', 'explore_', 'see_the_', 'see_',
            'tour_the_', 'tour_', 'experience_the_', 'experience_', 'discover_the_', 'discover_',
            'watch_a_', 'watch_the_', 'take_a_', 'enjoy_a_', 'try_a_', 'have_a_',
            'lunch_at_', 'dinner_at_', 'breakfast_at_', 'brunch_at_', 'meal_at_',
            'walk_through_the_', 'walk_through_', 'walk_around_the_', 'walk_around_',
            'stroll_through_the_', 'stroll_through_', 'stroll_around_'
        ]
        for prefix in prefixes_to_remove:
            if key.startswith(prefix):
                key = key[len(prefix):]
                break

        return key if key else ""

    def _extract_venue_llm(self, activity: str) -> Optional[str]:
        """
        LLM-based venue extraction for complex cases.
        Uses caching to avoid redundant API calls.
        """
        # Check cache first
        if activity in PresentationAgent._venue_extraction_cache:
            return PresentationAgent._venue_extraction_cache[activity]

        try:
            client = self.config.get_llm_client(label="venue_extraction")

            prompt = f"""Extract the venue/location name from this activity description.
Return ONLY the venue name, nothing else. If no clear venue, return "unknown".

Activity: "{activity}"

Examples:
- "Watch a Kabuki performance at Kabukiza Theater" → Kabukiza Theater
- "Take a sushi making class at Tokyo Cooking Studio" → Tokyo Cooking Studio
- "Enjoy traditional tea ceremony" → Tea Ceremony (use the activity itself)
- "Free time for shopping" → unknown

Venue name:"""

            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50
            )

            venue = response.choices[0].message.content.strip()

            # Clean up response
            if venue.lower() in ['unknown', 'none', 'n/a', '']:
                result = None
            else:
                # Remove quotes if LLM added them
                venue = venue.strip('"\'')
                result = self._normalize_placeholder_key(venue)

            # Cache the result
            PresentationAgent._venue_extraction_cache[activity] = result
            return result

        except Exception as e:
            print(f"  LLM venue extraction failed: {str(e)}")
            return None

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

        # Add restaurant images with multiple aliases
        for item in context.get("research") or []:
            if isinstance(item, dict) and item.get("type") == "restaurants":
                # Process all restaurant lists
                all_restaurants = []
                all_restaurants.extend(item.get("restaurants", []))
                all_restaurants.extend(item.get("dinner_options", []))
                all_restaurants.extend(item.get("lunch_options", []))
                all_restaurants.extend(item.get("breakfast_options", []))

                for restaurant in all_restaurants:
                    if isinstance(restaurant, dict):
                        name = restaurant.get("name", "")
                        base64 = restaurant.get("image_base64")
                        image_suggestion = restaurant.get("image_suggestion", "")
                        if name and base64:
                            self._add_image_aliases(registry, name, base64)
                            # Also add the image_suggestion key directly
                            if image_suggestion:
                                registry[image_suggestion] = base64

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
        return normalize_image_key(name)

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
        Works for any destination - uses generic patterns for proper nouns and landmarks.
        """
        import re
        attractions = []

        # Pattern 1: Names with landmark suffixes (works globally)
        # e.g., "Sensoji Temple", "Eiffel Tower", "British Museum", "Central Park"
        landmark_suffixes = (
            'Temple|Shrine|Museum|Palace|Park|Tower|Castle|Market|Garden|Bridge|'
            'Station|Cathedral|Church|Basilica|Mosque|Synagogue|Monument|Memorial|'
            'Square|Plaza|Beach|Lake|River|Mountain|Hill|Valley|Falls|Bay|'
            'Gallery|Library|Theater|Theatre|Opera|Hall|Center|Centre|'
            'District|Quarter|Street|Avenue|Boulevard|Promenade|Boardwalk|'
            'Island|Peninsula|Pier|Harbor|Harbour|Port|Marina|'
            'Zoo|Aquarium|Sanctuary|Reserve|Forest|Jungle|Desert|'
            'Fort|Fortress|Citadel|Wall|Gate|Arch|Dome|Pyramid|'
            'University|College|Academy|Institute|Observatory|Planetarium'
        )
        landmark_pattern = rf'([A-Z][a-z]+(?:[-\s][A-Z]?[a-z]+)*)\s+({landmark_suffixes})'
        for match in re.findall(landmark_pattern, text):
            name = f"{match[0]} {match[1]}".strip()
            if len(name) > 5:
                attractions.append(name)
                # Also add the prefix for flexible matching
                if len(match[0]) > 3:
                    attractions.append(match[0])

        # Pattern 2: Multi-word proper nouns (2-4 capitalized words)
        # e.g., "Notre Dame", "Big Ben", "Golden Gate", "Empire State"
        proper_noun_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        for match in re.findall(proper_noun_pattern, text):
            # Filter out common phrases that aren't landmarks
            skip_phrases = {'The Best', 'Must See', 'Top Ten', 'Day One', 'Day Two'}
            if match not in skip_phrases and len(match) > 5:
                attractions.append(match)

        # Pattern 3: Names with hyphens (common in many languages)
        # e.g., "Senso-ji", "Champs-Élysées", "Notre-Dame"
        hyphenated_pattern = r'\b([A-Z][a-z]+(?:-[A-Za-z]+)+)\b'
        for match in re.findall(hyphenated_pattern, text):
            if len(match) > 4:
                attractions.append(match)
                # Also add without hyphen for flexible matching
                attractions.append(match.replace('-', ' '))
                attractions.append(match.replace('-', ''))

        # Pattern 4: Single capitalized words that might be landmarks (>5 chars)
        # e.g., "Colosseum", "Parthenon", "Acropolis"
        single_word_pattern = r'\b([A-Z][a-z]{5,})\b'
        for match in re.findall(single_word_pattern, text):
            # Skip common non-landmark words
            skip_words = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                         'Saturday', 'Sunday', 'January', 'February', 'March',
                         'April', 'August', 'September', 'October', 'November',
                         'December', 'Morning', 'Afternoon', 'Evening', 'Restaurant',
                         'Hotel', 'Airport', 'Station', 'Street', 'Avenue'}
            if match not in skip_words:
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
        Uses multiple matching strategies and falls back to category-based images.
        IMPORTANT: Prevents duplicate images - each base64 image can only be used once.
        """
        import re

        matched_count = 0
        unmatched_keys = []
        used_images = set()  # Track base64 images already used (by first 100 chars)

        # Pre-build normalized lookup tables for faster matching
        # Key: stripped key (no underscores/hyphens) -> Value: list of (original_key, base64)
        stripped_to_registry = {}
        for reg_key, base64_data in registry.items():
            stripped = reg_key.replace('_', '').replace('-', '').lower()
            if stripped not in stripped_to_registry:
                stripped_to_registry[stripped] = []
            stripped_to_registry[stripped].append((reg_key, base64_data))

        # Pre-compute word sets for registry keys (for faster matching)
        registry_word_sets = {}
        for reg_key in registry:
            words = set(reg_key.split('_'))
            # Filter out very short words
            registry_word_sets[reg_key] = {w for w in words if len(w) > 2}

        # Build category-based fallback images
        fallback_images = self._build_category_fallbacks(registry)

        def get_image_hash(base64_data: str) -> str:
            """Get a hash of the image for deduplication (first 100 chars is enough)"""
            return base64_data[:100] if base64_data else ""

        def try_use_image(base64_data: str, placeholder_key: str) -> Optional[str]:
            """Try to use an image, returns None if already used"""
            nonlocal matched_count
            img_hash = get_image_hash(base64_data)
            if img_hash in used_images:
                return None  # Image already used elsewhere
            used_images.add(img_hash)
            matched_count += 1
            return base64_data

        def replace_match(match):
            nonlocal matched_count, unmatched_keys
            raw_key = match.group(1)
            key = raw_key.lower().strip()

            # Strategy 1: Exact match
            if key in registry:
                result = try_use_image(registry[key], key)
                if result:
                    return result

            # Strategy 2: Normalized match
            normalized = self._normalize_placeholder_key(key)
            if normalized in registry:
                result = try_use_image(registry[normalized], normalized)
                if result:
                    return result

            # Strategy 3: Stripped match using pre-built lookup table
            # e.g., "sensojitemple" should match "sensoji_temple"
            stripped_key = normalized.replace('_', '').replace('-', '').lower()
            if stripped_key in stripped_to_registry:
                for reg_key, base64_data in stripped_to_registry[stripped_key]:
                    result = try_use_image(base64_data, reg_key)
                    if result:
                        return result

            # Strategy 3b: Contains match (for cases like "visitsensojitemple" vs "sensoji_temple")
            for stripped_reg, entries in stripped_to_registry.items():
                if len(stripped_key) > 5 and len(stripped_reg) > 5:
                    if stripped_key in stripped_reg or stripped_reg in stripped_key:
                        for reg_key, base64_data in entries:
                            result = try_use_image(base64_data, reg_key)
                            if result:
                                return result

            # Strategy 4: Partial match (key contains registry key or vice versa)
            for reg_key, base64_data in registry.items():
                if key in reg_key or reg_key in key:
                    result = try_use_image(base64_data, reg_key)
                    if result:
                        return result

            # Strategy 5: Word overlap matching with scoring
            key_words = set(normalized.split('_'))
            key_words = {w for w in key_words if len(w) > 2}  # Filter short words

            best_match = None
            best_match_key = None
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
                        best_match_key = reg_key

            # Require minimum score to accept match (at least one 4+ char word)
            if best_match and best_score >= 4:
                result = try_use_image(best_match, best_match_key)
                if result:
                    return result

            # Strategy 6: Fuzzy single-word match for compound keys
            # e.g., "sensoji_temple" should match registry key "sensoji"
            for key_word in key_words:
                if len(key_word) >= 4:  # Only match on significant words
                    for reg_key, base64_data in registry.items():
                        if key_word == reg_key or key_word in reg_key:
                            result = try_use_image(base64_data, reg_key)
                            if result:
                                return result

            # Strategy 7: Category-based fallback
            # When specific image is unavailable, use any available image from same category
            # This is better than showing a placeholder SVG
            category = self._detect_category(raw_key)
            if category and category in fallback_images:
                img_hash = get_image_hash(fallback_images[category])
                # Only use if this specific fallback hasn't been used as a primary match
                # (allow reuse for fallbacks to avoid too many placeholders)
                if img_hash not in used_images or len(unmatched_keys) > 5:
                    matched_count += 1
                    return fallback_images[category]

            # No match found - create a placeholder SVG
            unmatched_keys.append(raw_key)
            label = self._humanize_key(raw_key)
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
        total_placeholders = matched_count + len(unmatched_keys)
        print(f"  Image placeholders: {matched_count}/{total_placeholders} matched")
        if unmatched_keys:
            print(f"  Unmatched placeholders: {unmatched_keys[:5]}{'...' if len(unmatched_keys) > 5 else ''}")
            # Show stripped versions for debugging
            stripped_samples = [k.replace('_', '').replace('-', '').lower() for k in unmatched_keys[:3]]
            available_stripped = list(stripped_to_registry.keys())[:8]
            print(f"  Stripped unmatched: {stripped_samples}")
            print(f"  Stripped registry: {available_stripped}")

        return result

    def _build_category_fallbacks(self, registry: Dict[str, str]) -> Dict[str, str]:
        """Build fallback images for each category (hotel, restaurant, activity)"""
        fallbacks = {}

        # Find the first available image for each category type
        hotel_keywords = ['hotel', 'inn', 'hostel', 'resort', 'lodge', 'accommodation']
        restaurant_keywords = ['restaurant', 'cafe', 'ramen', 'sushi', 'food', 'dining', 'eat']
        activity_keywords = ['temple', 'shrine', 'museum', 'park', 'tower', 'palace', 'attraction']

        for key, base64 in registry.items():
            key_lower = key.lower()

            # Check for hotel category
            if 'hotel' not in fallbacks:
                if any(kw in key_lower for kw in hotel_keywords):
                    fallbacks['hotel'] = base64

            # Check for restaurant category
            if 'restaurant' not in fallbacks:
                if any(kw in key_lower for kw in restaurant_keywords):
                    fallbacks['restaurant'] = base64

            # Check for activity category
            if 'activity' not in fallbacks:
                if any(kw in key_lower for kw in activity_keywords):
                    fallbacks['activity'] = base64

            # Stop if all categories have fallbacks
            if len(fallbacks) >= 3:
                break

        # Use hero as ultimate fallback for any missing category
        if 'hero' in registry:
            for category in ['hotel', 'restaurant', 'activity']:
                if category not in fallbacks:
                    fallbacks[category] = registry['hero']

        return fallbacks

    def _humanize_key(self, key: str) -> str:
        """
        Convert a run-together or underscore-separated key into readable text.

        Examples:
            "sensojitemple" -> "Sensoji Temple"
            "sensoji_temple" -> "Sensoji Temple"
            "tokyotower" -> "Tokyo Tower"
            "ichiran_ramen" -> "Ichiran Ramen"
        """
        # First, replace underscores with spaces
        label = key.replace('_', ' ')

        # If still no spaces, try to detect word boundaries
        if ' ' not in label:
            # Common landmark/venue suffixes to detect word boundaries
            suffixes = [
                'temple', 'shrine', 'museum', 'palace', 'park', 'tower',
                'castle', 'market', 'garden', 'bridge', 'station', 'district',
                'crossing', 'street', 'ramen', 'sushi', 'restaurant', 'cafe',
                'hotel', 'inn', 'hostel', 'resort', 'gyoen', 'jingu', 'dori',
                'gai', 'cho', 'ku', 'shi', 'square', 'plaza', 'center', 'centre'
            ]

            # Try to insert space before common suffixes
            label_lower = label.lower()
            for suffix in suffixes:
                if label_lower.endswith(suffix) and len(label_lower) > len(suffix):
                    prefix_end = len(label) - len(suffix)
                    prefix = label[:prefix_end]
                    suffix_part = label[prefix_end:]
                    # Only split if prefix is substantial
                    if len(prefix) >= 3:
                        label = f"{prefix} {suffix_part}"
                        break

        return label.title()

    def _detect_category(self, key: str) -> Optional[str]:
        """Detect the category of a placeholder key"""
        key_lower = key.lower()

        # Skip generic placeholders - these should use placeholder SVGs, not fallback images
        # This prevents reusing the same restaurant image for "Local restaurant near Day X area"
        if 'local_restaurant' in key_lower or 'near_day' in key_lower or 'day_area' in key_lower:
            return None

        # Hotel patterns
        if any(kw in key_lower for kw in ['hotel', 'inn', 'hostel', 'resort', 'lodge', 'prince', 'hilton', 'marriott', 'hyatt']):
            return 'hotel'

        # Restaurant patterns
        if any(kw in key_lower for kw in ['restaurant', 'cafe', 'ramen', 'sushi', 'ichiran', 'dining', 'food', 'eat', 'lunch', 'dinner', 'breakfast']):
            return 'restaurant'

        # Activity patterns (default for other location-like keys)
        if any(kw in key_lower for kw in ['temple', 'shrine', 'museum', 'park', 'tower', 'palace', 'castle', 'market', 'district', 'crossing']):
            return 'activity'

        return None

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

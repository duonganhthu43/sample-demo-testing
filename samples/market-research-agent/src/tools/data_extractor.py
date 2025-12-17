"""
Data Extraction Tool
Extracts and processes data from various sources
"""

import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False



class DataExtractor:
    """
    Extracts structured data from web pages and text
    """

    # In-memory cache for URL extractions (shared across instances)
    _url_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.session = requests.Session() if BS4_AVAILABLE else None
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Market Research Bot)'
        }) if BS4_AVAILABLE else None

    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL

        Args:
            url: URL to extract from

        Returns:
            Dictionary with extracted data
        """
        # Check cache first
        if url in DataExtractor._url_cache:
            print(f"Cache hit for URL: {url}")
            return DataExtractor._url_cache[url]

        if not BS4_AVAILABLE:
            print("BeautifulSoup not available, returning mock data")
            result = self._mock_url_data(url)
            DataExtractor._url_cache[url] = result
            return result

        try:
            print(f"Extracting data from: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            text = self._extract_text(soup)

            result = {
                "url": url,
                "title": title,
                "description": description,
                "text": text[:5000],  # Limit text length
                "word_count": len(text.split()),
                "domain": urlparse(url).netloc
            }

            # Store in cache
            DataExtractor._url_cache[url] = result
            return result

        except Exception as e:
            print(f"Failed to extract from {url}: {str(e)}")
            result = self._mock_url_data(url)
            DataExtractor._url_cache[url] = result
            return result

    def extract_company_info(self, text: str) -> Dict[str, Any]:
        """
        Extract company information from text using patterns

        Args:
            text: Text containing company information

        Returns:
            Dictionary with extracted company info
        """
        info = {
            "founded": self._extract_founded_year(text),
            "headquarters": self._extract_headquarters(text),
            "employees": self._extract_employee_count(text),
            "revenue": self._extract_revenue(text),
            "funding": self._extract_funding(text),
        }

        return {k: v for k, v in info.items() if v}

    def extract_key_metrics(self, text: str) -> Dict[str, Any]:
        """
        Extract key business metrics from text

        Args:
            text: Text containing metrics

        Returns:
            Dictionary of extracted metrics
        """
        metrics = {}

        # Market share
        market_share_match = re.search(r'market share[:\s]+(\d+\.?\d*)%', text, re.IGNORECASE)
        if market_share_match:
            metrics["market_share_percent"] = float(market_share_match.group(1))

        # Growth rate
        growth_match = re.search(r'growth rate[:\s]+(\d+\.?\d*)%', text, re.IGNORECASE)
        if growth_match:
            metrics["growth_rate_percent"] = float(growth_match.group(1))

        # Valuation
        valuation_match = re.search(r'valuation[:\s]+\$(\d+\.?\d*)\s*(billion|million)', text, re.IGNORECASE)
        if valuation_match:
            amount = float(valuation_match.group(1))
            unit = valuation_match.group(2).lower()
            metrics["valuation_usd"] = amount * (1e9 if unit == "billion" else 1e6)

        return metrics

    def extract_competitors(self, text: str) -> List[str]:
        """
        Extract competitor names from text

        Args:
            text: Text mentioning competitors

        Returns:
            List of competitor names
        """
        competitors = set()

        # Look for common patterns
        patterns = [
            r'competitors?\s+(?:include|are|such as)[:\s]+([^.]+)',
            r'competing with\s+([^.]+)',
            r'rivals?\s+(?:include|are|such as)[:\s]+([^.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Split on common delimiters
                names = re.split(r',|\sand\s', match)
                for name in names:
                    name = name.strip()
                    if len(name) > 2 and len(name) < 50:
                        competitors.add(name)

        return list(competitors)

    def _extract_title(self, soup: "BeautifulSoup") -> str:
        """Extract page title"""
        if soup.title:
            return soup.title.string.strip()
        return ""

    def _extract_description(self, soup: "BeautifulSoup") -> str:
        """Extract page description"""
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()

        og_desc = soup.find("meta", {"property": "og:description"})
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        return ""

    def _extract_text(self, soup: "BeautifulSoup") -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_founded_year(self, text: str) -> Optional[int]:
        """Extract company founding year"""
        patterns = [
            r'founded in (\d{4})',
            r'established in (\d{4})',
            r'founded[:\s]+(\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1800 <= year <= 2024:
                    return year
        return None

    def _extract_headquarters(self, text: str) -> Optional[str]:
        """Extract company headquarters location"""
        patterns = [
            r'headquartered in ([^.,]+)',
            r'headquarters[:\s]+([^.,]+)',
            r'based in ([^.,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) < 100:
                    return location
        return None

    def _extract_employee_count(self, text: str) -> Optional[int]:
        """Extract employee count"""
        patterns = [
            r'(\d+[,\d]*)\s+employees',
            r'employee count[:\s]+(\d+[,\d]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')
                return int(count_str)
        return None

    def _extract_revenue(self, text: str) -> Optional[float]:
        """Extract revenue in USD"""
        patterns = [
            r'revenue[:\s]+\$(\d+\.?\d*)\s*(billion|million)',
            r'\$(\d+\.?\d*)\s*(billion|million) in revenue',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                unit = match.group(2).lower()
                return amount * (1e9 if unit == "billion" else 1e6)
        return None

    def _extract_funding(self, text: str) -> Optional[float]:
        """Extract funding amount in USD"""
        patterns = [
            r'raised[:\s]+\$(\d+\.?\d*)\s*(billion|million)',
            r'funding[:\s]+\$(\d+\.?\d*)\s*(billion|million)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1))
                unit = match.group(2).lower()
                return amount * (1e9 if unit == "billion" else 1e6)
        return None

    def _mock_url_data(self, url: str) -> Dict[str, Any]:
        """Return mock data for a URL"""
        domain = urlparse(url).netloc
        return {
            "url": url,
            "title": f"Information about {domain}",
            "description": f"This is mock data extracted from {url}",
            "text": "Mock content text. In a real scenario, this would contain the actual page content.",
            "word_count": 10,
            "domain": domain
        }


# Convenience function
def extract_data(url: str) -> Dict[str, Any]:
    """
    Convenience function to extract data from URL

    Args:
        url: URL to extract from

    Returns:
        Extracted data dictionary
    """
    extractor = DataExtractor()
    return extractor.extract_from_url(url)

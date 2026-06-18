"""
Nyxon Automation Suite - Web Scraper
Scrapes any URL or uses presets for news, prices, and job listings.
Saves results to text and CSV.
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from enum import Enum

from automations.base import Automation
from utils.settings import settings


class ScrapeMode(Enum):
    GENERAL  = "general"
    NEWS     = "news"
    PRICES   = "prices"
    JOBS     = "jobs"


# Presets — (label, url, mode)
PRESETS: list[tuple[str, str, ScrapeMode]] = [
    ("BBC News",         "https://www.bbc.com/news",              ScrapeMode.NEWS),
    ("CNN",              "https://edition.cnn.com",               ScrapeMode.NEWS),
    ("Hacker News",      "https://news.ycombinator.com",          ScrapeMode.NEWS),
    ("Amazon Best",      "https://www.amazon.com/best-sellers",   ScrapeMode.PRICES),
    ("Indeed Jobs",      "https://www.indeed.com/jobs?q=python",  ScrapeMode.JOBS),
    ("LinkedIn Jobs",    "https://www.linkedin.com/jobs",         ScrapeMode.JOBS),
]

OUTPUT_DIR = Path.home() / "NyxonScrapes"


class WebScraper(Automation):
    """
    Scrapes a URL and extracts content based on the selected mode.

    Attributes:
        url         : target URL
        mode        : ScrapeMode enum
        save_txt    : save output as .txt
        save_csv    : save output as .csv
        output_dir  : folder to save results (default ~/NyxonScrapes)
    """

    def __init__(self) -> None:
        super().__init__(
            name="Web Scraper",
            description="Scrape news, prices, jobs or any website and save results.",
        )
        self.url: str        = ""
        self.mode: ScrapeMode = ScrapeMode.GENERAL
        self.save_txt: bool  = True
        self.save_csv: bool  = True
        self.output_dir: Path = Path(
            settings.get("web_scraper.output_dir", str(OUTPUT_DIR))
        )
        self.results: list[dict] = []

    def run(self) -> None:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            self._emit_log("Missing libraries. Run: pip install requests beautifulsoup4")
            return

        if not self.url:
            self._emit_log("No URL set.")
            return

        self._emit_log(f"Fetching {self.url} …")
        self._set_progress(0.1)

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(self.url, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as exc:
            self._emit_log(f"Request failed: {exc}")
            return

        self._set_progress(0.4)
        soup = BeautifulSoup(resp.text, "html.parser")
        self._emit_log(f"Page loaded ({len(resp.text):,} bytes)\n")

        # Extract based on mode
        if self.mode == ScrapeMode.NEWS:
            self.results = self._extract_news(soup)
        elif self.mode == ScrapeMode.PRICES:
            self.results = self._extract_prices(soup)
        elif self.mode == ScrapeMode.JOBS:
            self.results = self._extract_jobs(soup)
        else:
            self.results = self._extract_general(soup)

        self._set_progress(0.7)

        if not self.results:
            self._emit_log("No content extracted. The site may block scrapers or use JavaScript rendering.")
            return

        self._emit_log(f"Extracted {len(self.results)} item(s):\n")
        for i, item in enumerate(self.results[:20], 1):
            line = " | ".join(str(v) for v in item.values() if v)
            self._emit_log(f"  {i:>3}. {line[:120]}")

        if len(self.results) > 20:
            self._emit_log(f"  … and {len(self.results) - 20} more")

        # Save outputs
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.output_dir / f"scrape_{self.mode.value}_{timestamp}"

        if self.save_txt:
            self._save_txt(base.with_suffix(".txt"))
        if self.save_csv:
            self._save_csv(base.with_suffix(".csv"))

        self._set_progress(1.0)
        self._emit_log(f"\nSaved to {self.output_dir}")

    # ── Extractors ────────────────────────────────────────────────────────────

    def _extract_news(self, soup) -> list[dict]:
        results = []
        # Try common headline tags
        for tag in soup.find_all(["h1", "h2", "h3"], limit=50):
            text = tag.get_text(strip=True)
            if len(text) > 20:
                link = ""
                a = tag.find("a") or tag.parent
                if hasattr(a, "get"):
                    href = a.get("href", "")
                    if href.startswith("http"):
                        link = href
                results.append({"headline": text, "link": link})
        return results

    def _extract_prices(self, soup) -> list[dict]:
        results = []
        # Look for price patterns and nearby product names
        price_pattern = re.compile(r"[\$£€₵]\s?\d+[\.,]?\d*")
        for tag in soup.find_all(True):
            text = tag.get_text(strip=True)
            if price_pattern.search(text) and 5 < len(text) < 200:
                price = price_pattern.search(text).group()
                name = text.replace(price, "").strip()[:100]
                if name:
                    results.append({"product": name, "price": price})
        # Deduplicate
        seen = set()
        unique = []
        for r in results:
            key = r["product"][:40]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique[:50]

    def _extract_jobs(self, soup) -> list[dict]:
        results = []
        # Common job listing patterns
        for tag in soup.find_all(["h2", "h3", "a"], limit=80):
            text = tag.get_text(strip=True)
            if 10 < len(text) < 120:
                keywords = ["engineer", "developer", "manager", "analyst",
                            "designer", "intern", "officer", "specialist", "consultant"]
                if any(kw in text.lower() for kw in keywords):
                    link = tag.get("href", "") if tag.name == "a" else ""
                    results.append({"title": text, "link": link})
        return results[:50]

    def _extract_general(self, soup) -> list[dict]:
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        results = []
        for tag in soup.find_all(["h1", "h2", "h3", "p"], limit=60):
            text = tag.get_text(strip=True)
            if len(text) > 30:
                results.append({"tag": tag.name, "content": text[:300]})
        return results

    # ── Output ────────────────────────────────────────────────────────────────

    def _save_txt(self, path: Path) -> None:
        try:
            with path.open("w", encoding="utf-8") as f:
                f.write(f"Nyxon Web Scraper — {self.url}\n")
                f.write(f"Mode: {self.mode.value}  |  {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                for i, item in enumerate(self.results, 1):
                    f.write(f"{i}. " + " | ".join(str(v) for v in item.values() if v) + "\n")
            self._emit_log(f"TXT saved: {path.name}")
        except OSError as exc:
            self._emit_log(f"Could not save TXT: {exc}")

    def _save_csv(self, path: Path) -> None:
        if not self.results:
            return
        try:
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
            self._emit_log(f"CSV saved: {path.name}")
        except OSError as exc:
            self._emit_log(f"Could not save CSV: {exc}")

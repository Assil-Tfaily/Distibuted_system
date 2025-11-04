import time
import csv
import logging
import re
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class LastFMScraperBS:
    def __init__(self, output_csv: str = "Bs4_Scraping.csv", base_url: str = "https://www.last.fm"):
        self.base_url = base_url
        self.output_csv = output_csv
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self.failed_urls = []

    def get_genres(self) -> List[Dict]:
        """Fetch all available genres from Last.FM."""
        logger.info("Fetching genres from Last.FM music page")
        try:
            response = self.session.get(f"{self.base_url}/music", timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            genres = []
            # Multiple possible selectors for genres
            selectors = [
                "a.music-more-tags-tag-inner-wrap",
                "a.tag",
                "a.genre-tag",
                "li.tag a"
            ]
            
            for selector in selectors:
                elems = soup.select(selector)
                if elems:
                    logger.info(f"Found {len(elems)} genre tags using selector: {selector}")
                    for e in elems:
                        href = e.get("href")
                        name = e.get_text(strip=True)
                        if href and name and len(name) > 1:
                            genres.append({"name": name, "url": href})
                    break
            
            # Fallback: look for any links that might be genres
            if not genres:
                all_links = soup.find_all("a", href=re.compile(r"/tag/"))
                for link in all_links:
                    href = link.get("href")
                    name = link.get_text(strip=True)
                    if href and name and len(name) > 1:
                        genres.append({"name": name, "url": href})
            
            logger.info(f"Total genres found: {len(genres)}")
            return genres[:20]  # Limit to 20 genres for testing
        except Exception as e:
            logger.exception(f"Error fetching genres: {e}")
            return []

    def get_tracks_from_genre(self, genre_url: str, pages: int = 1) -> List[Dict]:
        """Get track links from the genre's Tracks section."""
        tracks = []
        seen = set()

        for page in range(1, pages + 1):
            if genre_url.startswith("/"):
                genre_url = self.base_url + genre_url
            
            # Try different URL patterns
            url_patterns = [
                f"{genre_url.rstrip('/')}/tracks?page={page}",
                f"{genre_url.rstrip('/')}/+tracks?page={page}",
                f"{self.base_url}/tag/{genre_url.split('/')[-1]}/tracks?page={page}"
            ]
            
            for page_url in url_patterns:
                logger.info(f"Trying URL pattern: {page_url}")
                try:
                    response = self.session.get(page_url, timeout=10)
                    if response.status_code == 200:
                        break
                except:
                    continue
            else:
                logger.warning(f"All URL patterns failed for genre: {genre_url}")
                continue
            
            try:
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Multiple selectors for track links
                track_selectors = [
                    "a[href*='/_/']",
                    "tr.chartlist-row a",
                    ".chartlist-name a",
                    ".track-list .track a"
                ]
                
                for selector in track_selectors:
                    anchor_elems = soup.select(selector)
                    if anchor_elems:
                        logger.info(f"Found {len(anchor_elems)} track candidates using selector: {selector}")
                        break
                else:
                    anchor_elems = soup.find_all("a", href=re.compile(r"/_/"))
                
                for a in anchor_elems:
                    try:
                        href = a.get("href") or ""
                        if "/_/" not in href:
                            continue
                        
                        name = a.get_text(strip=True)
                        name = re.sub(r"\s+", " ", name).strip()
                        
                        if not name or len(name) < 2:
                            continue
                        
                        # Make URL absolute
                        if href.startswith("/"):
                            href = self.base_url + href
                        
                        if href not in seen:
                            seen.add(href)
                            tracks.append({"name": name, "url": href})
                    except Exception:
                        continue
                
                logger.info(f"Page {page}: {len(tracks)} unique tracks so far")
                time.sleep(random.uniform(1, 2))  # Random delay
                
            except Exception as e:
                logger.exception(f"Error loading page {page}: {e}")
                continue
        
        return tracks

    def extract_track_details(self, track_url: str, genre_name: str) -> Dict:
        """Extract detailed info about a track with robust error handling."""
        logger.info(f"Extracting details from {track_url}")
        
        data = {
            "genre": genre_name,
            "track_url": track_url,
            "track_name": "N/A",
            "artist_name": "N/A",
            "album": "N/A",
            "duration": "N/A",
            "listeners": "N/A",
            "playcount": "N/A",
            "raw_html": "N/A",
            "scraping_status": "success"
        }
        
        try:
            response = self.session.get(track_url, timeout=15)
            
            # Handle 502 and other errors gracefully
            if response.status_code == 502:
                data["scraping_status"] = "502_error"
                logger.warning(f"502 Bad Gateway for {track_url}")
                return data
            elif response.status_code != 200:
                data["scraping_status"] = f"http_{response.status_code}"
                logger.warning(f"HTTP {response.status_code} for {track_url}")
                return data
            
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Store raw HTML (limited length to avoid huge files)
            data["raw_html"] = str(soup)[:5000]  # First 5000 chars
            
            # Track name - multiple selectors
            track_name_selectors = [
                "h1.header-new-title",
                "h1.track-header-title",
                "h1",
                ".track-header h1"
            ]
            
            for selector in track_name_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    data["track_name"] = elem.get_text(strip=True)
                    break
            
            # Artist name - multiple selectors
            artist_selectors = [
                'span[itemprop="byArtist"] [itemprop="name"]',
                "h2 a",
                ".artist-name a",
                ".header-new-description a"
            ]
            
            for selector in artist_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    data["artist_name"] = elem.get_text(strip=True)
                    break
            
            # Album - multiple selectors
            album_selectors = [
                "h4.source-album-name a",
                ".album-name a",
                ".track-album a"
            ]
            
            for selector in album_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    data["album"] = elem.get_text(strip=True)
                    break
            
            # Duration
            duration_patterns = [
                r"\b(\d{1,2}:\d{2})\b",
                r"Duration:\s*(\d{1,2}:\d{2})",
                r"Length:\s*(\d{1,2}:\d{2})"
            ]
            
            page_text = soup.get_text()
            for pattern in duration_patterns:
                match = re.search(pattern, page_text)
                if match:
                    data["duration"] = match.group(1)
                    break
            
            # Listeners and Playcount
            stats_selectors = [
                "abbr[title]",
                ".chart-details .chart-count",
                ".track-stats .stat"
            ]
            
            stats_values = []
            for selector in stats_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    title = elem.get("title", "").strip()
                    if title and re.match(r"^[\d,]+$", title.replace(" ", "").replace(",", "")):
                        stats_values.append(title)
                    # Also check text content
                    text = elem.get_text(strip=True)
                    if text and re.match(r"^[\d,]+$", text.replace(" ", "").replace(",", "")):
                        stats_values.append(text)
            
            if len(stats_values) >= 1:
                data["listeners"] = stats_values[0]
            if len(stats_values) >= 2:
                data["playcount"] = stats_values[1]
            
            # Validate we got at least some useful data
            if data["track_name"] != "N/A" and data["artist_name"] != "N/A":
                logger.info(f"Successfully extracted: {data['track_name']} - {data['artist_name']}")
            else:
                data["scraping_status"] = "partial_data"
                logger.warning(f"Partial data for {track_url}")
            
        except requests.exceptions.RequestException as e:
            data["scraping_status"] = "request_error"
            logger.error(f"Request error for {track_url}: {e}")
            self.failed_urls.append(track_url)
        except Exception as e:
            data["scraping_status"] = "parsing_error"
            logger.exception(f"Error parsing {track_url}: {e}")
            self.failed_urls.append(track_url)
        
        return data

    def save_to_csv(self, data: List[Dict]):
        if not data:
            logger.info("No data to save.")
            return
        
        keys = ["genre", "track_name", "artist_name", "album", "duration", "listeners", "playcount", "track_url", "raw_html", "scraping_status"]
        
        with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Saved {len(data)} rows to {self.output_csv}")
    def run(self, genre_names: List[str] = None, max_tracks_per_genre=None, pages: int = 1):
        """Run the scraper with improved error handling."""
        all_tracks = []
        try:
            genres = self.get_genres()
            
            if genre_names:
                genres = [g for g in genres if g["name"].lower() in [x.lower() for x in genre_names]]
                logger.info(f"Filtered to {len(genres)} genres: {[g['name'] for g in genres]}")
            
            for g in genres:
                logger.info(f"Processing genre: {g['name']}")
                tracks = self.get_tracks_from_genre(g["url"], pages=pages)
                
                if max_tracks_per_genre:
                    tracks = tracks[:max_tracks_per_genre]
                
                logger.info(f"Extracting details for {len(tracks)} tracks in {g['name']}")
                successful_in_genre = 0
                
                for i, t in enumerate(tracks):
                    try:
                        details = self.extract_track_details(t["url"], g["name"])
                        all_tracks.append(details)
                        
                        if details.get("scraping_status") == "success":
                            successful_in_genre += 1
                        
                        # Progress reporting
                        if (i + 1) % 10 == 0:
                            logger.info(f"Progress in {g['name']}: {i+1}/{len(tracks)}")
                        
                        # Variable delay with jitter
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.exception(f"Failed to extract: {t.get('url')}")
                        continue
                
                logger.info(f"Genre {g['name']}: {successful_in_genre}/{len(tracks)} successful")
        
        except Exception as e:
            logger.exception(f"Fatal error in scraper run: {e}")
        
        finally:
            self.save_to_csv(all_tracks)
            logger.info("Scraping completed!")


# Simple test function
def test_scraper():
    """Test the scraper with a small sample."""
    scraper = LastFMScraperBS(output_csv="test_scraping_results.csv")
    scraper.run(
        genre_names=["Rock", "Jazz"],  # Just 2 genres for testing
        max_tracks_per_genre=5,        # Just 5 tracks per genre
        pages=1
    )

if __name__ == "__main__":
    test_scraper()
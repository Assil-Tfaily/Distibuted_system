import ray
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict
import logging

@ray.remote
class LastFMScraperWorker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.base_url = "https://www.last.fm"
    
    def scrape_genre_tracks(self, genre_data: Dict, max_tracks: int = 50, pages: int = 2) -> List[Dict]:
        """Scrape tracks from a specific genre"""
        genre_name = genre_data['name']
        genre_url = genre_data['url']
        
        if genre_url.startswith("/"):
            genre_url = self.base_url + genre_url
        
        all_tracks = []
        
        for page in range(1, pages + 1):
            try:
                page_url = f"{genre_url.rstrip('/')}/tracks?page={page}"
                response = self.session.get(page_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "html.parser")
                track_links = soup.find_all("a", href=re.compile(r"/_/"))
                
                for link in track_links[:max_tracks]:
                    track_url = link.get("href")
                    if track_url and track_url.startswith("/"):
                        track_url = self.base_url + track_url
                    
                    track_name = link.get_text(strip=True)
                    track_name = re.sub(r"\s+", " ", track_name).strip()
                    
                    if track_name and len(track_name) > 1:
                        all_tracks.append({
                            "name": track_name,
                            "url": track_url,
                            "genre": genre_name
                        })
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                logging.error(f"Error scraping genre {genre_name} page {page}: {e}")
                continue
        
        return all_tracks
    
    def scrape_track_details(self, track_data: Dict) -> Dict:
        """Scrape detailed information for a single track"""
        try:
            response = self.session.get(track_data['url'], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Track name
            h1 = soup.find("h1")
            track_name = h1.get_text(strip=True) if h1 else track_data['name']
            
            # Artist name
            artist_name = "N/A"
            artist_span = soup.find("span", {"itemprop": "byArtist"})
            if artist_span:
                name_elem = artist_span.find(attrs={"itemprop": "name"})
                if name_elem:
                    artist_name = name_elem.get_text(strip=True)
            else:
                h2 = soup.find("h2")
                if h2:
                    artist_link = h2.find("a")
                    if artist_link:
                        artist_name = artist_link.get_text(strip=True)
            
            # Album
            album = "N/A"
            album_h4 = soup.find("h4", class_="source-album-name")
            if album_h4:
                album_link = album_h4.find("a")
                if album_link:
                    album = album_link.get_text(strip=True)
            
            # Duration
            duration = "N/A"
            dd_elems = soup.find_all("dd", class_="catalogue-metadata-description")
            for dd in dd_elems:
                text = dd.get_text(strip=True)
                match = re.search(r"\b\d{1,2}:\d{2}\b", text)
                if match:
                    duration = match.group(0)
                    break
            
            # Listeners and Playcount
            listeners = "N/A"
            playcount = "N/A"
            all_abbrs = soup.find_all("abbr", {"title": True})
            values = []
            for abbr in all_abbrs:
                title = abbr.get("title") or ""
                title = title.strip()
                if title and re.match(r"^[\d,]+$", title.replace(" ", "")):
                    values.append(title)
            
            if len(values) >= 1:
                listeners = values[0]
            if len(values) >= 2:
                playcount = values[1]
            
            return {
                "genre": track_data['genre'],
                "track_name": track_name,
                "artist_name": artist_name,
                "album": album,
                "duration": duration,
                "listeners": listeners,
                "playcount": playcount,
                "track_url": track_data['url'],
                "scraped_at": time.time(),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"Error scraping track {track_data['url']}: {e}")
            return {
                "genre": track_data['genre'],
                "track_name": track_data['name'],
                "track_url": track_data['url'],
                "status": "error",
                "error": str(e)
            }

class DistributedLastFMScraper:
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.workers = [LastFMScraperWorker.remote() for _ in range(num_workers)]
        self.base_url = "https://www.last.fm"
    
    def get_genres(self, target_genres: List[str] = None) -> List[Dict]:
        """Get available genres from LastFM"""
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            response = session.get(f"{self.base_url}/music")
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            
            genres = []
            elems = soup.find_all("a", class_="music-more-tags-tag-inner-wrap")
            
            for e in elems:
                href = e.get("href")
                name = e.get_text(strip=True)
                if href and name:
                    if target_genres is None or name.lower() in [g.lower() for g in target_genres]:
                        genres.append({"name": name, "url": href})
            
            return genres
            
        except Exception as e:
            logging.error(f"Error fetching genres: {e}")
            return []
    
    def scrape_music_data(self, genres: List[str] = None, max_tracks_per_genre: int = 50, pages_per_genre: int = 2) -> List[Dict]:
        """Main method to scrape music data distributed across workers"""
        # Get genres to scrape
        target_genres = self.get_genres(genres)
        logging.info(f"Found {len(target_genres)} genres to scrape")
        
        # Distribute genre scraping across workers
        genre_batches = self._distribute_work(target_genres, self.num_workers)
        
        # Scrape tracks from each genre (distributed)
        track_scraping_tasks = []
        for i, genre_batch in enumerate(genre_batches):
            if genre_batch:  # Only assign work if there are genres in this batch
                worker = self.workers[i % self.num_workers]
                track_scraping_tasks.append(
                    worker.scrape_genre_tracks.remote(genre_batch, max_tracks_per_genre, pages_per_genre)
                )
        
        # Collect all tracks
        all_tracks = []
        track_results = ray.get(track_scraping_tasks)
        for track_list in track_results:
            all_tracks.extend(track_list)
        
        logging.info(f"Found {len(all_tracks)} total tracks")
        
        # Distribute track detail scraping across workers
        detail_tasks = []
        for i, track in enumerate(all_tracks):
            worker = self.workers[i % self.num_workers]
            detail_tasks.append(worker.scrape_track_details.remote(track))
        
        # Collect results with progress
        results = []
        for i, task in enumerate(detail_tasks):
            result = ray.get(task)
            results.append(result)
            if (i + 1) % 10 == 0:
                logging.info(f"Processed {i + 1}/{len(detail_tasks)} tracks")
        
        return results
    
    def _distribute_work(self, items: List, num_workers: int) -> List[List]:
        """Distribute items evenly across workers"""
        batches = [[] for _ in range(num_workers)]
        for i, item in enumerate(items):
            batches[i % num_workers].append(item)
        return batches
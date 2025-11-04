import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
import re
from typing import List, Dict
import time

class LastFMSpider(scrapy.Spider):
    name = "lastfm"
    
    def __init__(self, genres=None, max_tracks_per_genre=50, pages=2, *args, **kwargs):
        super(LastFMSpider, self).__init__(*args, **kwargs)
        self.base_url = "https://www.last.fm"
        self.genres = genres or ["Rock", "Jazz", "Hip-Hop", "Indie", "80s", "Dance", "Classical"]
        self.max_tracks_per_genre = max_tracks_per_genre
        self.pages = pages
        self.start_urls = [f"{self.base_url}/music"]
        self.scraped_data = []
    
    def parse(self, response):
        """Parse the main music page to get genre URLs"""
        # Extract genre links
        genre_links = response.css('a.music-more-tags-tag-inner-wrap::attr(href)').getall()
        genre_names = response.css('a.music-more-tags-tag-inner-wrap::text').getall()
        
        genres = []
        for name, link in zip(genre_names, genre_links):
            name = name.strip()
            if name and name.lower() in [g.lower() for g in self.genres]:
                genres.append({"name": name, "url": link})
        
        # Follow genre links
        for genre in genres:
            for page in range(1, self.pages + 1):
                genre_tracks_url = f"{self.base_url}{genre['url']}/tracks?page={page}"
                yield scrapy.Request(
                    genre_tracks_url,
                    callback=self.parse_genre_tracks,
                    meta={'genre': genre['name']}
                )
    
    def parse_genre_tracks(self, response):
        """Parse genre tracks page to get track URLs"""
        genre = response.meta['genre']
        track_links = response.css('a[href*="/_/"]::attr(href)').getall()
        
        for track_link in track_links[:self.max_tracks_per_genre]:
            track_url = f"{self.base_url}{track_link}"
            yield scrapy.Request(
                track_url,
                callback=self.parse_track_details,
                meta={'genre': genre}
            )
    
    def parse_track_details(self, response):
        """Parse individual track page for details"""
        genre = response.meta['genre']
        
        # Extract track name
        track_name = response.css('h1::text').get(default='N/A').strip()
        
        # Extract artist name
        artist_name = 'N/A'
        artist_elem = response.css('span[itemprop="byArtist"] [itemprop="name"]::text').get()
        if artist_elem:
            artist_name = artist_elem.strip()
        else:
            artist_elem = response.css('h2 a::text').get()
            if artist_elem:
                artist_name = artist_elem.strip()
        
        # Extract album
        album = 'N/A'
        album_elem = response.css('h4.source-album-name a::text').get()
        if album_elem:
            album = album_elem.strip()
        
        # Extract duration
        duration = 'N/A'
        duration_text = response.css('dd.catalogue-metadata-description::text').get()
        if duration_text:
            match = re.search(r'\b\d{1,2}:\d{2}\b', duration_text)
            if match:
                duration = match.group(0)
        
        # Extract listeners and playcount
        listeners = 'N/A'
        playcount = 'N/A'
        stats = response.css('abbr[title]::attr(title)').getall()
        numeric_stats = [s.replace(' ', '').replace(',', '') for s in stats if s.replace(' ', '').replace(',', '').isdigit()]
        
        if len(numeric_stats) >= 1:
            listeners = numeric_stats[0]
        if len(numeric_stats) >= 2:
            playcount = numeric_stats[1]
        
        track_data = {
            'genre': genre,
            'track_name': track_name,
            'artist_name': artist_name,
            'album': album,
            'duration': duration,
            'listeners': listeners,
            'playcount': playcount,
            'track_url': response.url,
            'scraped_at': time.time()
        }
        
        self.scraped_data.append(track_data)
        yield track_data

def run_scrapy_spider(genres=None, max_tracks_per_genre=50, pages=2):
    """Run Scrapy spider and return collected data"""
    process = CrawlerProcess(get_project_settings())
    spider = LastFMSpider(genres=genres, max_tracks_per_genre=max_tracks_per_genre, pages=pages)
    
    def collect_results():
        return spider.scraped_data
    
    process.crawl(spider)
    process.start()
    return spider.scraped_data
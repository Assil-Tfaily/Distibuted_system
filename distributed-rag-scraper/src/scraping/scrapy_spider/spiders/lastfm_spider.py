import scrapy
from typing import Dict, List
import re

class LastFMSpider(scrapy.Spider):
    name = "lastfm"
    allowed_domains = ["last.fm"]
    start_urls = ["https://www.last.fm/music"]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1,
        'AUTOTHROTTLE_ENABLED': True,
    }

    def parse(self, response):
        """Parse the main music page to get genres."""
        genre_links = response.css('a.music-more-tags-tag-inner-wrap')
        
        for link in genre_links:
            genre_name = link.css('::text').get().strip()
            genre_url = link.attrib['href']
            
            if genre_url.startswith('/'):
                genre_url = response.urljoin(genre_url)
            
            yield scrapy.Request(
                url=genre_url + '/tracks',
                callback=self.parse_genre_tracks,
                meta={'genre': genre_name, 'genre_url': genre_url}
            )

    def parse_genre_tracks(self, response):
        """Parse genre tracks page."""
        genre = response.meta['genre']
        
        # Extract track links
        track_links = response.css('a[href*="/_/"]')
        
        for link in track_links:
            track_url = link.attrib['href']
            track_name = link.css('::text').get()
            
            if track_url and track_name and len(track_name.strip()) > 1:
                if track_url.startswith('/'):
                    track_url = response.urljoin(track_url)
                
                yield scrapy.Request(
                    url=track_url,
                    callback=self.parse_track_details,
                    meta={'genre': genre, 'track_name': track_name.strip()}
                )
        
        # Pagination
        next_page = response.css('a.pagination-next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse_genre_tracks,
                meta=response.meta
            )

    def parse_track_details(self, response):
        """Parse individual track details."""
        genre = response.meta['genre']
        track_name = response.meta['track_name']
        
        # Extract track details
        artist_name = response.css('span[itemprop="byArtist"] [itemprop="name"]::text').get()
        if not artist_name:
            artist_name = response.css('h2 a::text').get()
        
        album = response.css('h4.source-album-name a::text').get()
        
        # Duration
        duration_text = ' '.join(response.css('dd.catalogue-metadata-description::text').getall())
        duration_match = re.search(r'\b\d{1,2}:\d{2}\b', duration_text)
        duration = duration_match.group(0) if duration_match else 'N/A'
        
        # Listeners and playcount
        metrics = response.css('abbr[title]::attr(title)').getall()
        listeners = metrics[0] if len(metrics) > 0 else 'N/A'
        playcount = metrics[1] if len(metrics) > 1 else 'N/A'
        
        yield {
            'genre': genre,
            'track_name': track_name,
            'artist_name': artist_name or 'N/A',
            'album': album or 'N/A',
            'duration': duration,
            'listeners': listeners,
            'playcount': playcount,
            'track_url': response.url,
            'raw_html': response.text
        }
import scrapy

class TrackItem(scrapy.Item):
    genre = scrapy.Field()
    track_name = scrapy.Field()
    artist_name = scrapy.Field()
    album = scrapy.Field()
    duration = scrapy.Field()
    listeners = scrapy.Field()
    playcount = scrapy.Field()
    track_url = scrapy.Field()
    raw_html = scrapy.Field()
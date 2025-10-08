# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class MacbookScraperItem(scrapy.Item):
    # define the fields for your item here like:
    model = scrapy.Field()
    configuration = scrapy.Field()
    price_vnd = scrapy.Field()
    shop_name = scrapy.Field()
    url = scrapy.Field()
    scraped_at = scrapy.Field()

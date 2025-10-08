import scrapy
import json
import os
from ..items import MacbookScraperItem

class ShopdunkSpider(scrapy.Spider):
    name = "shopdunk"
    allowed_domains = ["shopdunk.com"]
    start_urls = ["https://shopdunk.com/mac"]

    def __init__(self, *args, **kwargs):
        super(ShopdunkSpider, self).__init__(*args, **kwargs)
        selectors_path = os.path.join(os.path.dirname(__file__), '../selectors.json')
        with open(selectors_path, 'r') as f:
            self.selectors = json.load(f)['shopdunk']

    def parse(self, response):
        # Save the HTML for debugging
        with open('shopdunk.html', 'wb') as f:
            f.write(response.body)
        self.log('Saved shopdunk.html')

        product_cards = response.css(self.selectors['product_container'])
        for card in product_cards:
            item = MacbookScraperItem()
            item['model'] = card.css(self.selectors['model'] + '::text').get()
            item['price_vnd'] = card.css(self.selectors['price'] + '::text').get()
            item['configuration'] = card.css(self.selectors['configuration'] + '::text').get()
            item['shop_name'] = self.name
            item['url'] = response.urljoin(card.css('a::attr(href)').get())
            item['scraped_at'] = __import__('time').strftime('%Y-%m-%d %H:%M:%S')
            yield item

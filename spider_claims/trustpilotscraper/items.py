# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TrustpilotscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class CompanyItem(scrapy.Item):
    url = scrapy.Field()
    company_name = scrapy.Field()
    company_mail_address = scrapy.Field()
    company_geo_location = scrapy.Field()
    company_image_source = scrapy.Field()
    company_category = scrapy.Field()
    company_trustpilot_rating = scrapy.Field()
    verified = scrapy.Field()
    number_of_reviews = scrapy.Field()
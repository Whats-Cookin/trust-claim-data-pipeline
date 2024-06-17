# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrowdsupplyItem(scrapy.Item):
    project_url = scrapy.Field()
    team_name = scrapy.Field()
    date_funded = scrapy.Field()
    raised_amount = scrapy.Field()
    goal_amount = scrapy.Field()
    project_name = scrapy.Field()
    project_description = scrapy.Field()

    
    backers_url = scrapy.Field()
    backers = scrapy.Field()
    number_of_backers = scrapy.Field()

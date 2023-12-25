from scraper.main import OpenCorperate
# from scraper.scrape_urls import *
import time

with OpenCorperate(teardown=True) as bot:
    bot.land_on_home_page()
    bot.search_var('a')
    bot.move_to_each_page()
    bot.get_infos()
    time.sleep(20)

# with GetCompUrls as bot:
#     bot.get_urls()

# get_urls()
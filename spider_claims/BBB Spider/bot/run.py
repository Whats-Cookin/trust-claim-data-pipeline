from scraper.main import BBB
import time

with BBB(teardown=True) as bot:
    bot.land_on_home_page()
    bot.by_pass_pop_up()
    bot.search_categories(category="Roofing Contractors", place="London, CA")
    bot.select_show_all_business()
    bot.scrape()
    time.sleep(20)

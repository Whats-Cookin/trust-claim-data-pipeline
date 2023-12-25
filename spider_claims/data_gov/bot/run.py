from scraper.scrape import DataGov
import time

with DataGov(teardown=True) as bot:
    bot.land_on_dataset_page()
    bot.apply_filtrations()
    # bot.download('CSV')
    bot.pagination()
    # bot.run_script()
    time.sleep(20)
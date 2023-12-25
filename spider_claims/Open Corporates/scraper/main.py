from scraper.constants import BASE_URL,DRIVER_PATH
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
# from scraper.dataset_format_filtration import DatasetFormatFiltration
# from scraper.pagination import Pagination
# from scraper.scrape_urls import GetCompUrls
from scraper.scrape import ScrapeIt
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class OpenCorperate(webdriver.Chrome):
    def __init__(self, driver_path=DRIVER_PATH, teardown=False):
        self.driver_path = driver_path
        self.teardown = teardown
        os.environ['PATH'] += self.driver_path
        super(OpenCorperate, self).__init__()
        self.implicitly_wait(15)
        self.maximize_window()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()

    def land_on_home_page(self):
        self.get(BASE_URL)

    def search_var(self, value):
        wait = WebDriverWait(self, 20)
        var = wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, 'oc-home-search_input'
        )))
        var.send_keys(value)
        search_btn = self.find_element(
            By.CLASS_NAME, 'oc-home-search_button'
        )
        search_btn.click()

    # def urls(self):
    #     all_urls = GetCompUrls
    #     all_urls.get_urls()

    def move_to_each_page(self):
        comp = self.find_element(
            By.XPATH, '//*[@id="companies"]/li[1]/a[2]'
        )
        comp.click()
        # self.back()

    def scrape_page(self):

        pass
    def get_infos(self):
        infos = ScrapeIt(driver=self)
        infos.get_info()
# //*[@id="companies"]/li[1]/a[2]
# //*[@id="companies"]/li[2]/a[2]
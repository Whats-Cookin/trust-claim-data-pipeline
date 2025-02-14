from scraper.constants import BASE_URL, DRIVER_PATH
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from scraper.dataset_format_filtration import DatasetFormatFiltration
from scraper.pagination import Pagination
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class DataGov(webdriver.Chrome):
    def __init__(self, driver_path=DRIVER_PATH, teardown=False):
        self.driver_path = driver_path
        self.teardown = teardown
        os.environ["PATH"] += self.driver_path
        super(DataGov, self).__init__()
        self.implicitly_wait(15)
        self.maximize_window()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.teardown:
            self.quit()

    def land_on_dataset_page(self):
        self.get(BASE_URL)

    def search_var(self, value):
        var = self.find_element(By.ID, "search-big")
        var.send_keys(value)
        btn = self.find_element(By.ID, 'button[value="search"]')
        btn.click()

    def apply_filtrations(self):
        filtration = DatasetFormatFiltration(driver=self)
        filtration.format("CSV")

    def pagination(self):
        action = Pagination(driver=self)
        action.next_page()

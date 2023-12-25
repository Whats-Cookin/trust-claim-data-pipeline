from scraper.constants import BASE_URL,DRIVER_PATH
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.scrape import ScrapeIt

class BBB(webdriver.Chrome):
    def __init__(self, driver_path=DRIVER_PATH, teardown=False):
        self.driver_path = driver_path
        self.teardown = teardown
        os.environ['PATH'] += self.driver_path
        super(BBB, self).__init__()
        self.implicitly_wait(15)
        self.maximize_window()

    def __exit__(self, exc_type, exc, traceback):
        if self.teardown:
            self.quit()

    def land_on_home_page(self):
        self.get(BASE_URL)

    def by_pass_pop_up(self):
        wait = WebDriverWait(self, 20)
        
        btn = wait.until(EC.presence_of_element_located((
            By.XPATH, '/html/body/div[3]/div[3]/div/div/div/div/div[1]/button'
        )))
           
        btn.click()
        
    def search_categories(self, category, place):
        
        wait = WebDriverWait(self, 20)
        cat_var = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input[name="find_text"]'
        )))
        place_var = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'input[name="find_loc"]'
        )))
        search_btn = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'button[data-type="search"]'
        )))

        cat_var.send_keys(category)
        place_var.send_keys(place)
        search_btn.click()

    def select_show_all_business(self):
        wait = WebDriverWait(self, 20)
        radio_ele = wait.until(EC.presence_of_element_located((
            By.ID, ':r1:'
        )))
        btn = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'button[aria-describedby="caption-desc-id"]'
        )))
        radio_ele.click()
        btn.click()

    def scrape(self):
        scraper=ScrapeIt(driver=self)
        scraper.engine()

# categories to search
    # Roofing Contractors
    # Home Improvement
    # Auto Repair
    # General Contractor
    # Charity - Local
    # Construction Services
    # Home Builders
    # Heating and Air Conditioning
    # Used Car Dealers
    # Tree Service
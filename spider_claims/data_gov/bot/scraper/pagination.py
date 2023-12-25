# This file will includes a class with instance methods
# That moves from one page of organisation list to anotger until all pages is exhuasted

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Pagination:
    def __init__(self, driver:WebDriver):
        self.driver = driver

    def next_page(self):
        x=6
        self.get_file('CSV')
        li_btn = self.driver.find_element(
            By.XPATH, f'//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[{x}]/a'
        )
        li_btn.click()

        self.get_file('CSV')
        li_btn = self.driver.find_element(
            By.XPATH, f'//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[{x+2}]/a'
        )
        li_btn.click()

        self.get_file('CSV')
        li_btn = self.driver.find_element(
            By.XPATH, f'//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[{x+3}]/a'
        )
        li_btn.click()

        self.get_file('CSV')
        li_btn = self.driver.find_element(
            By.XPATH, f'//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[{x+4}]/a'
        )
        li_btn.click()

        self.get_file('CSV')
        li_btn = self.driver.find_element(
            By.XPATH, f'//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[{x+5}]/a'
        )
        li_btn.click()

        for num in range(12710):
            self.get_file('CSV')
            li_btn = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div[2]/div/section[1]/div[3]/ul/li[11]/a'
            )
            li_btn.click()

        return False
    
    def get_file(self,data_format):
        wait = WebDriverWait(self, 10)
        org_list = self.driver.find_element(
            By.CLASS_NAME, 'dataset-list'
        )
        datasets = org_list.find_elements(
            By.CSS_SELECTOR, '*'
        )
        
        for dataset in datasets:
            try:
                if str(dataset.get_attribute('innerHTML')).strip() == f'{data_format}':
                    # dataset.click()
                    print("done")
            except:
                wait.until(EC.staleness_of(dataset))
                dataset = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dataset-resources *')))
                if str(dataset.get_attribute('innerHTML')).strip() == f'{data_format}':
                    # dataset.click()
                    print("done")
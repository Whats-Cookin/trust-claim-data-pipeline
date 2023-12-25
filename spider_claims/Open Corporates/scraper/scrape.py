
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ScrapeIt:
    def __init__(self, driver:WebDriver):
        self.driver = driver

    def get_info(self):
        company_name = ''
        company_number = ''
        status = ''
        incoporation_date = ''
        desolution_date = ''
        company_type = ''
        jurisdiction = ''
        registered_address = ''
        registry_page = ''
        industry_code =''
        previous_name = ''
        alternate_names = ''
        source = ''
        company_address = ''
        company_website = ''
        company_phone = ''
        code_scheme = ''
        description = ''
        identifier_system = ''
        identifier = ''
        category = ''
        confidence = ''

        company_name_element = self.driver.find_element(
            By.CSS_SELECTOR, 'h1[itemprop="name"]'
        )
        company_number_element = self.driver.find_element(
            By.CLASS_NAME, 'company_number'
        )
        status_element = self.driver.find_element(
            By.CLASS_NAME, 'status'
        )
        incoporation_date_element = self.driver.find_element(
            By.CLASS_NAME, 'incorporation_date'
        )
        company_type_element = self.driver.find_element(
            By.CLASS_NAME, 'company_type'
        )
        jurisdiction_element = self.driver.find_element(
            By.CLASS_NAME, 'jurisdiction'
        )
        registered_address_element = self.driver.find_elements(
            By.CLASS_NAME, 'address_line'
        )
        registry_page_element = self.driver.find_element(
            By.CLASS_NAME, 'registry_page *'
        )
        
        identifier_element = self.driver.find_elements(
            By.CLASS_NAME, 'table-wrapper'
        )

        print(company_name_element.text)
        print(company_number_element.text)
        print(status_element.text)
        print(incoporation_date_element.text)
        print(company_type_element.text)
        print(jurisdiction_element.text)
        for ele in registered_address_element:
            print(ele.text)
        print(registry_page_element.get_attribute('href')) 
        for i in identifier_element:
            print(i.text)

        next_page = self.driver.find_element(
            By.XPATH, '//*[@id="data-table-identifier_delegate"]/div/table/tbody/tr/td[5]/a'
        )
        next_page.click()
        source_element = self.driver.find_element(
            By.CLASS_NAME, 'source *'
        )
        print(source_element.get_attribute('href'))
        confidence_element = self.driver.find_element(
            By.CLASS_NAME, 'confidence'
        )
        print(confidence_element.text)
        self.driver.back()
        self.driver.back()
        
        # print(identifier_element)
        

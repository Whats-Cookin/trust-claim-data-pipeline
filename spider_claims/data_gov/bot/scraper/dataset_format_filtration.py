# This file will includes a class with instance methods
# That will filter the dataset we are to get
# After we have some results, to apply_filtration methon in scrape.py

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DatasetFormatFiltration:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def format(self, data_format):
        wait = WebDriverWait(self.driver, 10)
        data_formats_box = self.driver.find_element(
            By.CSS_SELECTOR, 'nav[aria-label="Formats"]'
        )

        data_formats_child_element = data_formats_box.find_elements(
            By.CSS_SELECTOR, "*"
        )

        for format_type in data_formats_child_element:
            try:
                if (
                    str(format_type.get_attribute("innerHTML")).strip()
                    == f"{data_format}"
                ):
                    format_type.click()
            except:
                wait.until(EC.staleness_of(format_type))
                format_type = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'nav[aria-label="Formats"] *')
                    )
                )
                if (
                    str(format_type.get_attribute("innerHTML")).strip()
                    == f"{data_format}"
                ):
                    format_type.click()

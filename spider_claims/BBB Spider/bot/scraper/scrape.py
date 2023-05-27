
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import re
# from scraper.constants import category

class ScrapeIt:
    def __init__(self, driver:WebDriver):
        self.driver = driver
        self.file = open('bbb.csv', 'a')
        self.writer = csv.writer(self.file)
    
    def click_on_entity(self, COMP_PATH):
        try:
            comp_btn = self.driver.find_element(
                By.XPATH, COMP_PATH
            )
            comp_btn.click()
        except:
            print('error in clicking')
    def get_info(self):
        try:
            comp_name_ele = self.driver.find_element(
                By.CLASS_NAME, 'bds-h2'
            )
        except:
            pass
        try:
            category_ele = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div[1]/div/header/div/div[2]/div[1]'
            )
        except:
            category_ele = 'Roofing Contractor'
        
        try:
            comp_address_ele = self.driver.find_element(
                By.TAG_NAME, 'address'
            )
            comp_phone_ele = self.driver.find_element(
                By.CLASS_NAME, 'dtm-phone'
            )
        except:
            comp_address_ele = 'NIL'
            comp_phone_ele = 'NIL'
        try:
            bbb_rating_ele = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div[2]/div/div[2]/div/div[4]/div/div/div[1]/div[1]/a/span/span[1]'
            )
        except:
            bbb_rating_ele = 'NR'
        
        url = self.driver.find_element(
            By.XPATH, '//*[@id="content"]/div[2]/div/div[2]/div/div[3]/div/div[1]/div/div/div[1]/a'
        ).get_attribute('href')
        try:
            year_in_business_ele = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div[2]/div/div[2]/div/div[4]/div/div/div[1]/div[2]/p[2]'
            )
            accredicted_since_ele = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div[2]/div/div[2]/div/div[4]/div/div/div[1]/div[2]/p[1]'
            )
            year_in_business = year_in_business_ele.text
            accredicted_since = accredicted_since_ele.text
            accredicted = 'YES'
        except:
            year_in_business_ele = 'NIL'
            accredicted_since_ele = 'NIL'
            year_in_business = year_in_business_ele
            accredicted_since = accredicted_since_ele
            accredicted = 'NO'

        try:
            comp_name =  comp_name_ele.text
        except:
            comp_name = 'NIL'
        try:
            category = category_ele.text
        except:
            category = 'Roofing Contractor'
        try:
            comp_address = comp_address_ele.text
            comp_phone = comp_phone_ele.text
        except:
            comp_address = 'NIL'
            comp_phone = 'NIL'
        try:
            bbb_rating = bbb_rating_ele.text
        except:
            bbb_rating = bbb_rating_ele
        index = url.index("/customer-reviews")
        source = url[:index]

        bbb_rating_range = {
            'A+': '97 - 100',
            'A': '94 - 96.99',
            'A-': '90 - 93.99',
            'B+': '87 - 89.99',
            'B': '84 - 86.99',
            'B-': '80 - 83.99',
            'C+': '77 - 79.99',
            'C': '74 - 76.99',
            'C-': '70 - 73.99',
            'D+': '67 - 69.99',
            'D': '64 - 66.99',
            'D-': '60 - 63.99',
            'F': '0 - 59.99',
            'NR': 'Not Rated'
        }

        company_rating_ave = {
            'A+': '98.5',
            'A': '95.5',
            'A-': '92.0',
            'B+': '88.5',
            'B': '85.5',
            'B-': '82.0',
            'C+': '78.5',
            'C': '75.5',
            'C-': '72.0',
            'D+': '68.5',
            'D': '65.5',
            'D-': '62.0',
            'F': '58.5',
            'NR': 'NIL'
        }

        bbb_rating = str(bbb_rating)
        bbb_rating_range = bbb_rating_range.get(bbb_rating, 'NIL')
        company_rating_ave = company_rating_ave.get(bbb_rating, 'NIL')
        try:
            year_in_business = year_in_business.split(':')[1].strip()
            accredicted_since = accredicted_since.split(':')[1].strip()
        except:
            year_in_business = year_in_business
            accredicted_since = accredicted_since
        print('Company Name: ', comp_name)
        print('Category: ', category)
        print('Company Address: ', comp_address)
        print('Company Phone: ', comp_phone)
        print('BBB Rating: ', bbb_rating)
        print('BBB Rating Range: ', bbb_rating_range)
        print('Company Average Point: ', company_rating_ave)
        print('Accredicted: ', accredicted)
        print('Year in Business: ', year_in_business)
        try:
            print('Accredicted Since: ', accredicted_since)
        except:
            print('Accredicted Since: ', accredicted_since) 
        print('Source: ', source)
        self.writer.writerow([comp_name or 'NIL', category or 'NIL', comp_address or 'NIL',
                            comp_phone or 'NIL', bbb_rating or 'NIL', bbb_rating_range or 'NIL',
                            company_rating_ave or 'NIL', year_in_business or 'NIL', accredicted or 'NIL',
                            accredicted_since or 'NIL', source or 'NIL'])

        # except:
        #     print('Get info error')
        #     self.writer.writerow(['NIL' or comp_name,'NIL' or category,'NIL' or comp_address,'NIL' or comp_phone,
        #                           'NIL' or bbb_rating,'NIL' or bbb_rating_range ,
        #                           'NIL' or company_rating_ave,'NIL' or year_in_business,
        #                           'NIL' or accredicted,'NIL' or accredicted_since,'NIL' or source])


    def go_back(self):
        self.driver.back()

    def process(self):
        entities = self.driver.find_elements(
            By.CLASS_NAME, 'bds-h4'
        )
        COMP_PATH = '//*[@id="content"]/div/div[3]/div/div[1]/div[2]/div[1]/div[2]/div/div[1]/div[1]/h3/a'
        self.click_on_entity(COMP_PATH=COMP_PATH)
        print(f'Company')
        self.get_info()
        print(' ')
        self.go_back()
        COMP_PATH = '//*[@id="content"]/div/div[3]/div/div[1]/div[2]/div[5]/div/div[1]/div[1]/h3/a'
        self.click_on_entity(COMP_PATH=COMP_PATH)
        print('Next Company')
        self.get_info()
        print(' ')
        self.go_back()
        x = 5
        y = 5
        # print(len(entities))
        for i in range(len(entities)-2):
            try:
                COMP_PATH = f'//*[@id="content"]/div/div[3]/div/div[1]/div[2]/div[{x}]/div/div[1]/div[1]/h3/a'
                self.click_on_entity(COMP_PATH=COMP_PATH)
                print(f'Next Company')
                self.get_info()
                print(' ')
                self.go_back()
                x+=1
            except:
                COMP_PATH = f'//*[@id="content"]/div/div[3]/div/div[1]/div[2]/div[{y}]/div/div[1]/div[1]/h3/a'
                self.click_on_entity(COMP_PATH=COMP_PATH)
                self.get_info()
                self.go_back()
                y=+1


    def pagination(self):
        try:
            nbtn = self.driver.find_element(
                By.LINK_TEXT, 'Next'
            )
            nbtn.click()
        except:
            print('Cant locate Next button')

    def engine(self):
        self.writer.writerow(['COMPANY NAME', 'CATEGORY', 'COMPANY ADDRESS',
                                'COMPANY PHONE', 'BBB RATING', 'BBB RATING AVERAGE',
                                'COMPANY RATING AVERAGE POINT', 'YEAR(S) IN BUSINESS', 'ACCREDICTED',
                                'ACCREDICTED SINCE', 'SOURCE'])
        try:
            num_of_page_ele = self.driver.find_element(
                By.XPATH, '//*[@id="content"]/div/div[3]/div/div[1]/div[3]/div/span[1]'
            )
            str_num_of_page = num_of_page_ele.text 
            numbers = re.findall(r'\d+', str_num_of_page)
        except:
            num_of_page_ele = 15

        try:
            if len(numbers) >= 2:
                num_of_page = numbers[1]
            else:
                print("Unable to extract the second number.")
        except:
            num_of_page = 15

        for i in range(15):
            self.process()
            self.pagination()
        else:
            print('A problem occured')
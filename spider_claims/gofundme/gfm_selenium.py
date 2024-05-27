from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def extract_gofundme_urls(url):
    # Set up Selenium options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # Set up the WebDriver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Fetch the page
        driver.get(url)
        
        # Optional: Wait for some time if the page takes time to load dynamically
        driver.implicitly_wait(10)
        
        # Extract links
        links = driver.find_elements(By.TAG_NAME, 'a')
        gofundme_urls = [link.get_attribute('href') for link in links if 'gofundme.com' in link.get_attribute('href')]
        
        return gofundme_urls
    
    finally:
        driver.quit()


def save_urls_to_file(urls, filename):
    with open(filename, 'w') as file:
        for url in urls:
            file.write(url + '\n')

if __name__ == "__main__":
    # search results page has more links
    # this searches for categories Nonprofit, Education, Animal, Environment, Community
    url = "https://www.gofundme.com/s?c=13&c=342&c=17&c=3&c=7"
    #"https://www.gofundme.com/"

    gofundme_urls = extract_gofundme_urls(url)

    save_urls_to_file(gofundme_urls, 'gofundme_all_urls.txt')


# /companies

from bs4 import BeautifulSoup
import requests



html_text = requests.get("https://opencorporates.com/companies?jurisdiction_code=&q=a&utf8=%E2%9C%93").text
soup = BeautifulSoup(html_text, 'lxml')
companies = soup.find('li', class_ = 'search-result company inactive deregistered')
print(companies)

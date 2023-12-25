from scrapy import Spider, Request
from urllib.parse import urljoin
from trustpilotscraper.items import CompanyItem


# from scrapy import Spider, Request
# from urllib.parse import urljoin
# from ..items import CompanyItem

class TrustpilotSpiderSpider(Spider):
    name = "trustpilotspider"
    allowed_domains = ["www.trustpilot.com", 
                    #    'proxy.scrapeops.io'
                       ]
    start_urls = ["https://www.trustpilot.com/categories"]

    ## Override the FEEDS in settings.py  
    custom_settings = {
        'FEEDS':{
            'trustpilotdata.json': {'format': 'json', 'overwrite': True},
            'trustpilotdata.csv': {'format': 'csv', 'overwrite': True},
        }
    }

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse)

    # def response_is_ban(self, request, response):
    #     return b'banned' in response.body

    # def exception_is_ban(self, request, exception):
    #     return None

    def parse(self, response):
        categories = response.css('div.styles_heading__nxYa7')

        for category in categories:
            cat_relative_url = category.css('.styles_headingLink__fl2dp').attrib['href']

            category_url = response.urljoin(cat_relative_url)
            yield Request(category_url, callback=self.parse_category)

    def parse_category(self, response):
        companies = response.css('div.styles_wrapper__2JOo2')

        for company in companies:
            relative_url = company.css('.styles_linkWrapper__UWs5j').attrib['href']

            company_url = response.urljoin(relative_url)
            yield Request(company_url, callback=self.parse_company_page)

        next_page = response.css('.pagination-link_next__SDNU4').attrib['href']

        if next_page is not None:
            next_page_url = urljoin('https://www.trustpilot.com/', next_page)
            yield Request(next_page_url, callback=self.parse_category)

    def parse_company_page(self, response):
        address_list = response.css('ul.styles_contactInfoElements__YqQAJ li.styles_contactInfoElement__SxlS3')

        company_item = CompanyItem()

        company_item['url'] = response.url
        company_item['company_name'] = response.css('#business-unit-title h1.title_title__i9V__ span.title_displayName__TtDDM::text').get()
        try:
            company_item['company_mail_address'] = address_list[0].css('.link_link__IZzHN::text').get()
        except:
            company_item['company_mail_address'] = 'NIL'
        try:
            company_item['company_geo_location'] = address_list[1].css('.styles_contactInfoAddressList__RxiJI li::text').get()
        except:
            company_item['company_geo_location'] = 'NIL'
        company_item['company_image_source'] = response.css('div.styles_summary__gEFdQ div.profile-image_imageWrapper__kDdWe a picture img::attr(src)').get()
        company_item['company_category'] = response.css('li.breadcrumb_breadcrumb__lJO__ a::text').extract()
        company_item['company_trustpilot_rating'] = response.css('#business-unit-title div.styles_container__OaEK8 div.styles_rating__NPyeH p::text').get()
        company_item['verified'] = response.css('#business-unit-title button.styles_verificationLabel__kukuk div.styles_verificationIcon___X7KO::text').get()
        company_item['number_of_reviews'] = response.css('#business-unit-title span.styles_clickable__zQWyh span.styles_text__W4hWi::text').get()

        yield company_item

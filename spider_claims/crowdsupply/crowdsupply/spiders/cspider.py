import scrapy
from scrapy.spiders import Spider, Request
from urllib.parse import urljoin
from datetime import date


class CSpider(Spider):
    name = "cspider"
    allowed_domains = ["crowdsupply.com"]
    start_urls = ["https://www.crowdsupply.com/browse"]

    custom_settings = {
        "FEEDS": {
            "crowdsupply-demo.csv": {"format": "csv", "overwrite": True},
        },
    }

    def parse(self, response):
        # Extract project URLs from the browse page
        project_urls = response.css("a.project-tile::attr(href)").extract()
        for project_url in project_urls:
            full_project_url = urljoin(response.url, project_url)
            yield Request(url=full_project_url, callback=self.parse_projectpage)

    def parse_projectpage(self, response):
        self.logger.info(f"Parsing project page: {response.url}")
        try:
            project_name = response.xpath(
                "/html/body/section[1]/div/h1/a/text()"
            ).extract_first()
            if project_name:
                project_url = response.url
                project_description = response.xpath(
                    "/html/body/section[1]/div/h3/text()"
                ).extract_first()
                raised_amount = response.xpath(
                    "/html/body/section[1]/div/div/div[2]/div/div[1]/div/p[1]/span/text()"
                ).extract_first()
                goal_amount = response.xpath(
                    "/html/body/section[1]/div/div/div[2]/div/div[1]/div/p[2]/span/text()"
                ).extract_first()
                date_funded_days_to_be_funded = response.xpath(
                    "/html/body/section[1]/div/div/div[2]/div/div[1]/div/div[2]/div[2]/a/span[1]/text()"
                ).extract_first()
                number_of_backers = response.xpath(
                    "/html/body/section[1]/div/div/div[2]/div/div[1]/div/div[2]/div[3]/a/span[1]/text()"
                ).extract_first()

                project_data = {
                    "Project Name": project_name,
                    "Project URL": project_url,
                    "Raised Amount": raised_amount,
                    "Project Description": project_description,
                    "Goal Amount": goal_amount,
                    "Date Funded or Days to be funded": date_funded_days_to_be_funded,
                    "Date Scraped": date.today(),
                    "Number of Backers": number_of_backers,
                }

                if not project_url.endswith("/"):
                    project_url += "/"
                backers_url = project_url + "backers/"
                request = scrapy.Request(
                    url=backers_url,
                    callback=self.parse_backerspage,
                    errback=self.handle_error,
                )
                request.meta["project_data"] = project_data
                yield request

                if number_of_backers:
                    try:
                        number_of_backers_int = int(number_of_backers.replace(",", ""))
                        number_of_backers_pages = number_of_backers_int // 100
                        # Follow pagination for backers pages
                        for page in range(2, number_of_backers_pages + 1):
                            paginated_backers_url = f"{backers_url}?page={page}"
                            request = scrapy.Request(
                                url=paginated_backers_url,
                                callback=self.parse_backerspage,
                                errback=self.handle_error,
                            )
                            request.meta["project_data"] = project_data
                            yield request
                    except ValueError:
                        self.logger.error(
                            f"Failed to convert number of backers to integer: {number_of_backers}"
                        )
            else:
                self.logger.warning(f"Project name not found: {response.url}")
        except Exception as e:
            self.logger.error(f"Error parsing project page {response.url}: {e}")

    def parse_backerspage(self, response):
        self.logger.info(f"Parsing backers page: {response.url}")
        try:
            project_data = response.meta.get("project_data", {})
            backers_url = response.url
            backers = response.css(".mb-3 p.mt-2::text").getall()

            project_data["Backers URL"] = backers_url
            project_data["Backers"] = backers

            yield project_data
        except KeyError as e:
            self.logger.error(
                f"KeyError: {e} - Missing 'project_data' in meta for URL: {response.url}"
            )
        except Exception as e:
            self.logger.error(f"Error parsing backers page {response.url}: {e}")

    def handle_error(self, failure):
        self.logger.error(repr(failure))

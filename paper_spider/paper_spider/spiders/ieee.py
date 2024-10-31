import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class IEEEPaperSpider(scrapy.Spider):
    name = "ieee_paper_spider"

    def __init__(self, conference=None, year=None):
        base_urls = {
            # ICRA
            'ICRA_2024': "https://ieeexplore.ieee.org/xpl/conhome/10609961/proceeding?isnumber=10609862&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
            'ICRA_2023': "https://ieeexplore.ieee.org/xpl/conhome/10160211/proceeding?isnumber=10160212&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
            'ICRA_2022': "https://ieeexplore.ieee.org/xpl/conhome/9811522/proceeding?isnumber=9811357&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
            'ICRA_2021': "https://ieeexplore.ieee.org/xpl/conhome/9560720/proceeding?isnumber=9560666&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
            'ICRA_2020': "https://ieeexplore.ieee.org/xpl/conhome/9187508/proceeding?isnumber=9196508&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
            'ICRA_2019': "https://ieeexplore.ieee.org/xpl/conhome/8780387/proceeding?isnumber=8793254&sortType=vol-only-seq&rowsPerPage=100&pageNumber=", 
            'ICRA_2018': "https://ieeexplore.ieee.org/xpl/conhome/8449910/proceeding?isnumber=8460178&sortType=vol-only-seq&rowsPerPage=100&pageNumber=", 
            # IROS
            # 'IROS_2023': "https://ieeexplore.ieee.org/xpl/conhome/10341341/proceeding?isnumber=10341342&sortType=vol-only-seq&rowsPerPage=100&pageNumber=",
        }
        self.base_url = base_urls.get(f"{conference}_{year}")
        if not self.base_url:
            self.logger.error(f"Invalid conference or year: {conference}_{year}")

    def start_requests(self):
        # Start scraping from page 1
        start_page = 1
        yield SeleniumRequest(
            url=f"{self.base_url}{start_page}",
            callback=self.parse,
            wait_time=10,
            wait_until=EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'xpl-issue-results-items > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > h2 > a')
            ),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
            meta={'page_number': start_page}  # Pass the current page number to the next request
        )

    def parse_abstract(self, response):
        title = response.meta.get('title')
        abstract = response.css('xpl-document-abstract > section > div:nth-of-type(2) > div:nth-of-type(1) > div > div > div::text').get()
        authors = response.css('div.authors-info-container span.authors-info a > span::text').getall()
        authors = ', '.join(authors)
        print(title)

        if abstract:
            yield {
                'title': title,
                'authors': authors,
                'abstract': abstract
            }

    def parse(self, response):
        links = response.css('xpl-issue-results-items > div > div:nth-of-type(2) > h2 > a::attr(href)').getall()
        titles = response.css('xpl-issue-results-items > div > div:nth-of-type(2) > h2 > a::text').getall()

        # Iterate over the links and titles, sending a new request to each link to parse the abstract
        for link, title in zip(links, titles):
            full_link = f"https://ieeexplore.ieee.org{link}"
            yield SeleniumRequest(
                url=full_link,
                callback=self.parse_abstract,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                meta={'title': title}  # Pass the title to the next request
            )

        # Pagination logic - Move to the next page if available
        current_page = response.meta['page_number']
        next_page = current_page + 1
    
        try:
            yield SeleniumRequest(
                url=f"{self.base_url}{next_page}",
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'xpl-issue-results-items > div:nth-of-type(1) > div:nth-of-type(1) > div:nth-of-type(2) > h2 > a')
                ),
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                meta={'page_number': next_page}  # Pass the next page number
            )
        except TimeoutException:
            # Handle the timeout, which likely means there are no more pages to scrape
            self.logger.error(f"TimeoutException encountered at page {next_page}, stopping pagination.")
            print(f"No more pages found after page {current_page}. Stopping.")



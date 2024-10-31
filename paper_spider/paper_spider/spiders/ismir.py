import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait


class ISMIRPaperSpider(scrapy.Spider):
    name = "ismir_paper_spider"

    def __init__(self, year=None):
        self.year = year

        base_urls = {
            '2023': "https://ismir2023program.ismir.net/papers.html?filter=keywords&session=",
            '2022': "https://ismir2022program.ismir.net/papers.html?filter=keywords&session=",
            '2021': "https://ismir2021.ismir.net/papers",
        }
        self.base_url = base_urls.get(f"{year}")
        if not self.base_url:
            self.logger.error(f"Invalid year: {year}")

    def start_requests(self):
        if int(self.year) in [2022, 2023]:            
            # Start scraping from page 1
            start_session = 1
            yield SeleniumRequest(
                url=f"{self.base_url}{start_session}",
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'body > div.container > div.content > div.cards.row.papers-cards > div > a')
                ),
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                meta={'session_number': start_session}  # Pass the current page number to the next request
            )
        elif int(self.year) in [2021]:            
            yield scrapy.Request(
                url=self.base_url,  # 2021년 URL로 직접 요청
                callback=self.parse,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
            )
        else:
            raise NotImplementedError

    def parse_abstract(self, response):
        def extract_with_xpath(query):
            return response.xpath(query).get()#.strip()
        
        title = response.meta.get('title')
        print(title)
        authors = response.xpath('/html/body/div[1]/div[2]/div[1]/div/h3/a/text()').getall()
        authors = [author.strip() for author in authors]
        authors = ', '.join(authors)
        abstract = extract_with_xpath("//*[@id='abstractExample']/p[1]/text()")

        if abstract:
            yield {
                'title': title,
                'authors': authors,
                'abstract': abstract
            }

    def parse(self, response):
        if int(self.year) in [2022, 2023]:          
            links = response.css('div.cards.row.papers-cards > div > a::attr(href)').getall()
            print(links)
            titles = response.css('div.cards.row.papers-cards > div > a > div > div > h5::text').getall()
            titles = [title.split(":", 1)[1].strip() for title in titles]
            print(len(links), len(titles))
            # print(link, title)

            # Iterate over the links and titles, sending a new request to each link to parse the abstract
            for link, title in zip(links, titles):
                full_link = f"https://ismir{self.year}program.ismir.net/{link}"
                yield SeleniumRequest(
                    url=full_link,
                    callback=self.parse_abstract,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                    meta={'title': title}
                )
                yield SeleniumRequest(
                    url=full_link,
                    callback=self.parse_abstract,
                    wait_time=10,
                    wait_until=EC.presence_of_all_elements_located(
                        (By.XPATH, '/html/body/div[1]/div[2]/div[3]/div[1]/div/div/div')
                    ),
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                )

            # Pagination logic - Move to the next page if available
            current_session = response.meta['session_number']
            next_session = current_session + 1
        
            try:
                yield SeleniumRequest(
                    url=f"{self.base_url}{next_session}",
                    callback=self.parse,
                    wait_time=10,
                    wait_until=EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'body > div.container > div.content > div.cards.row.papers-cards > div > a')
                    ),
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'},
                    meta={'session_number': next_session}  # Pass the next page number
                )
            except TimeoutException:
                # Handle the timeout, which likely means there are no more pages to scrape
                self.logger.error(f"TimeoutException encountered at page {next_session}, stopping pagination.")
                print(f"No more pages found after page {current_session}. Stopping.")

        elif int(self.year) in [2021]:            
            papers = response.xpath('//div[starts-with(@class, "paper")]')
            for paper in papers:
                title = paper.xpath('./div[1]/text()')
                if title:
                    title = title.get().strip()
                    authors = paper.xpath('./div[2]').getall()
                    authors = paper.xpath('./div[2]/span[@class="paper_author"]/text()').getall()
                    authors = [author.strip() for author in authors]
                    authors = ', '.join(authors)
                    abstract = response.xpath('//*[@id="paper_abstract_1"]/p/text()').get().strip()
                    print(title)
                    if abstract:
                        # Yield the title, paper_id, abstract, and authors
                        yield {
                            'title': title,
                            'authors': authors,
                            'abstract': abstract
                        }
        else:
            raise NotImplementedError
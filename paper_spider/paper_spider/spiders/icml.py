import scrapy


class ICMLPaperSpider(scrapy.Spider):
    name = "icml_paper_spider"

    def __init__(self, year=None):
        super(ICMLPaperSpider, self).__init__()

        versions = {
            '2024': 'v235',
            '2023': 'v202',
            '2022': 'v162',
            '2021': 'v139',
            '2020': 'v119',
            '2019': 'v97',
            '2018': 'v80',
        }
        version = versions.get(f"{year}")
        if not version:
            self.logger.error(f"Invalid year: {year}")

        self.start_urls = [
            f"https://proceedings.mlr.press/{version}"
        ]

    def parse(self, response):
        paper_links = response.xpath("/html/body/main/div/div[position()>1]/p[3]/a[1]/@href").getall()
        yield from response.follow_all(paper_links, self.parse_paper)

    def parse_paper(self, response):  # noqa
        def extract_with_xpath(query):
            return response.xpath(query).get().strip()

        title = extract_with_xpath("/html/body/main/div/article/h1/text()")
        authors = extract_with_xpath("/html/body/main/div/article/span/text()")
        authors = ', '.join(authors)
        abstract = extract_with_xpath("//*[@id='abstract']/text()")

        if abstract:
            yield {
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }



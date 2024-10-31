import scrapy


class IJCAIPaperSpider(scrapy.Spider):
    name = "ijcai_paper_spider"

    def __init__(self, year=None):
        super(IJCAIPaperSpider, self).__init__()

        self.start_urls = [
            f"https://www.ijcai.org/proceedings/{year}"
        ]

    def parse(self, response):
        # //*[@id="paper1"]/div[3]/a[2]
        # //*[@id="paper3"]/div[3]/a[2]
        paper_links = response.xpath('//*[starts-with(@id, "paper")]/div[3]/a/@href').getall()
        yield from response.follow_all(paper_links, self.parse_paper)

    def parse_paper(self, response):  # noqa
        def extract_with_xpath(query):
            return response.xpath(query).get().strip()

        title = extract_with_xpath("//*[@id='block-system-main']/div/div/div[1]/div[1]/h1/text()")
        print(title)
        authors = extract_with_xpath("//*[@id='block-system-main']/div/div/div[1]/div[1]/h2/text()")
        abstract = extract_with_xpath("//*[@id='block-system-main']/div/div/div[3]/div[1]/text()")

        if abstract:
            yield {
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }



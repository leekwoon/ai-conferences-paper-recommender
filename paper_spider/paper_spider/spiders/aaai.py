import scrapy


class AAAIPaperSpider(scrapy.Spider):
    name = "aaai_paper_spider"

    def __init__(self, year=None):
        super(AAAIPaperSpider, self).__init__()

        self.start_urls = [
            f"https://dblp.org/db/conf/aaai/aaai{year}.html"
        ]

    def parse(self, response):
        paper_links = response.xpath('//nav/ul/li/div/a[1]/@href').getall()
        yield from response.follow_all(paper_links, self.parse_paper)

    def parse_paper(self, response):  # noqa
        def extract_with_xpath(query):
            return response.xpath(query).get().strip()

        title = extract_with_xpath("/html/body/div[1]/div[1]/div[1]/div/article/h1/text()")

        author_elements = response.xpath('/html/body/div[1]/div[1]/div[1]/div/article/div/div[1]/section[1]/ul/li/span[1]/text()').getall()
        authors = ', '.join([author.strip() for author in author_elements])

        abstract = extract_abstract(response)

        if abstract:
            yield {
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }


def extract_abstract(response):
    # 1. <h2> 태그 이후 <p> 태그가 있는 경우 우선 추출
    abstract = response.xpath('normalize-space(//section[contains(@class, "abstract")]/h2/following-sibling::p)').get()

    # 2. <p> 태그가 없으면 <h2> 태그 이후 바로 나오는 텍스트 노드 추출
    if not abstract:
        abstract = response.xpath('normalize-space(//section[contains(@class, "abstract")]/h2/following-sibling::text())').get()

    # 추출된 abstract가 없으면 None을 반환하고, 있으면 공백을 제거한 후 반환
    return abstract.strip() if abstract else None



import scrapy


class InterspeechPaperSpider(scrapy.Spider):
    name = "interspeech_paper_spider"

    def __init__(self, year=None):
        super(InterspeechPaperSpider, self).__init__()

        self.year = year
        self.start_urls = [
            f"https://www.isca-archive.org/interspeech_{year}/index.html"
        ]

    def parse(self, response):
        # 모든 div 하위의 <a> 태그에서 href 속성을 추출
        paper_links = response.xpath('//div//a/@href').getall()
        paper_links = [link for link in paper_links if link.endswith('.html')]
        paper_links = [f"https://www.isca-archive.org/interspeech_{self.year}" + '/' + link for link in paper_links]

        # 추출된 링크들을 따라가면서 개별 논문 페이지로 이동
        yield from response.follow_all(paper_links, self.parse_paper)

    def parse_paper(self, response):  # noqa
        def extract_with_xpath(query):
            return response.xpath(query).get().strip()

        title = extract_with_xpath("//*[@id='global-info']/h3/text()")
        authors = extract_with_xpath("//*[@id='global-info']/h5/text()")
        abstract = extract_with_xpath("//*[@id='abstract']/p/text()")
        print(title)

        if abstract:
            yield {
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }



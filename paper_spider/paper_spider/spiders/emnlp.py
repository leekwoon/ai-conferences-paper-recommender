import scrapy


class EMNLPPaperSpider(scrapy.Spider):
    name = "emnlp_paper_spider"

    def __init__(self, year=None):
        super(EMNLPPaperSpider, self).__init__()

        self.year = year
        self.start_urls = [
            f"https://aclanthology.org/events/emnlp-{year}"
        ]

    def parse(self, response):
        if self.year in ['2020', '2021', '2022', '2023']:
            paper_links = response.xpath(f'//*[starts-with(@id, "{self.year}")]/p/span[2]/strong/a/@href').getall()
            # paper_links = response.xpath(f'//*[@id="{self.year}emnlp-main"]/p/span[2]/strong/a/@href').getall()
        elif self.year == '2019':
            # paper_links = response.xpath(f'//*[@id="d19-*"]/p/span[2]/strong/a/@href').getall()
            paper_links = response.xpath('//*[starts-with(@id, "d19-")]/p/span[2]/strong/a/@href').getall()
        elif self.year == '2018':
            # ID가 "w18-"로 시작하는 모든 요소에서 링크 추출
            paper_links = response.xpath('//*[starts-with(@id, "w18-")]/p/span[2]/strong/a/@href').getall()
        else:
            raise NotImplementedError

        paper_links = ["https://aclanthology.org" + '/' + link for link in paper_links]
        yield from response.follow_all(paper_links, self.parse_paper)

    def parse_paper(self, response):  # noqa
        def extract_with_xpath(query):
            return response.xpath(query).get().strip()

        # <a> 태그 안의 모든 텍스트와 <span>의 텍스트를 모두 가져오기
        title_parts = response.xpath('//*[@id="title"]/a//text()').getall()

        # 모든 텍스트를 합쳐서 하나의 문자열로 구성
        title = ''.join(title_parts).strip()

        authors = response.xpath("//*[@id='main']/div[1]/p/a/text()").getall()
        authors = ', '.join(authors)
        abstract = extract_with_xpath("//*[@id='main']/div[2]/div[1]/div/div/span/text()")
        print(title)

        if abstract:
            yield {
                "title": title,
                "authors": authors,
                "abstract": abstract,
            }

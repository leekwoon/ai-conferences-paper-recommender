import scrapy


class ICLRPaperSpider(scrapy.Spider):
    name = "iclr_paper_spider"

    def __init__(self, year=None):
        super(ICLRPaperSpider, self).__init__()
        self.year = year
        self.start_urls = [
            f"https://iclr.cc/Conferences/{year}/Schedule"
        ]

    def parse(self, response):
        # XPath to select all 'maincard_*' elements
        papers = response.xpath('//div[starts-with(@id, "maincard_")]')

        # Loop through each paper and extract the title and id
        for paper in papers:
            paper_id = paper.xpath('@id').get()
            paper_id = paper_id.split('_')[1]
            title = paper.xpath('./div[3]/text()').get().strip() if paper.xpath('./div[3]/text()').get() else None
            paper_type = paper.xpath('./div[1]/text()').get().strip() if paper.xpath('./div[1]/text()').get() else None

            if paper_type in ['Poster', 'Oral', 'Spotlight Poster', 'Spotlight',
                # year 2023
                'In-Person Poster presentation / top 5% paper',
                'In-Person presentation / poster accept',
                'Virtual presentation / top 25% paper',
                'In-Person Poster presentation / top 25% paper',
                'Virtual Poster presentation / top 5% paper',
                'Virtual Poster presentation / top 25% paper',
                'In-Person Poster presentation / poster accept',
                'Virtual presentation / top 5% paper',
                'Virtual Poster presentation / poster accept',
                'In-Person Oral presentation / top 25% paper',
                'In-Person Oral presentation / top 5% paper',
                'Virtual presentation / poster accept'
            ]:
                # Make a request to the individual paper page to get the abstract and author info
                paper_url = f'https://iclr.cc/Conferences/{self.year}/Schedule?showEvent={paper_id}'
                # Pass the title and paper_id to the next request
                yield scrapy.Request(paper_url, callback=self.parse_paper_details, meta={'title': title, 'paper_id': paper_id})

    def parse_paper_details(self, response):
        # Extract the abstract from the individual paper page
        abstract = response.xpath('//div[@class="abstractContainer"]/p/text() | //div[@class="abstractContainer"]/text()').get()

        # Extract authors (assuming they are in buttons as per your example)
        author_buttons = response.xpath('//*[@id="main"]/div[2]/div/button/text()').getall()
        authors = [author.strip() for author in author_buttons]
        authors = ', '.join(authors)

        # Get the title and paper_id from the previous response's meta data
        title = response.meta['title']
        # paper_id = response.meta['paper_id']

        if abstract:
            # Yield the title, paper_id, abstract, and authors
            yield {
                'title': title,
                'authors': authors,
                'abstract': abstract
            }



import scrapy
from scrapy.item import Item, Field

from scrapy.conf import settings
from scrapy import Request
import requests
from scrapy import Selector


class SiteProductItem(Item):
    Blog = Field()
    Description_About_Us = Field()
    ImageUrls_About_Us = Field()
    StaffMembers_Name = Field()
    StaffMembers_Photo = Field()
    StaffMembers_Role = Field()


class BlogScraper (scrapy.Spider):
    name = "scrapingdata"
    allowed_domains = ['www.55places.com']
    DOMAIN_URL = 'https://www.55places.com'
    START_URL = 'https://www.55places.com/blog'
    ABOUT_PAGE_URL = 'https://www.55places.com/about'
    pagination = 'https://www.55places.com/blog/page/{page_num}'
    settings.overrides['ROBOTSTXT_OBEY'] = False
    current_page = 1

    def start_requests(self):
        yield Request(url=self.START_URL,
                      callback=self.parse_page,
                      dont_filter=True
                      )

    def parse_page(self, response):

        #  Crawl description in about us page.
        aboutus_description = ""
        paneldata_aboutus = requests.get('https://www.55places.com/about').content
        about_us_content = Selector(text=paneldata_aboutus)
        paneldata = about_us_content.xpath('//div[@class="panel-body"]/p//text()').extract()
        for panel_datum in paneldata:
            aboutus_description = " " + panel_datum

        #  Crawl Image Url in about us page.
        image_urls_aboutus = about_us_content.xpath('//div[@class="panel-body"]//img/@src').extract()

        #  Crawl Staff Members in about us page.
        staff_members_name = about_us_content.xpath('//div[contains(@class, "name-title")]'
                                                    '//span[@itemprop="name"]//text()').extract()
        staff_members_role = about_us_content.xpath('//div[contains(@class, "name-title")]'
                                                    '//span[@itemprop="roleName"]//text()').extract()
        staff_members_photo = about_us_content.xpath('//div[@class="panel-body"]//img/@src').extract()

        #  Crawl all data from blog page
        meta = response.meta
        blog = meta.get('blog')
        if not blog:
            blog = []

        blog_articles_list = response.xpath('//li[@class="list-item"]'
                                            '//a[contains(@class, "blog-article-link-component")]/@href').extract()

        for blog_article in blog_articles_list:
            blog_url = self.DOMAIN_URL + blog_article
            blog_data = requests.get(blog_url).content
            blog_content = Selector(text=blog_data)
            blog_title = blog_content.xpath('//div[@class="title-section"]/h3[@class="title h3"]//text()').extract()
            blog_writer = blog_content.xpath("//meta[@itemprop='name']/@content").extract()[1]
            blog_date = self._parse_blog_date(blog_content)
            blog_subtitles = blog_content.xpath('//div[@class="article-body"]//h3//text()').extract()
            image_urls = blog_content.xpath('//div[@class="full-width"]//img//@src').extract()
            blog_description = self._parse_blog_description(blog_content)

            json_blog = {
                "blog title": blog_title,
                "blog writer": blog_writer,
                "blog date": blog_date,
                "blog subtitles": blog_subtitles,
                "image urls": image_urls,
                "blog description": blog_description
            }

            blog.append(json_blog)

        #   Pagination

        older_post = response.xpath('//div[@class="blog-articles-pagination"]'
                                    '//div[contains(@class, "text-left")]').extract()
        if len(older_post) == 0:
            next_page = None
        else:
            self.current_page += 1
            next_page = self.pagination.format(page_num=self.current_page)

        if next_page:
            meta['blog'] = blog
            yield Request(
                url=next_page,
                callback=self.parse_page,
                meta=meta
            )
        if self.current_page == 2:
        # else:
            result = SiteProductItem()
            result['Blog'] = blog
            result['Description_About_Us'] = aboutus_description
            result['ImageUrls_About_Us'] = image_urls_aboutus
            result['StaffMembers_Name'] = staff_members_name
            result['StaffMembers_Photo'] = staff_members_photo
            result['StaffMembers_Role'] = staff_members_role
            yield result

    @staticmethod
    def _parse_blog_date(response):
        assert_date = response.xpath('//div[@class="blog-articles-meta-component"]//text()').extract()[0]
        blog_date = assert_date.split('on')[-1]
        return blog_date

    @staticmethod
    def _parse_blog_description(response):
        blog_descs = response.xpath('//div[@itemprop="articleBody"]//p//text()').extract()
        for blog_desc in blog_descs:
            blog_description = " " + blog_desc
        return blog_description


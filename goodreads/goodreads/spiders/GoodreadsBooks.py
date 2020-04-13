import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
from datetime import datetime, timezone
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

class BookInformation(scrapy.Item):
    Name = scrapy.Field()
    Author = scrapy.Field()
    Rating_count = scrapy.Field()
    Rating_score = scrapy.Field()
    Pages = scrapy.Field()
    url = scrapy.Field()
    Genres = scrapy.Field()
    Original_name = scrapy.Field()
    ISBN = scrapy.Field()
    ISBN13 = scrapy.Field()
    ASIN = scrapy.Field()
    Format = scrapy.Field()
    Edition = scrapy.Field()
    First_Published_Date = scrapy.Field()
    Edition_Publish_Info = scrapy.Field()
    Edition_Language = scrapy.Field()
    Literary_Awards = scrapy.Field()
    Review_Count = scrapy.Field()
    Image_Url = scrapy.Field()
    Date_Time_Collected = scrapy.Field()

    def __lt__(self, other):
        # return self['pages'] < other['pages']
        return (self['rating_count'] * self['rating_score']) > \
               (other['rating_count'] * other['rating_score'])


# restrict path for popular lists = (//a[contains(@href, "/list/popular_lists")])[text()<lessthan][text()>biggerthan]
# Note the the start_url should be somewhere where you can take the pages else it will never reach the domain we want
# (ie if you want from 500 to 550 you have to start in the page 500 because if you start in 1 then it cannot see the
# 500th page with an href)
class GoodreadsSpider1(CrawlSpider):
    name = 'goodreads1'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/list/popular_lists']
    rules = (
        Rule(LinkExtractor(allow=('/list/popular',),
                           restrict_xpaths='(//a[contains(@href, "/list/popular_lists")])[text()<=1]')),
        Rule(LinkExtractor(allow=('/list/show/',),
                           restrict_xpaths='//div[@class="pagination"] | //a[@class="listTitle"]')),
        Rule(LinkExtractor(allow=('/book/show/',), restrict_xpaths='//a[@class="bookTitle"]'), callback='parse_book',
             follow=True),
        # Rule(LinkExtractor(allow=('/work/editions/',))),
    )

    def parse_book(self, response):
        item = BookInformation()
        return parse_book(item, response)


class GoodreadsSpider2(CrawlSpider):
    name = 'goodreads2'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/list/popular_lists?page=2']
    rules = (
        Rule(LinkExtractor(allow=('/list/popular',),
                           restrict_xpaths='(//a[contains(@href, "/list/popular_lists")])[text()<=2][text()>1]')),
        Rule(LinkExtractor(allow=('/list/show/',),
                           restrict_xpaths='//div[@class="pagination"] | //a[@class="listTitle"]')),
        Rule(LinkExtractor(allow=('/book/show/',), restrict_xpaths='//a[@class="bookTitle"]'), callback='parse_book',
             follow=True),
        # Rule(LinkExtractor(allow=('/work/editions/',))),
    )

    def parse_book(self, response):
        item = BookInformation()
        return parse_book(item, response)

class GoodreadsSpider3(CrawlSpider):
    name = 'goodreads3'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/list/popular_lists?page=3']
    rules = (
        Rule(LinkExtractor(allow=('/list/popular',),
                           restrict_xpaths='(//a[contains(@href, "/list/popular_lists")])[text()<=3][text()>2]')),
        Rule(LinkExtractor(allow=('/list/show/',),
                           restrict_xpaths='//div[@class="pagination"] | //a[@class="listTitle"]')),
        Rule(LinkExtractor(allow=('/book/show/',), restrict_xpaths='//a[@class="bookTitle"]'), callback='parse_book',
             follow=True),
        # Rule(LinkExtractor(allow=('/work/editions/',))),
    )

    def parse_book(self, response):
        item = BookInformation()
        return parse_book(item, response)

class GoodreadsSpider4(CrawlSpider):
    name = 'goodreads4'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/list/popular_lists?page=3']
    rules = (
        Rule(LinkExtractor(allow=('/list/popular',),
                           restrict_xpaths='(//a[contains(@href, "/list/popular_lists")])[text()<=3][text()>2]')),
        Rule(LinkExtractor(allow=('/list/show/',),
                           restrict_xpaths='//div[@class="pagination"] | //a[@class="listTitle"]')),
        Rule(LinkExtractor(allow=('/book/show/',), restrict_xpaths='//a[@class="bookTitle"]'), callback='parse_book',
             follow=True),
        Rule(LinkExtractor(allow=('/work/editions/',))),
    )

    def parse_book(self, response):
        item = BookInformation()
        return parse_book(item, response)



def edition_publishing_info_parse(response):
    edition_publish_info = response.xpath('//div[@class="row"][contains(text(),"Published")]//text()').get()
    if edition_publish_info:
        edition_publish_info = re.sub('\\s+', ' ', edition_publish_info).strip()
    return edition_publish_info


def first_published_parse(response):
    first_published = response.xpath('//nobr[@class="greyText"]//text()').get()
    if first_published:
        first_published = first_published.strip()
        first_published = re.compile('(?<=published )(.*)').search(first_published).group(1)[:-1]
    else:
        first_published = None
    return first_published


def pages_check(response):
    pages = response.xpath('//span[@itemprop="numberOfPages"]//text()').get()
    if pages is None:
        pages = float(-1)
    elif len(pages) <= 6:
        pages = float(1)
    else:
        pages = float(pages.strip()[:-6])
    return pages


def get_ISBNs(response):
    ISBN = response.xpath('//div[contains(text(),"ISBN")]/parent::*//div[@class="infoBoxRowItem"]//text()').get()
    ISBN13 = response.xpath('//span[@itemprop="isbn"]//text()').get()
    if ISBN:
        ISBN = ISBN.strip()
        if len(ISBN) == 9:
            ISBN = str(0) + str(ISBN)
        elif len(ISBN) == 13:
            ISBN13 = ISBN
            ISBN = None
        elif len(ISBN) != 10:
            ISBN = None

    if ISBN13:
        ISBN13 = ISBN13.strip()
        if len(ISBN13) == 10:
            ISBN = ISBN13
            ISBN13 = None
        elif len(ISBN13) == 9:
            ISBN = str(0) + ISBN13
            ISBN13 = None
        elif len(ISBN13) != 13:
            ISBN13 = None

    return [ISBN, ISBN13]


def parse_book(item, response):
    name = response.xpath('//h1[@id="bookTitle"]//text()').get().strip()
    item['Name'] = name

    rating_count = float(
        response.xpath('//div[@id="bookMeta"]//a[2]//meta[@itemprop="ratingCount"]/@content').get())
    item['Rating_count'] = rating_count

    rating_score = float(response.xpath('//span[@itemprop="ratingValue"]//text()').get().strip())
    item['Rating_score'] = rating_score

    genres = response.xpath('//a[@class="actionLinkLite bookPageGenreLink"]//text()').getall()
    item['Genres'] = genres

    pages = pages_check(response)
    item['Pages'] = pages

    original_name = response.xpath('//div[contains(text(),"Original Title")]/parent::*[1]//div[2]//text()').get()
    item['Original_name'] = original_name

    awards = response.xpath(
        '//div[contains(text(),"Literary Awards")]/parent::*//a[@class="award"]//text()').getall()
    item['Literary_Awards'] = awards

    edition_language = response.xpath('//div[contains(text(),"Edition Language")]'
                                      '/parent::*//div[@itemprop="inLanguage"]//text()').get()
    item['Edition_Language'] = edition_language

    author = response.xpath('//a[@class="authorName"]//span[@itemprop="name"]//text()').get()
    item['Author'] = author

    review_count = response.xpath('//meta[@itemprop="reviewCount"]//@content').get()
    item['Review_Count'] = float(review_count)

    book_format = response.xpath('//span[@itemprop="bookFormat"]//text()').get()
    item['Format'] = book_format

    edition = response.xpath('//span[@itemprop="bookEdition"]//text()').get()
    item['Edition'] = edition

    image_url = response.xpath('//img[@id="coverImage"]//@src').get()
    item['Image_Url'] = image_url

    edition_publish_info = edition_publishing_info_parse(response)
    item['Edition_Publish_Info'] = edition_publish_info

    first_published = first_published_parse(response)
    item['First_Published_Date'] = first_published

    [ISBN, ISBN13] = get_ISBNs(response)
    item['ISBN'] = ISBN
    item['ISBN13'] = ISBN13

    ASIN = response.xpath('//div[contains(text(),"ASIN")]/parent::*//div[@itemprop="isbn"]//text()').get()
    item['ASIN'] = ASIN

    item['url'] = response.url

    date_time_collected = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    item['Date_Time_Collected'] = date_time_collected

    return item
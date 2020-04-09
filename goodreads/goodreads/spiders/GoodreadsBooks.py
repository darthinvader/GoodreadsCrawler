import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
from datetime import datetime, timezone


class BookInformation(scrapy.Item):
    Name = scrapy.Field()  # DONE
    Author = scrapy.Field()  # DONE
    Rating_count = scrapy.Field()  # DONE
    Rating_score = scrapy.Field()  # DONE
    Pages = scrapy.Field()  # DONE
    url = scrapy.Field()  # DONE
    Genres = scrapy.Field()  # DONE
    Original_name = scrapy.Field()  # DONE
    ISBN = scrapy.Field()  # DONE
    ISBN13 = scrapy.Field()  # DONE
    ASIN = scrapy.Field()  # DONE  # DONE
    Format = scrapy.Field()  # DONE
    Edition = scrapy.Field()  # DONE
    First_Published = scrapy.Field()  # DONE
    Edition_Published = scrapy.Field()
    Edition_Publisher = scrapy.Field()
    Edition_Language = scrapy.Field()  # DONE
    Literary_Awards = scrapy.Field()  # DONE
    Review_Count = scrapy.Field()  # DONE
    Image_Url = scrapy.Field()  # DONE
    Date_Time_Collected = scrapy.Field()  # DONE

    def __lt__(self, other):
        # return self['pages'] < other['pages']
        return (self['rating_count'] * self['rating_score']) > \
               (other['rating_count'] * other['rating_score'])


# class Book_Ammount(scrapy.Item):


class GoodreadsSpider(CrawlSpider):
    name = 'goodreads'
    allowed_domains = ['goodreads.com']
    start_urls = ['https://www.goodreads.com/list/show/16997.Books_for_Intelligent_Teens']
    rules = (
        Rule(LinkExtractor(allow=('/list/popular',))),
        Rule(LinkExtractor(allow=('/list/show/',),
                           restrict_xpaths='//div[@class="pagination"] | //a[@class="listTitle"]')),
        Rule(LinkExtractor(allow=('/book/show/',), restrict_xpaths='//a[@class="bookTitle"]'), callback='parse_book',
             follow=True),
        Rule(LinkExtractor(allow=('/work/editions/',))),
    )

    def parse_book(self, response):
        item = BookInformation()

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
        item['Review_Count'] = review_count

        book_format = response.xpath('//span[@itemprop="bookFormat"]//text()').get()
        item['Format'] = book_format

        edition = response.xpath('//span[@itemprop="bookEdition"]//text()').get()
        item['Edition'] = edition

        image_url = response.xpath('//img[@id="coverImage"]//@src').get()
        item['Image_Url'] = image_url

        book_publishing_info = response.xpath('//div[@class="row"][contains(text(),"Published")]//text()').get()
        # print(book_publishing_info)
        first_published = response.xpath('//nobr[@class="greyText"]//text()').get()
        if first_published:
            first_published = first_published.strip()
            first_published = re.compile('(?<=published )(.*)').search(first_published).group(1)[:-1]
        else:
            first_published = None
        item['First_Published'] = first_published

        if book_publishing_info:
            book_info = book_publishing_info.splitlines()
            edition_published = book_info[1].strip()
            if not edition_published.startswith('Published'):
                # print(edition_published)
                edition_publisher = book_info[1].strip()


        [ISBN, ISBN13] = get_ISBNs(response)
        item['ISBN'] = ISBN
        item['ISBN13'] = ISBN13

        ASIN = response.xpath('//div[contains(text(),"ASIN")]/parent::*[1]//div[2]//text()').get()
        item['ASIN'] = ASIN

        item['url'] = response.url

        date_time_collected = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        item['Date_Time_Collected'] = date_time_collected

        return item


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
    ISBN = response.xpath('//div[contains(text(),"ISBN")]/parent::*[1]//div[2]//text()').get()
    ISBN13 = response.xpath('//div[contains(text(),"ISBN")]/parent::*//span[@itemprop="isbn"]//text()').get()
    if ISBN:
        ISBN = ISBN.strip()
        if len(ISBN) == 9:
            ISBN = str(0) + str(ISBN)
        elif len(ISBN) == 13:
            ISBN13 = ISBN
        elif len(ISBN) != 10:
            ISBN = None

    if ISBN13:
        ISBN13 = ISBN13.strip()
        if len(ISBN13) == 10:
            ISBN = ISBN13
        elif len(ISBN13) == 9:
            ISBN = str(0) + ISBN13
        elif len(ISBN13) != 13:
            ISBN13 = None

    return [ISBN, ISBN13]

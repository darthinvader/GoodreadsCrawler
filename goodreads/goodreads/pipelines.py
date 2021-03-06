# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json


class JsonWriterPipeline(object):

    def open_spider(self, spider):
        self.file = open('books.json', 'a+')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        book = json.dumps(dict(item)) + "\n"
        self.file.write(book)
        return item

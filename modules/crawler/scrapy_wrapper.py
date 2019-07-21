#! python3
"""
Created on 15.06.2019

Several methods, structures and ideas in this wrapper are based on original code by Philipp Poschmann.
For the most part, this is the case in the GenericCrawlSpider and GenericCrawlPipeline classes.

@author: Maximilian Pensel
"""
import sys
import os
import shutil

import pandas as pd
import json
import traceback
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.crawler import CrawlerProcess
from urllib.parse import urlparse
from scrapy.settings import Settings
from langdetect.lang_detect_exception import LangDetectException
from langdetect import detect
import textract
from textract.exceptions import CommandLineError

from core.Workspace import WorkspaceManager
from modules.crawler import filemanager

ACCEPTED_LANG = ["de", "en"]  # will be dynamically set through the UI in the future

if len(sys.argv) >= 2:
    SETTINGS_PATH = sys.argv[1]
else:
    SETTINGS_PATH = None

DEBUG = False
if len(sys.argv) >= 3 and sys.argv[2] == "DEBUG":
    DEBUG = True


def parse_urls(url_filecontent: str):
    # preferably check every entry for a valid url
    return url_filecontent.splitlines()


def load_settings(settings_path):
    try:
        settings_file = open(settings_path, "r")
        settings = json.load(settings_file)
        print(settings)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc)
        return None

    return settings


class WebsiteParagraph(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    content = scrapy.Field()

    pass


def create_spider(settings):
    class GenericCrawlSpider(CrawlSpider):

        crawl_settings = settings

        name = 'generic_crawler'

        denied_extensions = ('mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai', 'drw',
                             'dxf', 'eps', 'ps', 'svg', 'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',
                             '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
                             'm4a', 'm4v', 'flv', 'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods',
                             'odg', 'odp', 'css', 'exe', 'bin', 'rss', 'zip', 'rar', 'gz', 'tar'
                             )

        start_urls = parse_urls(filemanager.get_url_content(crawl_settings["urls_file"]))
        allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))

        # p = re.compile("^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")
        rules = [
            # Rule(LinkExtractor(deny=r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")),
            Rule(LxmlLinkExtractor(  # deny=(r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?"),
                                     # deny=blacklistloader.load_blacklist(),  # Blacklist feature not yet implemented
                                    deny_extensions=denied_extensions), callback='parse_item', follow=True)
        ]

        def parse_item(self, response):
            print(response.url)

            ct = str(response.headers.get(b"Content-Type", "").lower())
            if "pdf" in ct:
                items = self.handle_pdf(response)
            else:
                items = self.handle_html(response)

            return items

        # ensure that start_urls are also parsed
        parse_start_url = parse_item

        def handle_html(self, response):
            items = []

            scraping_tags = ["p", "td"]

            for tag in scraping_tags:
                paragraphs = response.xpath("//"+tag)
                for par in paragraphs:
                    par_content = "".join(par.xpath(".//text()").extract())
                    items.extend(self.process_paragraph(response, par_content))

            return items

        def handle_pdf(self, response):
            # print("Warning: pdf not yet supported")
            filename = response.url.split('/')[-1]
            pdf_tmp_dir = os.path.join(GenericCrawlSpider.crawl_settings["workspace"],
                                       filemanager.running_crawl_settings_path,
                                       "PDF_TMP")
            txt_tmp_dir = os.path.join(GenericCrawlSpider.crawl_settings["workspace"],
                                       filemanager.running_crawl_settings_path,
                                       "TXT_TMP")
            if not os.path.exists(pdf_tmp_dir):
                os.makedirs(pdf_tmp_dir)
            filepath = os.path.join(pdf_tmp_dir, filename)

            with open(filepath, "wb") as pdffile:
                pdffile.write(response.body)

            try:
                content = textract.process(filepath)
            except CommandLineError as exc:  # Catching either ExtensionNotSupported or MissingFileError
                print(exc, file=sys.stderr)
                return []  # In any case, text extraction failed so no items were parsed

            global DEBUG  # fetch DEBUG flag
            if DEBUG:  # Only store intermediary .txt conversion of pdf in DEBUG mode
                if not os.path.exists(txt_tmp_dir):
                    os.makedirs(txt_tmp_dir)
                txt_name = filename.replace(".pdf", ".txt")
                with open(os.path.join(txt_tmp_dir, txt_name), "wb") as txt_file:
                    txt_file.write(content)

            content = content.decode("utf-8")  # convert byte string to utf-8 string
            items = []
            for par_content in content.splitlines():
                items.extend(self.process_paragraph(response, par_content))

            # Cleanup temporary pdf directory, unless in debug mode
            if not DEBUG:
                delete_path(pdf_tmp_dir)

            return items

        def process_paragraph(self, response, par_content):
            items = []

            if par_content.strip():  # immediately ignore empty or only whitespace paragraphs
                try:
                    lang = detect(par_content)
                    if lang in ACCEPTED_LANG:
                        items.append(self.make_scrapy_item(response.url, par_content))
                except LangDetectException as exc:
                    print("Error: {0} on langdetect input '{1}'. Being careful and storing the value anyway!"
                          .format(exc, par_content),
                          file=sys.stderr)
                    # Storing the value if language detection has failed. This behaviour remains to be evaluated.
                    # Of course repeating code is ugly, but language detection works the same with pdf and html,
                    # so being outsourced in the future anyway.
                    items.append(self.make_scrapy_item(response.url, par_content))

            return items

        @staticmethod
        def make_scrapy_item(url, content):
            item = WebsiteParagraph()
            item["url"] = url
            item["content"] = content
            return item

    return GenericCrawlSpider


class GenericCrawlPipeline(object):

    def process_item(self, item, spider):
        url = item['url']
        content = item['content']
        df_item = {"url": [url], "content": [content]}

        domain = urlparse(url).netloc
        if domain in spider.allowed_domains:
            print("Adding content for ", str(url), "to", str(domain))
            # self.dataframes[domain] = self.dataframes[domain].append(pd.DataFrame.from_dict(df_item))
            filemanager.add_to_csv(spider.crawl_settings["name"], domain, df_item)

        return item

    def open_spider(self, spider):
        filemanager.make_raw_data_path(spider.crawl_settings["name"])
        for domain in spider.allowed_domains:
            filemanager.create_csv(spider.crawl_settings["name"], domain, True)

    def close_spider(self, spider):
        for domain in spider.allowed_domains:
            filemanager.complete_csv(spider.crawl_settings["name"], domain)



class GenericCrawlSettings(Settings):

    def __init__(self):
        super().__init__(values={
            "ITEM_PIPELINES": {"scrapy_wrapper.GenericCrawlPipeline": 300},
            "DEPTH_LIMIT": 5,
            "FEED_EXPORT_ENCODING": "utf-8",
            "LOG_LEVEL": "WARNING",
            # "LOG_FILE": os.path.join(WorkspaceManager().get_workspace(), "logs", "scrapy.log")
            })


if SETTINGS_PATH is None:
    print("Error: no specification directory given. Call scrapy_wrapper.py as follows:\n" +
          "  python scrapy_wrapper.py <spec_dir> [DEBUG]\n" +
          "  <spec_dir> should contain a urls.txt and settings.json",
          file=sys.stderr)
    exit()


if __name__ == '__main__':
    crawl_settings = load_settings(SETTINGS_PATH)
    WorkspaceManager(crawl_settings["workspace"])  # Load it once, so that singleton is initialized to the correct workspace

    scrapy_settings = GenericCrawlSettings()

    process = CrawlerProcess(settings=scrapy_settings)
    process.crawl(create_spider(crawl_settings))
    try:
        process.start()
    except Exception as error:
        print("Warning: Don't worry, the crawl finished, strange error still fired for some reason.", error)

#! python3
"""
Created on 15.06.2019

Several methods, structures and ideas in this wrapper are based on original code by Philipp Poschmann.
For the most part, this is the case in the GenericCrawlSpider and GenericCrawlPipeline classes.

@author: Maximilian Pensel
"""
import sys
import os

if __name__ == '__main__':
    # make sure the project root is on the PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)))

import logging

import shutil
from logging import FileHandler, Formatter, StreamHandler

import pandas
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
from langdetect import DetectorFactory
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


def load_settings(settings_path):
    try:
        settings_file = open(settings_path, "r")
        settings = json.load(settings_file)
        print("Starting crawl with the following settings: {0}".format(settings))
    except Exception as exc:
        print(traceback.format_exc(), file=sys.stderr)
        print(exc, file=sys.stderr)
        return None

    return settings


class WebsiteParagraph(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    content = scrapy.Field()
    depth = scrapy.Field()

    pass


def create_spider(settings, start_url, crawler_name):
    class GenericCrawlSpider(CrawlSpider):

        crawl_settings = settings

        domain = urlparse(start_url).netloc

        # name = 'generic_crawler'
        name = crawler_name

        allowed_domains = [domain]

        start_urls = [start_url]

        denied_extensions = ('mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai', 'drw',
                             'dxf', 'eps', 'ps', 'svg', 'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',
                             '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
                             'm4a', 'm4v', 'flv', 'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods',
                             'odg', 'odp', 'css', 'exe', 'bin', 'rss', 'zip', 'rar', 'gz', 'tar'
                             )

        # start_urls = parse_urls(filemanager.get_url_content(crawl_settings["urls_file"]))
        # allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))

        # p = re.compile("^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")
        rules = [
            # Rule(LinkExtractor(deny=r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")),
            Rule(LxmlLinkExtractor(  # deny=(r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?"),
                                     # deny=blacklistloader.load_blacklist(),  # Blacklist feature not yet implemented
                                    allow=start_url+".*",  # crawl only links behind the given start-url
                                    deny_extensions=denied_extensions), callback='parse_item', follow=True)
        ]

        def __init__(self):
            super().__init__()
            # setup individual logger for every spider
            log_fmt = Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")

            log_fh = FileHandler(os.path.join(WorkspaceManager().get_workspace(), "logs", name + ".log"),
                                 mode="w")
            log_fh.setFormatter(log_fmt)
            log_fh.setLevel(logging.DEBUG)

            log_ch = StreamHandler(sys.stdout)
            log_ch.setLevel(logging.INFO)
            log_ch.setFormatter(log_fmt)

            self.logger.logger.addHandler(log_fh)
            self.logger.logger.addHandler(log_ch)
            self.logger.debug("[__init__] - Logger setup finished.")

            self.langdetect_stats = pandas.DataFrame(columns=["Paragraphs"])
            self.langdetect_stats.index.name = "Language"

        def parse_item(self, response):
            self.logger.info("[parse_item] - Processing {0}".format(response.url))

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

            scraping_paths = ["//p", "//td"]

            for xp in scraping_paths:
                paragraphs = response.xpath(xp)
                for par in paragraphs:
                    par_content = "".join(par.xpath(".//text()").extract())
                    items.extend(self.process_paragraph(response, par_content))

            return items

        def handle_pdf(self, response):
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
                self.logger.error(exc)
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
                filemanager.delete_and_clean(pdf_tmp_dir, ignore_empty=True)

            return items

        def process_paragraph(self, response, par_content):
            items = []

            if par_content.strip():  # immediately ignore empty or only whitespace paragraphs
                try:
                    lang = detect(par_content)
                    if lang in ACCEPTED_LANG:
                        items.append(self.make_scrapy_item(response.url, par_content, response.meta["depth"]))
                    if not self.langdetect_stats.index.contains(lang):
                        self.langdetect_stats.at[lang, "Paragraphs"] = 0
                    self.langdetect_stats.at[lang, "Paragraphs"] += 1
                except LangDetectException as exc:
                    pass
                    self.logger.error("[process_paragraph] - Error: "
                                      "{0} on langdetect input '{1}'. Being careful and storing the value anyway!"
                                      .format(exc, par_content))
                    # Storing the value if language detection has failed. This behaviour remains to be evaluated.
                    # Of course repeating code is ugly, but language detection works the same with pdf and html,
                    # so being outsourced in the future anyway.
                    items.append(self.make_scrapy_item(response.url, par_content, response.meta["depth"]))

                    if not self.langdetect_stats.index.contains("Not enough features"):
                        self.langdetect_stats.at["Not enough features", "Paragraphs"] = 0
                    self.langdetect_stats.at["Not enough features", "Paragraphs"] += 1

            return items

        @staticmethod
        def make_scrapy_item(url, content, depth):
            item = WebsiteParagraph()
            item["url"] = url
            item["content"] = content
            item["depth"] = depth
            return item

    return GenericCrawlSpider


class GenericCrawlPipeline(object):

    def process_item(self, item, spider):
        url = item['url']
        content = item['content']
        df_item = dict()
        for key in item:
            # df_item = {"url": [url], "content": [content]}
            df_item[key] = [item[key]]

        domain = urlparse(url).netloc
        if domain in spider.allowed_domains:
            spider.logger.info("[process_item] - Adding content for {0} to {1}".format(str(url), str(spider.name)))
            # self.dataframes[domain] = self.dataframes[domain].append(pd.DataFrame.from_dict(df_item))
            filemanager.add_to_csv(spider.crawl_settings["name"], spider.name, df_item)

        return item

    def open_spider(self, spider):
        filemanager.make_raw_data_path(spider.crawl_settings["name"])
        for domain in spider.allowed_domains:
            filemanager.create_csv(spider.crawl_settings["name"], spider.name, True)

    def close_spider(self, spider):
        for domain in spider.allowed_domains:
            filemanager.complete_csv(spider.crawl_settings["name"], spider.name)
            filemanager.save_dataframe(spider.crawl_settings["name"], "lang-" + spider.name, spider.langdetect_stats)


class GenericScrapySettings(Settings):

    def __init__(self):
        super().__init__(values={
            "ITEM_PIPELINES": {"scrapy_wrapper.GenericCrawlPipeline": 300},
            "DEPTH_LIMIT": 5,
            "FEED_EXPORT_ENCODING": "utf-8",
            "LOG_LEVEL": "WARNING",
            "DEPTH_PRIORITY": 1,
            "SCHEDULER_DISK_QUEUE": 'scrapy.squeues.PickleFifoDiskQueue',
            "SCHEDULER_MEMORY_QUEUE": 'scrapy.squeues.FifoMemoryQueue',
            "LOG_FILE": os.path.join(WorkspaceManager().get_workspace(), "logs", "scrapy.log")
            })


if SETTINGS_PATH is None:
    print("Error: no specification directory given. Call scrapy_wrapper.py as follows:\n" +
          "  python scrapy_wrapper.py <spec_dir> [DEBUG]\n" +
          "  <spec_dir> should contain a urls.txt and settings.json",
          file=sys.stderr)
    exit()


if __name__ == '__main__':
    # setup consistent language detection
    DetectorFactory.seed = 0

    crawl_settings = load_settings(SETTINGS_PATH)
    # Load the WorkspaceManager once, so that singleton is initialized to the correct workspace
    WorkspaceManager(crawl_settings["workspace"])

    if not DEBUG:
        sys.stdout = open(os.path.join(WorkspaceManager().get_workspace(), "logs", "scrapy.log"), 'a')
        sys.stderr = sys.stdout

    scrapy_settings = GenericScrapySettings()

    process = CrawlerProcess(settings=scrapy_settings)
    start_urls = list(set(crawl_settings["urls"]))
    allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))
    domain_name = len(start_urls) == len(set(allowed_domains))
    for url in start_urls:
        # find a better way for naming crawlers uniquely
        name = urlparse(url).netloc if domain_name else (urlparse(url).netloc + urlparse(url).path).replace("/", "_")
        process.crawl(create_spider(crawl_settings, url, name))
    try:
        process.start()
    except Exception as error:
        print(error, file=sys.stderr)

    # every spider finished, finalize crawl
    crawl_raw_dir = filemanager.get_crawl_raw_path(crawl_settings["name"])
    crawl_dir = filemanager.get_crawl_path(crawl_settings["name"])
    stats_df = pandas.DataFrame(columns=["paragraphs"])
    stats_df.index.name = "url"
    one_incomplete = False
    for csv in os.listdir(crawl_raw_dir):
        # As soon as there still is an incomplete file set one_incomplete = True
        one_incomplete = one_incomplete or filemanager.incomplete_flag in csv
        fullpath = os.path.join(crawl_raw_dir, csv)
        df = pandas.read_csv(fullpath, sep=None, engine="python")
        stats_df.at[csv.replace(".csv", ""), "paragraphs"] = df.count()["url"]

    filemanager.save_dataframe(crawl_settings["name"], "stats", stats_df)

    if not one_incomplete and not DEBUG:
        filemanager.finalize_crawl(crawl_settings["name"])

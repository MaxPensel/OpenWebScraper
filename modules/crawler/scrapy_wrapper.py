#! python3
"""
Created on 15.06.2019

Several methods, structures and ideas in this wrapper are based on original code by Philipp Poschmann.
For the most part, this is the case in the GenericCrawlSpider and GenericCrawlPipeline classes.

@author: Maximilian Pensel
"""
import logging
import sys
import os

from modules.crawler.model import CrawlSpecification

if __name__ == '__main__':
    # make sure the project root is on the PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)))

import shutil

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

import core
from core.Workspace import WorkspaceManager, LOG_DIR as WS_LOG_DIR
from modules.crawler import filemanager

ACCEPTED_LANG = ["de", "en"]  # will be dynamically set through the UI in the future
LANGSTATS_FILENAME = "languages"
LANGSTATS = pandas.DataFrame(columns=ACCEPTED_LANG)
LANGSTATS.index.name = "url"


if len(sys.argv) >= 2:
    SETTINGS_PATH = sys.argv[1]
else:
    SETTINGS_PATH = None

DEBUG = False
if len(sys.argv) >= 3 and sys.argv[2] == "DEBUG":
    DEBUG = True

if DEBUG:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

MLOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG, file_level=log_level)


def load_settings(settings_path) -> CrawlSpecification:
    try:
        settings_file = open(settings_path, "r")
        settings = CrawlSpecification()
        json_str = settings_file.read()
        settings.deserialize(json_str)
        MLOG.info("Starting crawl with the following settings: {0}".format(json_str))
    except Exception as exc:
        MLOG.exception("{0}: {1}".format(type(exc).__name__, exc))
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

        # start_urls = parse_urls(filemanager.get_url_content(crawl_settings.urls))
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
            self.s_log = core.simple_logger(modname="crawlspider",
                                            file_path=os.path.join(WorkspaceManager().get_workspace(),
                                                                   WS_LOG_DIR,
                                                                   self.crawl_settings.name,
                                                                   name + ".log")
                                            )
            for hand in self.s_log.handlers:
                self.logger.logger.addHandler(hand)
            self.s_log.info("[__init__] - Crawlspider logger setup finished.")

            # setup empty stats for accepted languages
            for lang in ACCEPTED_LANG:
                LANGSTATS.at[start_url, lang] = 0

        def parse_item(self, response):
            self.s_log.info("[parse_item] - Processing {0}".format(response.url))

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
            pdf_tmp_dir = os.path.join(GenericCrawlSpider.crawl_settings.workspace,
                                       filemanager.running_crawl_settings_dir,
                                       "PDF_TMP")
            txt_tmp_dir = os.path.join(GenericCrawlSpider.crawl_settings.workspace,
                                       filemanager.running_crawl_settings_dir,
                                       "TXT_TMP")
            if not os.path.exists(pdf_tmp_dir):
                os.makedirs(pdf_tmp_dir)
            filepath = os.path.join(pdf_tmp_dir, filename)

            with open(filepath, "wb") as pdffile:
                pdffile.write(response.body)

            try:
                content = textract.process(filepath)
            except CommandLineError as exc:  # Catching either ExtensionNotSupported or MissingFileError
                self.s_log.exception("[handle_pdf] - {0}: {1}".format(type(exc).__name__, exc))
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
                    self.register_paragraph_language(lang)
                except LangDetectException as exc:
                    self.s_log.error("[process_paragraph] - "
                                     "{0} on langdetect input '{1}'. Being careful and storing the value anyway!"
                                     .format(exc, par_content))
                    # Storing the value if language detection has failed. This behaviour remains to be evaluated.
                    # Of course repeating code is ugly, but language detection works the same with pdf and html,
                    # so being outsourced in the future anyway.
                    items.append(self.make_scrapy_item(response.url, par_content, response.meta["depth"]))
                    self.register_paragraph_language("Not enough features")

            return items

        @staticmethod
        def register_paragraph_language(lang):
            if lang not in LANGSTATS.columns:
                LANGSTATS.insert(len(LANGSTATS.columns), lang, 0, True)
            LANGSTATS.at[start_url, lang] += 1

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
            spider.s_log.info("[process_item] - Adding content for {0} to {1}".format(str(url), str(spider.name)))
            # self.dataframes[domain] = self.dataframes[domain].append(pd.DataFrame.from_dict(df_item))
            filemanager.add_to_csv(spider.crawl_settings.name, spider.name, df_item)

        return item

    def open_spider(self, spider):
        spider.s_log.info(" vvvvvvvvvvvvvvvvvvvvvvvvvvvv OPENING SPIDER {0} vvvvvvvvvvvvvvvvvvvvvvvvvvvv"
                          .format(spider.name))
        filemanager.make_raw_data_path(spider.crawl_settings.name)
        for domain in spider.allowed_domains:
            filemanager.create_csv(spider.crawl_settings.name, spider.name, True)

    def close_spider(self, spider):
        spider.s_log.info(" ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ CLOSING SPIDER {0} ^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
                          .format(spider.name))
        filemanager.complete_csv(spider.crawl_settings.name, spider.name)


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
            "ROBOTSTXT_OBEY": True
            })


if SETTINGS_PATH is None:
    MLOG.error("No crawl specification file given. Call scrapy_wrapper.py as follows:\n" +
               "  python scrapy_wrapper.py <spec_file> [DEBUG]\n" +
               "  <spec_file> should be a json that contains start urls, blacklist, workspace directory, etc.")
    exit()


if __name__ == '__main__':
    # setup consistent language detection
    DetectorFactory.seed = 0

    crawl_settings = load_settings(SETTINGS_PATH)
    # Load the WorkspaceManager once, so that singleton is initialized to the correct workspace
    WorkspaceManager(crawl_settings.workspace)

    scrapy_settings = GenericScrapySettings()
    crawl_log_path = os.path.join(WorkspaceManager().get_log_path(),
                                  crawl_settings.name)
    if not os.path.exists(crawl_log_path):
        os.makedirs(crawl_log_path, exist_ok=True)
    scrapy_log_path = os.path.join(crawl_log_path,
                                   "scrapy.log")

    scrapy_settings.set("LOG_FILE", scrapy_log_path)

    process = CrawlerProcess(settings=scrapy_settings)
    start_urls = list(set(crawl_settings.urls))
    allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))
    for url in start_urls:
        name = (urlparse(url).netloc + urlparse(url).path).replace("/", "_")
        process.crawl(create_spider(crawl_settings, url, name))
    try:
        process.start()
    except Exception as exc:
        MLOG.exception("{0}: {1}".format(type(exc).__name__, exc))

    # every spider finished, finalize crawl
    # save LANGSTATS
    filemanager.save_dataframe(crawl_settings.name, LANGSTATS_FILENAME, LANGSTATS)

    crawl_raw_dir = filemanager.get_crawl_raw_path(crawl_settings.name)
    crawl_dir = filemanager.get_crawl_path(crawl_settings.name)
    stats_df = pandas.DataFrame(columns=["total paragraphs", "unique paragraphs", "unique urls"])
    stats_df.index.name = "url"
    one_incomplete = False
    for csv in os.listdir(crawl_raw_dir):
        # As soon as there still is an incomplete file set one_incomplete = True
        one_incomplete = one_incomplete or filemanager.incomplete_flag in csv
        fullpath = os.path.join(crawl_raw_dir, csv)
        try:
            df = pandas.read_csv(fullpath, sep=None, engine="python")
            col = csv.replace(".csv", "")
            stats_df.at[col, "total paragraphs"] = df.count()["url"]
            if df.empty:
                stats_df.at[col, "unique paragraphs"] = 0
                stats_df.at[col, "unique urls"] = 0
            else:
                unique = df.nunique()
                stats_df.at[col, "unique paragraphs"] = unique["content"]
                stats_df.at[col, "unique urls"] = unique["url"]
        except Exception as exc:
            stats_df.at[csv.replace(".csv", ""), "total paragraphs"] = "Could not process"
            MLOG.exception("Error while analyzing results. {0}: {1}".format(type(exc).__name__, exc))

    filemanager.save_dataframe(crawl_settings.name, "stats", stats_df)

    if not one_incomplete and not DEBUG:
        filemanager.finalize_crawl(crawl_settings.name)

#! python3
"""
Created on 15.06.2019

Several methods, structures and ideas in this wrapper are based on original code by Philipp Poschmann.
For the most part, this is the case in the GenericCrawlSpider and GenericCrawlPipeline classes.

@author: Maximilian Pensel
"""
import importlib
import logging
import sys
import os

from modules.crawler.model import CrawlSpecification, CrawlMode

if __name__ == '__main__':
    # make sure the project root is on the PYTHONPATH
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir, os.pardir)))

import pandas
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.crawler import CrawlerProcess
from urllib.parse import urlparse
from scrapy.settings import Settings
from langdetect import DetectorFactory

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
    """
    Loads the json string in settings_path and deserializes to CrawlSpecification object.
    Determines required behaviour with respect to CrawlSpecification.mode.
    :param settings_path: file path to the json crawl specification file
    :return: parsed and semantically updated CrawlSpecification object
    """
    try:
        settings_file = open(settings_path, "r")
        settings = CrawlSpecification()
        json_str = settings_file.read()
        settings.deserialize(json_str)

        # Load the WorkspaceManager once, so that singleton is initialized to the correct workspace
        WorkspaceManager(settings.workspace)

        # determine behaviour w.r.t. mode
        if settings.mode == CrawlMode.NEW:
            filemanager.remove_crawl_content(settings.name)
        elif settings.mode == CrawlMode.CONTINUE:
            MLOG.info("Determining incomplete/non-existent data files to continue crawling.")
            datafiles = filemanager.get_datafiles(settings.name)
            run_with = list()
            for url in settings.urls:
                fname = filemanager.url2filename(url)
                if (fname + filemanager.incomplete_flag) in datafiles:
                    run_with.append(url)
                elif fname not in datafiles:
                    run_with.append(url)
            MLOG.info("Crawl continuation detected the following {0} out of {1} urls to be incomplete or missing: {2}"
                      .format(len(run_with), len(settings.urls), run_with))
            settings.update(urls=run_with)
        elif settings.mode == CrawlMode.RECRAWL_EMPTY:
            # load all datafiles, find empty dataframes and modify settings.url accordingly
            pass

        MLOG.info("Starting crawl with the following settings:\n{0}".format(settings.serialize()))
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
        # crawl_settings["parser"] = "modules.crawler.scrapy.parsers.ParagraphParser"
        # load parser locations from settings (?)
        parser_mod = importlib.import_module("modules.crawler.scrapy.parsers")
        parser_class = getattr(parser_mod, "ParagraphParser")  # instantiate parser, later depending on crawl_settings
        parser = parser_class(xpaths=crawl_settings.xpaths, keep_on_lang_error=True)

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
                                    deny_extensions=denied_extensions), callback=parser.parse, follow=True)
        ]

        # ensure that start_urls are also parsed
        parse_start_url = parser.parse

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

    return GenericCrawlSpider


class GenericScrapySettings(Settings):

    def __init__(self):
        super().__init__(values={
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

    if not crawl_settings:
        MLOG.error("Crawl settings could not be loaded. Exiting scrapy_wrapper.")
        sys.exit(1)

    scrapy_settings = GenericScrapySettings()
    crawl_log_path = os.path.join(WorkspaceManager().get_log_path(),
                                  crawl_settings.name)
    if not os.path.exists(crawl_log_path):
        os.makedirs(crawl_log_path, exist_ok=True)
    scrapy_log_path = os.path.join(crawl_log_path,
                                   "scrapy.log")

    scrapy_settings.set("ITEM_PIPELINES", crawl_settings.pipelines)
    scrapy_settings.set("LOG_FILE", scrapy_log_path)

    process = CrawlerProcess(settings=scrapy_settings)
    start_urls = list(set(crawl_settings.urls))
    allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))
    for url in start_urls:
        name = filemanager.url2filename(url)
        process.crawl(create_spider(crawl_settings, url, name))
    try:
        process.start()
    except Exception as exc:
        MLOG.exception("{0}: {1}".format(type(exc).__name__, exc))

    # every spider finished, finalize crawl
    # save LANGSTATS
    filemanager.save_dataframe(crawl_settings.name, LANGSTATS_FILENAME, LANGSTATS)

    stats_df = pandas.DataFrame(columns=["total paragraphs", "unique paragraphs", "unique urls"])
    stats_df.index.name = "url"
    one_incomplete = False
    for csv in filemanager.get_datafiles(crawl_settings.name):
        # As soon as there still is an incomplete file set one_incomplete = True
        one_incomplete = one_incomplete or filemanager.incomplete_flag in csv
        try:
            df = filemanager.load_crawl_data(crawl_settings.name, csv, convert=False)
            stats_df.at[csv, "total paragraphs"] = df.count()["url"]
            if df.empty:
                stats_df.at[csv, "unique paragraphs"] = 0
                stats_df.at[csv, "unique urls"] = 0
            else:
                unique = df.nunique()
                stats_df.at[csv, "unique paragraphs"] = unique["content"]
                stats_df.at[csv, "unique urls"] = unique["url"]
        except Exception as exc:
            stats_df.at[csv.replace(".csv", ""), "total paragraphs"] = "Could not process"
            MLOG.exception("Error while analyzing results. {0}: {1}".format(type(exc).__name__, exc))

    filemanager.save_dataframe(crawl_settings.name, "stats", stats_df)

    if not one_incomplete and not DEBUG:
        filemanager.finalize_crawl(crawl_settings.name)

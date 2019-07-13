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

ACCEPTED_LANG = ["de", "en"]  # will be dynamically set through the UI in the future

if len(sys.argv) >= 2:
    SPEC_DIR = sys.argv[1]
else:
    SPEC_DIR = None

DEBUG = False
if len(sys.argv) >= 3 and sys.argv[2] == "DEBUG":
    DEBUG = True


def load_urls(spec_dir):
    url_filename = "urls.txt"
    try:
        url_file = open(os.path.join(spec_dir, url_filename), "r")
        urls = []
        for line in url_file:
            urls.append(line)
        print(urls)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc)
        return None

    return urls


def load_settings(spec_dir):
    settings_filename = "settings.json"
    try:
        settings_file = open(os.path.join(spec_dir, settings_filename), "r")
        settings = json.load(settings_file)
        print(settings)
    except Exception as exc:
        print(traceback.format_exc())
        print(exc)
        return None

    return settings


def delete_path(path):
    # combination of the following three delete the full directory tree whose root is specified by path
    shutil.rmtree(path)
    os.makedirs(path)
    os.removedirs(path)


class WebsiteParagraph(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    content = scrapy.Field()

    pass


def create_spider(urls, settings):
    class GenericCrawlSpider(CrawlSpider):
        name = 'generic_crawler'

        denied_extensions = ('mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai', 'drw',
                             'dxf', 'eps', 'ps', 'svg', 'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',
                             '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
                             'm4a', 'm4v', 'flv', 'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods',
                             'odg', 'odp', 'css', 'exe', 'bin', 'rss', 'zip', 'rar', 'gz', 'tar'
                             )

        start_urls = urls
        allowed_domains = list(map(lambda x: urlparse(x).netloc, start_urls))

        run_settings = settings

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
            pdf_tmp_dir = os.path.join(self.run_settings["spec_dir"], "PDF_TMP")
            txt_tmp_dir = os.path.join(self.run_settings["spec_dir"], "TXT_TMP")
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
        if domain in self.dataframes:
            print("Adding content for ", str(url), "to", str(domain))
            self.dataframes[domain] = self.dataframes[domain].append(pd.DataFrame.from_dict(df_item))

        return item

    def open_spider(self, spider):
        self.dataframes = {}

        for domain in spider.allowed_domains:
            self.dataframes[domain] = pd.DataFrame(columns=["url", "content"])

    def close_spider(self, spider):
        output_dir = spider.run_settings["out_dir"]

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        errors = []

        for url in self.dataframes:
            try:
                filename = os.path.join(output_dir, url+".csv")
                print("Writing to", filename)
                self.dataframes[url].to_csv(filename, sep=";", index=False, encoding="utf-8")
            except Exception as exc:
                errors.append(exc)

        if not DEBUG:
            if len(errors) == 0:
                delete_path(spider.run_settings["spec_dir"])
            else:
                print("The following errors have been encountered during the finalisation of the crawl specified in {0}"
                      .format(spider.run_settings["spec_dir"]), file=sys.stderr)
                for exc in errors:
                    print(exc, file=sys.stderr)


class GenericCrawlSettings(Settings):

    def __init__(self):
        super().__init__(values={
            "ITEM_PIPELINES": {"scrapy_wrapper.GenericCrawlPipeline": 300},
            "DEPTH_LIMIT": 5,
            "FEED_EXPORT_ENCODING": "utf-8",
            "LOG_LEVEL": "WARNING"
            })


if SPEC_DIR is None:
    print("Error: no specification directory given. Call scrapy_wrapper.py as follows:\n" +
          "  python scrapy_wrapper.py <spec_dir> [DEBUG]\n" +
          "  <spec_dir> should contain a urls.txt and settings.json",
          file=sys.stderr)
    exit()

scrapy_settings = GenericCrawlSettings()

url_list = load_urls(SPEC_DIR)

run_settings = load_settings(SPEC_DIR)
run_settings["spec_dir"] = SPEC_DIR

process = CrawlerProcess(settings=scrapy_settings)
process.crawl(create_spider(url_list, run_settings))
try:
    process.start()
except Exception as error:
    print("Warning: Don't worry, the crawl finished, strange error still fired for some reason.", error)

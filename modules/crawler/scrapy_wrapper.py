#! python3
'''
Created on 15.06.2019

@author: Maximilian Pensel
'''
import sys
import os, shutil
import pandas as pd
import json
import traceback
import scrapy
from twisted.internet import reactor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.crawler import CrawlerProcess
from urllib.parse import urlparse
from scrapy.settings import Settings
from langdetect.lang_detect_exception import LangDetectException
from langdetect import detect
#import pdftextextraction
#from scrapy_crawl.spiders.crawlspider import GenericCrawlSpider

ACCEPTED_LANG = ["de", "en"] # will be dynamically set through the UI in the future

if len(sys.argv) >= 2:
    SPEC_DIR = sys.argv[1]
else:
    SPEC_DIR = None
    
DEBUG = False
if len(sys.argv) >= 3 and sys.argv[2] == "DEBUG":
    DEBUG = True

def load_urls(spec_dir):
    url_filename      = "urls.txt"
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

class WebsiteParagraph(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    content = scrapy.Field()
    
    pass


def handle_html(response):
    items = []
    paragraphs = response.xpath("//p")
    for par in paragraphs:
        par_content = "".join(par.xpath(".//text()").extract())
        if len(par_content) > 10:
            try:
                lang = detect(par_content)
                if lang in ACCEPTED_LANG:
                    item = WebsiteParagraph()
                    item['url'] = response.url
                    item['content'] = par_content
                    items.append(item)
            except LangDetectException:
                pass

    paragraphs = response.xpath("//td")
    for par in paragraphs:
        par_content = "".join(par.xpath(".//text()").extract())
        if len(par_content) > 10:
            try:
                lang = detect(par_content)
                if lang in ACCEPTED_LANG:
                    item = WebsiteParagraph()
                    item['url'] = response.url
                    item['content'] = par_content
                    items.append(item)
            except LangDetectException:
                pass
    return items


def handle_pdf(response):
    print("Warning: pdf not yet supported")
    items = []
#    pdf_paragraphs = pdftextextraction.extract_paragraphs(response.url)

#    if pdf_paragraphs is not None:
#        for par in pdf_paragraphs:
#            if len(par) > 10:
#                try:
#                    lang = detect(par)
#                    if lang in ACCEPTED_LANG:
#                        item = WebsiteParagraph()
#                        item['url'] = response.url.encode("utf-8")
#                        item['content'] = par
#                        items.append(item)
#                except LangDetectException:
#                    pass

    return items

def create_spider(urls, settings):
    class GenericCrawlSpider(CrawlSpider):
        name = 'generic_crawler'
    
        denied_extensions = ('mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg', 'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff', '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
        'm4a', 'm4v', 'flv', 'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg',
        'odp', 'css', 'exe', 'bin', 'rss', 'zip', 'rar', 'gz', 'tar', 'pdf' # only for now not accepting pdf
        )
   
        start_urls = urls
        allowed_domains = list(map(lambda x:urlparse(x).netloc, start_urls))
        
        run_settings = settings
        
        #p = re.compile("^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")
        rules = [
            #Rule(LinkExtractor(deny=r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")),
            Rule(LxmlLinkExtractor(#deny=(r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?"),
                               #deny=blacklistloader.load_blacklist(),
                               deny_extensions=denied_extensions), callback='parse_item', follow=True)
        ]
    
        def parse_item(self, response):
            print(response.url)
            items = []
            
            ct = str(response.headers.get(b"Content-Type", "").lower())
            if "pdf" in ct:
                items = handle_pdf(response)
            else:
                items = handle_html(response)
    
            return items
    
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
                # combination of the following three delete the current crawl_x directory as well as the "running" dir, in case this was the last crawl
                shutil.rmtree(spider.run_settings["spec_dir"])
                os.makedirs(spider.run_settings["spec_dir"])
                os.removedirs(spider.run_settings["spec_dir"])
            else:
                print("The following errors have been encountered during the finalisation of the crawl specified in {0}".format(spider.run_settings["spec_dir"]), file=sys.stderr)
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

if SPEC_DIR == None:
    print(
"""Error: no specification directory given. Call scrapy_wrapper as follows:
  python scrapy_wrapper.py <spec_dir>
<spec_dir> should contain a urls.txt and settings.json
""", file=sys.stderr)
    exit()

scrapy_settings = GenericCrawlSettings()

urls = load_urls(SPEC_DIR)

run_settings = load_settings(SPEC_DIR)
run_settings["spec_dir"] = SPEC_DIR

process = CrawlerProcess(settings=scrapy_settings)
process.crawl(create_spider(urls, run_settings))
try:
    process.start()
except Exception as exc:
    print("Warning: Don't worry, the crawl finished, strange error still fired for some reason.", exc)
'''
Created on 15.06.2019

@author: Maximilian Pensel
'''
import sys
import os
import pandas as pd
import subprocess
import traceback
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess
from urllib.parse import urlparse
from scrapy.settings import Settings
from langdetect.lang_detect_exception import LangDetectException
from langdetect import detect
#import pdftextextraction
#from scrapy_crawl.spiders.crawlspider import GenericCrawlSpider

if len(sys.argv) >= 2:
    dir = sys.argv[1]
else:
    dir = None

# temporary script for testing, this will be replaced by the call to scrapy
#command = ["python", "wait.py", "10", "2"]
#command = ["scrapy", "crawl", "generic_crawler"]

#try:
#    subprocess.call(command)
#
#    if not dir is None:
#        os.removedirs(dir)
#except Exception as exc:
#    print(traceback.format_exc())
#    print(exc)

ACCEPTED_LANG = ["de", "en"]

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


#def handle_pdf(response):
#    items = []
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

#    return items

class GenericCrawlSpider(CrawlSpider):
    name = 'generic_crawler'

    denied_extensions = ('mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif', 'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg', 'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff', '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a', 'm4v', 'flv', 'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg',
    'odp', 'css', 'exe', 'bin', 'rss', 'zip', 'rar', 'gz', 'tar',
    'pdf' # only for now not accepting pdf
    )
    
    

    #allowed_domains = urlloader.load_domains()
    #start_urls = ["https://lat.inf.tu-dresden.de/quantla/"]
    start_urls = ["http://bertablock.de/"]
    allowed_domains = list(map(lambda x:urlparse(x).netloc, start_urls))
    print("allowed domains: {0}".format(str(allowed_domains)))

    #start_urls = urlloader.load_urls()
    print("urls: {0}".format(str(start_urls)))

    #p = re.compile("^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")
    rules = [
        #Rule(LinkExtractor(deny=r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?")),
        Rule(LinkExtractor(#deny=(r"^https://www.glashuette-original.com/(fr|it|es|zh-hans|ja)(/.*)?"),
                           #deny=blacklistloader.load_blacklist(),
                           deny_extensions=denied_extensions), callback='parse_item', follow=True)
    ]

    def parse_item(self, response):
        print(response.url)
        items = []

        #ct = response.headers.get("content-type", "").lower()
        #if "pdf" in ct:
        #    items = handle_pdf(response)
        #else:
        items = handle_html(response)

        return items

class GenericCrawlPipeline(object):
    
    def process_item(self, item, spider):
        #print("PROCESSING ITEM IN PIPELINE:", str(item))
        #line = json.dumps(dict(item), ensure_ascii=False).encode("utf8") + "\n"
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
        CRAWLED_DIR = "running/crawl_0/"
        
        for url in self.dataframes:
            filename = os.path.join(CRAWLED_DIR, url+".csv")
            print("Writing to", filename)
            self.dataframes[url].to_csv(filename, sep=";", index=False, encoding="utf-8")


class GenericCrawlSettings(Settings):

    def __init__(self):
        super().__init__(values={
            "ITEM_PIPELINES": {"scrapy_wrapper.GenericCrawlPipeline": 300},
            "DEPTH_LIMIT": 5,
            "FEED_EXPORT_ENCODING": "utf-8",
            "LOG_LEVEL": "WARNING"
            })

settings = GenericCrawlSettings()

process = CrawlerProcess(settings=settings)
process.crawl(GenericCrawlSpider)
process.start()
import os
from urllib.parse import urlparse

import pandas

import core
from core.Workspace import WorkspaceManager
from modules.crawler import filemanager
from modules.crawler.model import CrawlSpecification

###
# Crawl Finalizers
###


class CrawlFinalizer:

    def __init__(self, spec: CrawlSpecification):
        self.crawl_specification = spec

    def finalize_crawl(self, data: {} = None):
        pass


class LocalCrawlFinalizer(CrawlFinalizer):
    LANGSTATS_ID = "languages"

    def __init__(self, spec: CrawlSpecification, settings: {}):
        super().__init__(spec)
        self.log = core.simple_logger("LocalCrawlFinalizer", file_path=os.path.join(WorkspaceManager().get_log_path(),
                                                                                    self.crawl_specification.name,
                                                                                    "scrapy.log"))

    def finalize_crawl(self, data: {} = None):
        if data is None:
            data = dict()

        if LocalCrawlFinalizer.LANGSTATS_ID in data:
            # save LANGSTATS
            self.log.info("Saving language statistics to ")
            filemanager.save_dataframe(self.crawl_specification.name,
                                       LocalCrawlFinalizer.LANGSTATS_ID,
                                       data[LocalCrawlFinalizer.LANGSTATS_ID])

        stats_df = pandas.DataFrame(columns=["total paragraphs", "unique paragraphs", "unique urls"])
        stats_df.index.name = "url"
        one_incomplete = False
        for csv in filemanager.get_datafiles(self.crawl_specification.name):
            # As soon as there still is an incomplete file set one_incomplete = True
            one_incomplete = one_incomplete or filemanager.incomplete_flag in csv
            try:
                df = filemanager.load_crawl_data(self.crawl_specification.name, csv, convert=False)
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
                self.log.exception("Error while analyzing results. {0}: {1}".format(type(exc).__name__, exc))

        filemanager.save_dataframe(self.crawl_specification.name, "stats", stats_df)

        if not one_incomplete:  # and not DEBUG:
            filemanager.move_crawl_specification(self.crawl_specification.name)


class RemoteCrawlFinalizer(CrawlFinalizer):

    def __init__(self, spec: CrawlSpecification, settings: {}):
        super().__init__(spec)
        self.log = core.simple_logger("LocalCrawlFinalizer", file_path=os.path.join(WorkspaceManager().get_log_path(),
                                                                                    self.crawl_specification.name,
                                                                                    "scrapy.log"))

    def finalize_crawl(self, data: {} = None):
        if data is None:
            data = dict()
    # TODO: this method is automatically called after the entire crawl has finished, gather the crawl results from
    #       the workspace (using filemanager) and compose an http request for further processing


###
# Pipelines
###

class Paragraph2WorkspacePipeline(object):


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
            filemanager.add_to_csv(spider.crawl_specification.name, spider.name, df_item)

        return item

    def open_spider(self, spider):
        spider.s_log.info(" vvvvvvvvvvvvvvvvvvvvvvvvvvvv OPENING SPIDER {0} vvvvvvvvvvvvvvvvvvvvvvvvvvvv"
                          .format(spider.name))
        filemanager.make_raw_data_path(spider.crawl_specification.name)
        for domain in spider.allowed_domains:
            filemanager.create_csv(spider.crawl_specification.name, spider.name, True)

    def close_spider(self, spider):
        spider.s_log.info(" ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ CLOSING SPIDER {0} ^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
                          .format(spider.name))
        filemanager.complete_csv(spider.crawl_specification.name, spider.name)

"""
Created on 24.09.2019

@author: Maximilian Pensel

Copyright 2019 Maximilian Pensel <maximilian.pensel@gmx.de>

This file is part of OpenWebScraper.

OpenWebScraper is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenWebScraper is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenWebScraper.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import shutil
from urllib.parse import urlparse

import pandas
import math
import numpy as np

import core
from core.Workspace import WorkspaceManager
from modules.crawler import filemanager
from modules.crawler.model import CrawlSpecification

from modules.crawler.remote.result_producer import send_result

###
# Crawl Finalizers
###


class CrawlFinalizer:

    def __init__(self, spec: CrawlSpecification):
        self.crawl_specification = spec

    def finalize_crawl(self, data: {} = None):
        pass


class LocalCrawlFinalizer(CrawlFinalizer):
    LANGSTATS_ID = "allowed_languages"

    def __init__(self, spec: CrawlSpecification, settings: {}):
        super().__init__(spec)
        self.log = core.simple_logger("LocalCrawlFinalizer", file_path=os.path.join(WorkspaceManager().get_log_path(),
                                                                                    self.crawl_specification.name,
                                                                                    "scrapy.log"))

    def finalize_crawl(self, data: {} = None):
        self.log.info("Finalizing crawl ...")
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

        self.log.info("Done finalizing crawl.")


def get_filename_from_path(filepath):
    """Extract filename from filepath.

    Split path into "path", "extension".
    Then split path into elements and extract last one
    """
    return os.path.splitext(filepath)[0].split("/")[-1]


class RemoteCrawlFinalizer(CrawlFinalizer):

    def __init__(self, spec: CrawlSpecification, settings: {}):
        super().__init__(spec)
        self.log = core.simple_logger("RemoteCrawlFinalizer", file_path=os.path.join(WorkspaceManager().get_log_path(),
                                                                                     self.crawl_specification.name,
                                                                                     "scrapy.log"))

    def finalize_crawl(self, data: {} = None):
        self.log.info("Finalizing crawl ...")

        # maximum size for message chunk (100 MB)
        max_message_size = 104857600

        if data is None:
            data = dict()

        # TODO: this method is automatically called after the entire crawl has finished, gather the crawl results from
        #       the workspace (using filemanager) and compose an http request for further processing

        # fetching crawl results
        log_path = os.path.join(WorkspaceManager().get_log_path())
        for csv_filepath in filemanager.get_datafiles(self.crawl_specification.name, abspath=True):
            # get filename
            filename = get_filename_from_path(csv_filepath)
            # initialize data
            data['crawl'] = self.crawl_specification.name
            data['filename'] = filename
            # # read log file
            # log_filepath = os.path.join(log_path, self.crawl_specification.name, filename)
            # if "INCOMPLETE" not in log_path:
            #     with open("{}.log".format(log_filepath), mode="r", encoding="utf-8") as logfile:
            #         log_content = logfile.read()
            #         data['log'] = log_content

            # read df
            df = pandas.read_csv(csv_filepath, sep=';', quotechar='"', encoding="utf-8")
            # self.log.info(df)
            # get filesize to estimate number of required messages
            result_size = os.path.getsize(csv_filepath)
            self.log.info("Result size: {}".format(result_size))

            # split df into chunks if size is larger than max_message_size
            if result_size > max_message_size:
                self.log.info("Multiple messages required!")
                # number of required chunks
                chunk_count =  math.ceil(result_size / max_message_size)
                chunks = np.array_split(df, chunk_count)
                #self.log.info(chunks)
                # send all chunks to queue
                for index, chunk in enumerate(chunks):
                    #self.log.info(chunk)
                    filename_part = "{}_part{}".format(filename, index)
                    data['filename'] = filename_part
                    data['data'] = chunk.to_csv(index=False, sep=';')
                    #self.log.info(data['data'])
                    send_flag = send_result(data)
            # send complete dictionary
            else:
                self.log.info("One message required!")
                data['data'] = df.to_csv(index=False, sep=';')
                #self.log.info(data['data'])
                send_flag = send_result(data)

            # with open(csv_filepath, mode="r", encoding="utf-8") as csv_file:
            #     csv_content = csv_file.read()
            #     # TODO: add this content to a dict in order to compose http request
            #     filename = get_filename_from_path(csv_filepath)
            #     data[filename] = csv_content

        # fetching log contents
        # log_path = os.path.join(WorkspaceManager().get_log_path(), self.crawl_specification.name)
        # self.log.info(log_path)
        # for log_filename in os.listdir(log_path):
        #     log_filepath = os.path.join(log_path, log_filename)
        #     self.log.info(log_filepath)
        #     with open(log_filepath, mode="r", encoding="utf-8") as logfile:
        #         log_content = logfile.read()
        #         self.log.info(log_content)
                # TODO: add this content to a dict in order to compose http request


        self.log.info("Clearing data directory.")
        data_path = filemanager._get_data_path()
        shutil.rmtree(data_path, ignore_errors=True)

        self.log.info("Clearing log directory.")
        shutil.rmtree(log_path, ignore_errors=True)
        # clear logger files if not deleted
        log_path = os.path.join(WorkspaceManager().get_log_path(), self.crawl_specification.name)
        for log_filename in os.listdir(log_path):
            with open(os.path.join(log_path, log_filename) , "w") as text_file:
                text_file.write("")

        # self.log.info("Clearing specification.")
        # os.remove(filemanager.get_running_specification_path(self.crawl_specification.name))

        self.log.info("Done finalizing crawl.")

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

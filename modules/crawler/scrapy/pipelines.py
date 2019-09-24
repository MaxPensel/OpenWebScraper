from urllib.parse import urlparse

from modules.crawler import filemanager


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
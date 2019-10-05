""""
Created on 29.08.2019

@author: Maximilian Pensel
"""

import validators

import core

TITLE = "Crawler"
MAIN_WIDGET = "modules.crawler.view.CrawlerWidget"
VERSION = "0.2.0 <beta>"
LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)

INITIALIZER_WIDGETS = {"Local Workspace Initializer": "modules.crawler.ui.initializers.local.LocalCrawlView",
                       "Message Queue Initializer": "modules.crawler.ui.initializers.msgqueue.MessageQueueCrawlView"}
INITIALIZER_DEFAULT = "Local Workspace Initializer"

PARSER_WIDGETS = {"Paragraph Parser": "modules.crawler.ui.parsers.paragraph.ParagraphParserSettingsView"}
PARSER_DEFAULT = "Paragraph Parser"


def detect_valid_urls(urls_in):
    lines = 0
    invalid = list()
    urls = list()
    for line in urls_in:
        if line:
            lines += 1
            validator_result = validators.url(line)
            if not validator_result:
                invalid.append(line)
            else:
                urls.append(line)
    return lines, invalid, urls


class WindowsCreationFlags:
    DETACHED_PROCESS = 0x00000008

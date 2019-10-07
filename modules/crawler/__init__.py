""""
Created on 29.08.2019

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
along with OpenWebScraper.  If not, see <https://www.gnu.org/licenses/>."""

import validators

import core

TITLE = "Crawler"
MAIN_WIDGET = "modules.crawler.view.CrawlerWidget"
VERSION = "0.4.0 <beta>"
COPYRIGHT = "2019 Maximilian Pensel"
LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)

INITIALIZER_WIDGETS = {"Local Workspace Initializer": "modules.crawler.ui.initializers.local.LocalCrawlView",
                       "Remote HTTP Initializer": "modules.crawler.ui.initializers.httpremote.HttpRemoteCrawlView"}
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

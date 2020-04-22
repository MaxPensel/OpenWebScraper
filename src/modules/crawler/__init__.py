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

import os
import validators
import core
import toml

from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS["general"]["master_log"])

MOD_PATH = os.path.join(APP_SETTINGS["modloader"]["mod_dir"], "crawler")


def load_settings():
    return toml.load(os.path.join(MOD_PATH, "settings.toml"))


SETTINGS = load_settings()


def init(main_window):
    main_window.register_settings("Crawler", os.path.join(MOD_PATH, "settings.toml"))
    LOG.info("Finished initialization.")


def detect_valid_urls(urls_in):
    lines = 0
    invalid = list()
    urls = list()
    for line in urls_in:
        if line and not line.startswith("#"):  # ignore empty lines and comments
            lines += 1
            validator_result = validators.url(line)
            if not validator_result:
                invalid.append(line)
            else:
                urls.append(line)
    return lines, invalid, urls


def compile_invalid_html(urls):
    invalid_html = "The following is a list of lines that have not been recognized as a valid url " \
                   "by the url validator. This could be because they syntactically do not form a valid " \
                   "url-string or they are not responding to an http-request or the http-request is " \
                   "being redirected to another url (other reasons might be possible).<br />" \
                   "Consider opening the following urls in your browser to verify the problems yourself." \
                   "<ul>"
    for inv in urls:
        invalid_html += "<li><a href='{0}'>{0}</a></li>".format(inv)
    invalid_html += "</ul>"
    return invalid_html


class WindowsCreationFlags:
    DETACHED_PROCESS = 0x00000008

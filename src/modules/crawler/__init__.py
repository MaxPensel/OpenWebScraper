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
from simple_settings import LazySettings
from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS.general["master_log"])

SETTINGS = LazySettings(os.path.join(LazySettings("settings.toml").modloader["mod_dir"], "crawler", "settings.toml"))


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


class WindowsCreationFlags:
    DETACHED_PROCESS = 0x00000008

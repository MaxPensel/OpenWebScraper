""""
Created on 22.04.2020

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

import core
import toml
from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="analyzer", file_path=APP_SETTINGS["general"]["master_log"])

MOD_PATH = os.path.join(APP_SETTINGS["modloader"]["mod_dir"], "analyzer")

SETTINGS = toml.load(os.path.join(MOD_PATH, "settings.toml"))

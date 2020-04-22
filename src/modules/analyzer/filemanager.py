"""
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
from modules.crawler import filemanager as crawler_files
from modules.analyzer import SETTINGS
import pandas as pd

__PANDAS_READ_PARS = dict(
    sep=";",
    engine="python",
    encoding="utf-8"
)

__PANDAS_WRITE_PARS = dict(
    sep=";",
    encoding="utf-8"
)


def _get_stats_path(crawlname):
    crawl_path = crawler_files.get_crawl_path(crawlname)
    return os.path.join(crawl_path, SETTINGS["files"]["stats_filename"])


def get_stats(crawlname):
    """ Return pandas.DataFrame if analysis exists, None otherwise. """
    stats_path = _get_stats_path(crawlname)
    print("checking " + stats_path)
    if not os.path.exists(stats_path):
        return None
    return pd.read_csv(stats_path, **__PANDAS_READ_PARS)


def save_stats(crawlname, stats_df):
    stats_path = _get_stats_path(crawlname)
    stats_df.to_csv(stats_path, **__PANDAS_WRITE_PARS)
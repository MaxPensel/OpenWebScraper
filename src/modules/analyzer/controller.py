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
import threading

import pandas as pd
from PyQt5.QtWidgets import QAbstractScrollArea
from qtpy import QtCore

from core import ViewController
from core.QtExtensions import saturate_combobox, SimpleYesNoMessage
from modules.analyzer.model import PandasModel
from modules.crawler import SETTINGS as CRAWLER_SETTINGS
from modules.crawler import filemanager as crawler_files
from modules.analyzer import filemanager as analyzer_files, LOG


def get_paragraph_crawls():
    return crawler_files.get_crawlnames(filt=lambda name: len(crawler_files.get_datafiles(name)) > 0)


class AnalyzerController(ViewController):

    def __init__(self, view):
        super().__init__(view)

        self.crawls = get_paragraph_crawls()

        self.init_elements()
        self.setup_behavior()

    def init_elements(self):
        saturate_combobox(self._view.crawl_selector, self.crawls, True)

        self._view.stat_generator.setEnabled(False)
        self._view.analyzing_feedback_label.setVisible(False)
        self._view.analysis_progress_bar.setVisible(False)

        self.update_view()

    def setup_behavior(self):
        self._view.crawl_selector.currentIndexChanged.connect(self.select_crawl)

        self._view.stat_generator.clicked.connect(self.generate_analysis)

        self._view.stats_view.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

    def update_view(self):
        if get_paragraph_crawls() != self.crawls:
            self.crawls = crawler_files.get_crawlnames()
            cur_selec = self._view.crawl_selector.currentText()
            saturate_combobox(self._view.crawl_selector, self.crawls, True)
            self._view.crawl_selector.setCurrentIndex(self._view.crawl_selector.findText(cur_selec, QtCore.Qt.MatchFixedString))

    def select_crawl(self):
        """ Check if there are already statistics and offer to create statistics """
        crawlname = self._view.crawl_selector.currentText()

        if crawlname == "":
            self._view.stat_generator.setEnabled(False)
            self._view.stats_view.setModel(None)
            return

        self._view.stat_generator.setEnabled(True)
        df = analyzer_files.get_stats(crawlname)
        if isinstance(df, pd.DataFrame):
            self.show_data(df)
        else:
            self._view.stats_view.setModel(None)

    def show_data(self, df):
        try:
            self._view.stats_view.setModel(PandasModel(df))
            self._view.stats_view.resizeColumnsToContents()
        except Exception as err:
            LOG.exception(err)

    def start_analysis_mode(self):
        self._view.crawl_selector.setEnabled(False)
        self._view.stat_generator.setEnabled(False)

        self._view.analyzing_feedback_label.setVisible(True)

        self._view.analysis_progress_bar.setValue(0)
        self._view.analysis_progress_bar.setVisible(True)

    def set_analysis_progress(self, progress):
        LOG.debug(f"Setting progress to {progress}")
        self._view.analysis_progress_bar.setValue(progress)

    def stop_analysis_mode(self):
        self._view.crawl_selector.setEnabled(True)
        self._view.stat_generator.setEnabled(True)

        self._view.analyzing_feedback_label.setVisible(False)
        self._view.analysis_progress_bar.setVisible(False)

    def generate_analysis(self):
        crawlname = self._view.crawl_selector.currentText()
        df_stats = analyzer_files.get_stats(crawlname)
        if df_stats is not None:
            msg = SimpleYesNoMessage("Recreate Analysis?", f"The crawl '{crawlname}' was already analyzed. "
                                                           "Do you wish to recreate the analysis?")
            if not msg.is_confirmed():
                return

        # Generate the actual analysis:
        self.start_analysis_mode()
        thread = threading.Thread(target=self._generate_analysis_thread, args=[crawlname])
        thread.start()

    def _generate_analysis_thread(self, crawlname):
        data_files = crawler_files.get_datafiles(crawlname)
        LOG.info(f"Analyzing {len(data_files)} data-files for {crawlname}: {data_files}")
        stats = pd.DataFrame(columns=["URL", "Paragraphs", "Unique Paragraphs", "Words", "Words in Unique Paragraphs"])
        tracker = AnalysisProgressTracker(len(data_files)*5, lambda tr: self.set_analysis_progress(tr.rate))
        for file in data_files:
            data = crawler_files.load_crawl_data(crawlname, file, convert=False)
            tracker.step()  # done loading
            if "content" in data.columns:
                data["words"] = data["content"].apply(lambda par: len(str(par).split()))
                tracker.step()  # done calculating words
                data_unique = data.drop_duplicates()
                n_pars = len(data)
                n_unique_pars = data["content"].nunique()
                n_words = sum(data["words"])
                n_words_unique = sum(data_unique["words"])
                new_row = pd.DataFrame([{"URL": crawler_files.filename2url(file),
                                         "Paragraphs": n_pars,
                                         "Unique Paragraphs": n_unique_pars,
                                         "Words": n_words,
                                         "Words in Unique Paragraphs": n_words_unique}])
                stats = stats.append(new_row)
            else:
                LOG.warning(f"{file}.csv is not in the expected format ('content' column missing).")

            tracker.step()  # done processing data file
        stats = stats.set_index("URL")

        # Analyze log files
        log_files = list(filter(lambda lf: not lf.startswith("scrapy"), crawler_files.get_logfiles(crawlname)))
        LOG.info(f"Analyzing {len(log_files)} log-files for {crawlname}: {log_files}")
        try:
            logstats = pd.DataFrame()
            for fname in log_files:
                log_content = crawler_files.get_log_content(crawlname, fname)
                tracker.step()  # done loading
                counts = dict()
                counts["URL"] = fname
                counts["Warnings"] = 0
                counts["Forbidden by robots.txt"] = 0

                for line in log_content.splitlines():
                    if "WARNING" in line:
                        counts["Warnings"] += 1

                        if "WARNING - Not allowed:" in line:
                            reason = line.split(" // ")[1].strip()
                            if reason not in counts:
                                counts[reason] = 0
                            counts[reason] += 1
                        elif "Forbidden by robots.txt" in line:
                            counts["Forbidden by robots.txt"] += 1
                        elif "No features in text." in line:
                            if not "Langdetect Error" in counts:
                                counts["Langdetect Error"] = 0
                            counts["Langdetect Error"] += 1

                logstats = pd.concat([logstats, pd.DataFrame([counts])], sort=False)

                tracker.step()  # done processing log file

            logstats = logstats.set_index("URL").fillna(0)
            logstats.index = stats.index.str.replace(".log", "").str.replace("_", "/")
            logstats.index = stats.index.map(
                lambda idx: idx if idx in stats.index else idx + CRAWLER_SETTINGS["filemanager"]["incomplete_flag"])
            # logstats.index = stats.index.str.replace(CRAWLER_SETTINGS["filemanager"]["incomplete_flag"], "")
            # print(stats.info())
            # print(logstats.info())
            stats = pd.concat([stats, logstats], axis=1).fillna(0).astype(int)
        except Exception as err:
            LOG.exception(err)

        analyzer_files.save_stats(crawlname, stats)
        LOG.info(f"Done analyzing {crawlname}, saved.")
        self.show_data(stats.reset_index())
        self.stop_analysis_mode()

class AnalysisProgressTracker:

    def __init__(self, total, callback=None):
        self.total = total
        self.done = 0
        self.callback = callback

        self.__update_rate()

    def step(self):
        self.done += 1
        self.__update_rate()
        if self.callback:
            self.callback(self)

    def __update_rate(self):
        self.rate = (self.done/self.total) * 100

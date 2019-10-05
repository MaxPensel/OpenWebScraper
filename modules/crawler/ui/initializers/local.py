"""
Created on 02.10.2019

@author: Maximilian Pensel
"""
import os
import subprocess
import sys

from PyQt5.QtWidgets import QWidget, QComboBox, QPushButton, QVBoxLayout, QGroupBox, QLineEdit, QHBoxLayout, QMessageBox

import core
from core.QtExtensions import saturate_combobox, SimpleErrorInfo, SimpleYesNoMessage, SimpleMessageBox, \
    HorizontalContainer
from crawlUI import Settings
from modules.crawler import filemanager, WindowsCreationFlags, detect_valid_urls
from modules.crawler.controller import CrawlerController
from modules.crawler.model import CrawlSpecification

LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)


class LocalCrawlView(HorizontalContainer):

    def __init__(self):
        super().__init__()
        # ### Different options for initiating a crawl

        # reload previous crawl
        self.prev_crawl_combobox = QComboBox()
        self.prev_crawl_load = QPushButton("Load Crawl Settings")

        prev_crawl_layout = QVBoxLayout()
        prev_crawl_layout.addWidget(self.prev_crawl_combobox)
        prev_crawl_layout.addWidget(self.prev_crawl_load)

        self.prev_crawl_groupbox = QGroupBox("Load Previous Crawl")
        self.prev_crawl_groupbox.setLayout(prev_crawl_layout)

        # continue unfinished crawl
        self.continue_crawl_combobox = QComboBox()
        self.continue_crawl_button = QPushButton("Continue Crawl")

        continue_crawl_layout = QVBoxLayout()
        continue_crawl_layout.addWidget(self.continue_crawl_combobox)
        continue_crawl_layout.addWidget(self.continue_crawl_button)

        continue_crawl_groupbox = QGroupBox("Continue Unfinished Crawl")
        continue_crawl_groupbox.setLayout(continue_crawl_layout)

        # new crawl
        self.crawl_name_input = QLineEdit()
        self.crawl_name_input.setPlaceholderText("Crawl name")

        self.crawl_button = QPushButton("Start New Crawl")

        new_crawl_layout = QVBoxLayout()
        new_crawl_layout.addWidget(self.crawl_name_input)
        new_crawl_layout.addWidget(self.crawl_button)

        new_crawl_input_group = QGroupBox("New Crawl")
        new_crawl_input_group.setLayout(new_crawl_layout)

        # put together crawl starting options
        self.addWidget(self.prev_crawl_groupbox)
        self.addWidget(continue_crawl_groupbox)
        self.addWidget(new_crawl_input_group)

        self.cnt = LocalCrawlController(self)


class LocalCrawlController(core.ViewController):

    def __init__(self, view: LocalCrawlView):
        super().__init__(view)
        self.master_cnt = None
        self.resettables.extend([view.prev_crawl_combobox,
                                view.continue_crawl_combobox,
                                view.crawl_name_input])

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """

        self._view.continue_crawl_combobox.setInsertPolicy(QComboBox.InsertAlphabetically)
        saturate_combobox(self._view.continue_crawl_combobox, filemanager.get_running_crawls())

        self._view.prev_crawl_groupbox.setDisabled(True)

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """
        self._view.continue_crawl_button.clicked.connect(self.continue_crawl)
        self._view.crawl_button.clicked.connect(self.start_crawl)

        # trigger model updates
        if self.master_cnt:
            self._view.crawl_name_input.textChanged.connect(self.master_cnt.update_model)
        else:
            self._view.crawl_name_input.textChanged.connect(self.update_model)

        self._view.continue_crawl_combobox.currentIndexChanged.connect(self.select_unfinished_crawl)

    def update_model(self):
        if self.master_cnt:
            self.master_cnt.crawl_specification.update(name=self._view.crawl_name_input.displayText())

    def update_view(self):
        self._view.crawl_name_input.setText(self.master_cnt.crawl_specification.name)

    def select_unfinished_crawl(self):
        # load crawl
        settings_filename = self._view.continue_crawl_combobox.currentText()
        if settings_filename:
            self.master_cnt.crawl_specification = filemanager.load_running_crawl_settings(settings_filename)
            self.reset_view(do_not=[self._view.continue_crawl_combobox])
            self.master_cnt.reset_view()
            if self.master_cnt:
                self.master_cnt.update_view()
            else:
                self.update_view()

    def continue_crawl(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification

        if self._view.continue_crawl_combobox.currentIndex() == 0:
            msg = SimpleErrorInfo("Error", "No crawl selected for continuation.")
            msg.exec()
            LOG.error("No crawl selected for continuation.")
            return
        msg = SimpleMessageBox("Attention",
                               "Are you sure that the crawl '{0}' is not running anymore?"
                               .format(spec.name),
                               details="Check your task manager (or Alt+Tab) for any console-type windows, perhaps "
                                       "your crawl is still being executed. If you are sure that the process has "
                                       "stopped, you can continue it now.",
                               icon=QMessageBox.Warning)
        cont = msg.addButton("Continue Crawl", QMessageBox.ActionRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()
        pressed = msg.clickedButton()
        if pressed == cont:
            LOG.info("Setting up to continue an unfinished crawl ...")

            LOG.info("Determining incomplete urls in crawl {0}".format(spec.name))
            incomplete = filemanager.get_incomplete_urls(spec.name, spec.urls)
            LOG.info("Found {0} out of {1} incomplete urls: {2}".format(len(incomplete), len(spec.urls), incomplete))
            spec.update(urls=incomplete)

            filemanager.save_crawl_settings(spec.name, spec)

            settings_path = filemanager.get_running_specification_path(spec.name)

            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)
            self._view.continue_crawl_combobox.removeItem(self._view.continue_crawl_combobox.currentIndex())
            self.update_view()

    def start_crawl(self):
        LOG.info("Pre-flight checks for starting a new crawl ...")
        if not self.master_cnt.crawl_specification.name:
            msg = SimpleErrorInfo("Error", "Your crawl must have a name.")
            msg.exec()
            return

        if self.master_cnt.crawl_specification.name in filemanager.get_running_crawls():
            msg = SimpleMessageBox("Warning",
                                   "There is still an unfinished crawl by the name '{0}'."
                                   .format(self.master_cnt.crawl_specification.name),
                                   details="It is recommended to use a different name. If you are sure that this "
                                           "crawl is not running anymore you can also fully restart it with its "
                                           "original settings or use the continue crawl feature.",
                                   icon=QMessageBox.Warning)
            restart = msg.addButton("Restart Crawl", QMessageBox.ActionRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec()
            pressed = msg.clickedButton()
            if pressed == restart:
                settings_path = self.setup_crawl(continue_crawl=True)
            else:
                return
        else:
            lines, invalid, urls = detect_valid_urls(self.master_cnt.crawl_specification.urls)
            if invalid:
                invalid_html = "The following is a list of lines that have not been recognized as a valid url " \
                               "by the url validator. This could be because they syntactically do not form a valid " \
                               "url-string or they are not responding to an http-request or the http-request is " \
                               "being redirected to another url (other reasons might be possible).<br />" \
                               "Consider opening the following urls in your browser to verify the problems yourself." \
                               "<ul>"
                for inv in invalid:
                    invalid_html += "<li><a href='{0}'>{0}</a></li>".format(inv)
                invalid_html += "</ul>"
                if lines == len(invalid) or len(urls) == 0:
                    msg = SimpleErrorInfo("Error", "<b>No valid urls given.</b>", details=invalid_html)
                    msg.exec()
                    return

                msg = SimpleYesNoMessage("Warning", "<b>{0} out of {1} non-empty lines contain invalid urls.</b>"
                                                    .format(len(invalid), lines),
                                                    "{0}"
                                                    "<b>Do you wish to start the crawl with the remaining "
                                                    "{1} valid urls?</b>"
                                                    .format(invalid_html, lines-len(invalid)))

                if not msg.is_confirmed():
                    return
                # else: update specification to use only valid urls and start the crawl
                self.master_cnt.crawl_specification.update(urls=urls)

            settings_path = self.setup_crawl()

        if not settings_path:
            msg = SimpleErrorInfo("Error", "Crawl setup encountered an error. Not starting crawl.")
            msg.exec()
            return
        if settings_path is not None:
            LOG.info("Starting new crawl with settings in file {0}".format(settings_path))
            start_scrapy(settings_path)
        else:
            LOG.error("Something went wrong it crawl specification setup. Not starting scrapy!")

    def setup_crawl(self, continue_crawl=False):
        spec = self.master_cnt.crawl_specification

        if continue_crawl:
            # check if running specification exists, if so, return its path
            if spec.name not in filemanager.get_running_crawls():
                LOG.error("Cannot continue crawl '{0}', no running specification found."
                          .format(spec.name))
                return None
            else:
                return filemanager.get_running_specification_path(spec.name)
        else:
            # setup parser and finalizers; for now this setup is fixed, should be UI configurable in the future
            spec.update(parser="modules.crawler.scrapy.parsers.ParagraphParser",
                        parser_data={"xpaths": ["//p", "//td"],
                                     "keep_on_lang_error": False},
                        pipelines={"modules.crawler.scrapy.pipelines.Paragraph2WorkspacePipeline": 300},
                        finalizers={"modules.crawler.scrapy.pipelines.LocalCrawlFinalizer": {}})
            if spec.name in filemanager.get_crawlnames():
                msg = SimpleYesNoMessage("Continue?",
                                         "There is already data for a crawl by the name '{0}'. Continue anyway?"
                                         .format(spec.name))
                if not msg.is_confirmed():
                    return None

            return filemanager.save_crawl_settings(spec.name, spec)


def start_scrapy(settings_path):
    python_exe = os.path.abspath(Settings().python)
    LOG.info("Running scrapy_wrapper.py with {0}".format(python_exe))
    try:
        if os.name == "nt":  # include the creation flag DETACHED_PROCESS for calls in windows
            subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd="modules/crawler/",
                             creationflags=WindowsCreationFlags.DETACHED_PROCESS)
        else:
            subprocess.Popen(python_exe + " scrapy_wrapper.py \"" + settings_path + "\"",
                             stdout=sys.stdout,
                             shell=True,
                             start_new_session=True,
                             cwd="modules/crawler/",
                             close_fds=True)
    except Exception as exc:
        LOG.exception("{0}: {1}".format(type(exc).__name__, exc))

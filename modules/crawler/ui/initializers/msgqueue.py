import os

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QGroupBox
import core
from core.QtExtensions import HorizontalContainer, SimpleErrorInfo
from modules.crawler.controller import CrawlerController


class MessageQueueCrawlView(HorizontalContainer):

    def __init__(self):
        super().__init__()

        # setup queue
        queue_label = QLabel("Set the message queue location:")

        self.queue_input = QLineEdit()
        self.queue_input.setPlaceholderText("e.g. http://example.com/crawler_queue")

        queue_layout = QVBoxLayout()
        queue_layout.addWidget(queue_label)
        queue_layout.addWidget(self.queue_input)

        queue_input_group = QGroupBox("Message Queue Setup")
        queue_input_group.setLayout(queue_layout)

        # new crawl
        self.crawl_name_input = QLineEdit()
        self.crawl_name_input.setPlaceholderText("Crawl name")

        self.crawl_button = QPushButton("Send to Queue")

        new_crawl_layout = QVBoxLayout()
        new_crawl_layout.addWidget(self.crawl_name_input)
        new_crawl_layout.addWidget(self.crawl_button)

        new_crawl_input_group = QGroupBox("New Crawl")
        new_crawl_input_group.setLayout(new_crawl_layout)

        # put together crawl starting options
        self.addWidget(queue_input_group)
        self.addWidget(new_crawl_input_group)

        self.cnt = MessageQueueController(self)


class MessageQueueController(core.ViewController):

    def __init__(self, view: MessageQueueCrawlView):
        super().__init__(view)

        self.master_cnt = None
        self.resettables.extend([self._view.crawl_name_input])

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        # TODO: perhaps initialize self._view.queue_input to some default message queue location
        #  e.g. self._view.queue_input.setText("DEFAULT_URI")
        pass

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        self._view.crawl_button.clicked.connect(self.send_to_queue)

        # trigger model updates
        if self.master_cnt:
            self._view.crawl_name_input.textChanged.connect(self.master_cnt.update_model)
        else:
            self._view.crawl_name_input.textChanged.connect(self.update_model)

    def update_model(self):
        if self.master_cnt:
            self.master_cnt.crawl_specification.update(name=self._view.crawl_name_input.displayText())

    def update_view(self):
        self._view.crawl_name_input.setText(self.master_cnt.crawl_specification.name)

    def send_to_queue(self):
        """
        Creates and sends an appropriate json crawl specification to the specified message queue.
        Perhaps it should send one specification per start url.
        :return:
        """
        # do some specific crawl specification setup
        self.master_cnt.crawl_specification.update(
            # make workspace relative, because scrapy_wrapper is not being executed on THIS system
            workspace=os.path.join("..", "..", "default_workspace"),
            pipelines={"modules.crawler.scrapy.pipelines.Paragraph2WorkspacePipeline": 300},  # keep this too (?!)
            # extend finalizers by one that retrieves the crawl results and sends them away
            finalizers={"modules.crawler.scrapy.pipelines.LocalCrawlFinalizer": {},
                        "modules.crawler.scrapy.pipelines.RemoteCrawlFinalizer": {}}  # <---- implement this

        )

        queue_location = self._view.queue_input.displayText()

        json_text = self.master_cnt.crawl_specification.serialize()

        SimpleErrorInfo("Feature not yet implemented",
                        "Sending crawl specifications to a message queue "
                        "has not yet been implemented, please be patient.").exec()

        # TODO: create http request with specification json (json_text)
        #  and send it to the specified message queue location (queue_location)

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

from core import ViewController
from modules.crawler.controller import CrawlerController


class ParagraphParserSettingsView(QWidget):

    def __init__(self):
        super().__init__()

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(QLabel("Paragraph Parser Settings Area"))

        self.cnt = ParagraphParserSettingsController(self)


class ParagraphParserSettingsController(ViewController):

    def __init__(self, view):
        super().__init__(view)
        self.master_cnt = None
        self.resettables.extend([])

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        pass

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """
        pass

    def update_model(self):
        pass

    def update_view(self):
        pass
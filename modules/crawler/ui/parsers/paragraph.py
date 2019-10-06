from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QCheckBox, QGroupBox, QVBoxLayout, QPlainTextEdit

from core import ViewController
from core.QtExtensions import HorizontalContainer
from modules.crawler.controller import CrawlerController
from modules.crawler.model import CrawlSpecification
from modules.crawler.scrapy.parsers import ParagraphParser


class ParagraphParserSettingsView(HorizontalContainer):

    def __init__(self):
        super().__init__()

        # langdetect behavior
        self.keep_langdetect_errors = QCheckBox("Keep paragraphs on langdetect errors")
        langdetect_behavior_group = QGroupBox("Langdetect Behavior")
        langdetect_behavior_group.setLayout(QVBoxLayout())
        langdetect_behavior_group.layout().addWidget(self.keep_langdetect_errors)

        # language selection
        self.lang_checks = dict()
        self.lang_area = QGroupBox("Languages to Crawl")
        self.lang_area.setLayout(QVBoxLayout())


        # xpath selection
        self.xpath_area = QPlainTextEdit()
        xpath_group = QGroupBox("XPath Expressions")
        xpath_group.setLayout(QVBoxLayout())
        xpath_group.layout().addWidget(self.xpath_area)

        self.addWidget(langdetect_behavior_group)
        self.addWidget(self.lang_area)
        self.addWidget(xpath_group)

        self.cnt = ParagraphParserSettingsController(self)


class ParagraphParserSettingsController(ViewController):

    def __init__(self, view):
        super().__init__(view)
        self.master_cnt = None
        self.resettables.extend([])

        # this is for the ui, default is given from modules.crawler.scrapy.parsers.ParagraphParser
        self.allowed_languages = {"de": "German",
                                  "en": "English"}

        self.init_elements()

        self.setup_behaviour()

    def register_master_cnt(self, master_controller: CrawlerController):
        self.master_cnt = master_controller
        self.update_model()

    def init_elements(self):
        """ Sets up the initial state of the elements

        This could determine the enabled state of a button, default values for text areas, etc.
        Should not further adjust layouts or labels!
        """
        # setup allowed languages
        for lang in sorted(self.allowed_languages, key=self.allowed_languages.get):
            self._view.lang_checks[lang] = QCheckBox(self.allowed_languages[lang])
            if lang in ParagraphParser.DEFAULT_ALLOWED_LANGUAGES:
                self._view.lang_checks[lang].setChecked(True)
            self._view.lang_area.layout().addWidget(self._view.lang_checks[lang])

        # setup default xpath expressions
        self._view.xpath_area.setPlainText("\n".join(ParagraphParser.DEFAULT_XPATHS))

    def setup_behaviour(self):
        """ Setup the behaviour of elements

        This includes all functionality of state changes for primitive widgets.
        Should not initialise default state, use init_elements() for that.
        """

        # trigger model updates
        self._view.keep_langdetect_errors.clicked.connect(self.update_model)
        self._view.xpath_area.textChanged.connect(self.update_model)
        for lang in self.allowed_languages:
            self._view.lang_checks[lang].clicked.connect(self.update_model)

    def update_model(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification
        data = {
            ParagraphParser.KEY_KEEP_LANGDETECT_ERRORS: self._view.keep_langdetect_errors.isChecked(),
            ParagraphParser.KEY_LANGUAGES:
                [lang for lang in self.allowed_languages if self._view.lang_checks[lang].isChecked()],
            ParagraphParser.KEY_XPATHS: self._view.xpath_area.toPlainText().splitlines()
        }
        spec.update(parser="modules.crawler.scrapy.parsers.ParagraphParser",
                    parser_data=data)
        pass

    def update_view(self):
        spec = self.master_cnt.crawl_specification  # type: CrawlSpecification

        self._view.keep_langdetect_errors.setChecked(
            ParagraphParser.KEY_KEEP_LANGDETECT_ERRORS in spec.parser_data and
            spec.parser_data[ParagraphParser.KEY_KEEP_LANGDETECT_ERRORS])

        for lang in self.allowed_languages:
            self._view.lang_checks[lang].setChecked(
                ParagraphParser.KEY_LANGUAGES in spec.parser_data and
                lang in spec.parser_data[ParagraphParser.KEY_LANGUAGES]
            )

        if ParagraphParser.KEY_XPATHS in spec.parser_data:
            self._view.xpath_area.setPlainText(
                "\n".join(spec.parser_data[ParagraphParser.KEY_XPATHS])
            )
        else:
            self._view.xpath_area.setPlainText()



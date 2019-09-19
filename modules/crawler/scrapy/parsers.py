import logging
import os
import tempfile

import textract
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from scrapy import Item, Field
from textract.exceptions import CommandLineError


class ResponseParser:

    def __init__(self, callbacks=None, spider=None):
        if callbacks is None:
            callbacks = dict()
        self.callbacks = callbacks
        self.spider = spider

    def parse(self, response):
        content_type = str(response.headers.get(b"Content-Type", "").lower())
        for ctype in self.callbacks:
            if ctype in content_type:
                return self.callbacks[ctype](response)

        self.log(logging.WARN, "No callback found to parse content type '{0}'".format(content_type))

    def log(self, level, message):
        if self.spider:
            self.spider.s_log.log(level, message)
        else:
            print("[{0}] {1}".format(level, message))


class ParagraphParser(ResponseParser):

    def __init__(self, xpaths=None, accepted_languages=None, keep_on_lang_error=False, spider=None):
        super().__init__(spider)

        # set defaults
        if xpaths is None:
            xpaths = list()
        if accepted_languages is None:
            accepted_languages = ["de", "en"]

        self.callbacks["text/html"] = self.parse_html
        self.callbacks["application/pdf"] = self.parse_pdf

        self.xpaths = xpaths
        self.accepted_languages = accepted_languages
        self.keep_on_lang_error = keep_on_lang_error
        self.detected_languages = dict()

    def parse_html(self, response):
        items = []

        for xp in self.xpaths:
            paragraphs = response.xpath(xp)
            for par in paragraphs:
                par_content = "".join(par.xpath(".//text()").extract())
                items.extend(self.process_paragraph(response, par_content))

        return items

    def parse_pdf(self, response):
        tmp_file = tempfile.TemporaryFile(suffix=".pdf", prefix="scrapy_", delete=False)
        tmp_file.write(response.body)
        tmp_file.close()
        try:
            content = textract.process(tmp_file.name)
        except CommandLineError as exc:  # Catching either ExtensionNotSupported or MissingFileError
            self.log(logging.ERROR, "[parse_pdf] - {0}: {1}".format(type(exc).__name__, exc))
            return []  # In any case, text extraction failed so no items were parsed

        content = content.decode("utf-8")  # convert byte string to utf-8 string
        items = []
        for par_content in content.splitlines():
            items.extend(self.process_paragraph(response, par_content))

        # Cleanup temporary pdf file
        os.unlink(tmp_file.name)

        return items

    def process_paragraph(self, response, par_content):
        items = []

        if par_content.strip():  # immediately ignore empty or only whitespace paragraphs
            try:
                lang = detect(par_content)
                if lang in self.accepted_languages:
                    items.append(ParagraphItem(url=response.url, content=par_content, depth=response.meta["depth"]))
                self.register_paragraph_language(lang)
            except LangDetectException as exc:
                if self.keep_on_lang_error:
                    self.log(logging.WARN, "[process_paragraph] - "
                                           "{0} on langdetect input '{1}'. You chose to store the content anyway!"
                                           .format(exc, par_content))
                    items.append(ParagraphItem(url=response.url, content=par_content, depth=response.meta["depth"]))
                    self.register_paragraph_language(str(exc))

        return items

    def register_paragraph_language(self, lang):
        if lang not in self.detected_languages:
            self.detected_languages[lang] = 0
        self.detected_languages[lang] += 1


###
# Scrapy item definitions
###

class ParagraphItem(Item):
    url = Field()
    content = Field()
    depth = Field()


class RawContentItem(Item):
    url = Field()
    content = Field()
    depth = Field()

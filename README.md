# SpiderGUI

This is a simple modular graphical endpoint for the [Scrapy](https://scrapy.org/) python web-crawler library.
It allows to issue crawls with a basic list of urls and prefix-blacklist.
It also supports several post-processing and analytical features that are heavily based on [pandas](http://pandas.pydata.org/).
The GUI and its features are specifically tailored to the german DFG research project ["Die Konstruktion organisationaler Identität und der Einfluss von Geschichte"](http://gepris.dfg.de/gepris/projekt/398074981?context=projekt&task=showDetail&id=398074981&) at the [TU Ilmenau](https://www.tu-ilmenau.de/).

# Remarks

This software is still in early development. It is primarily developed with windows users in mind.
Seeing as python, PyQt5, etc. are platform independend, it should run on unix-based systems as well, although this is not extensively tested yet.

As a user, if you encounter any bugs or unexpected behaviour, please report them through github issues.
A simple in-app documentation is still planned to 
As a developer, be aware that some of the design choices may not be fully incorporated at every level yet.
There is some code documentation, but as is to be expected of an early development stage, it is most likely insufficient to fully understand everything.
Feel free to contact me with specific questions

# Installation

The installation process might be simplified in the future, for now, several steps need to be taken.
A Python3.7 environment is required and it is recommended to obtain this through Anaconda.
1. Install [Anaconda](https://www.anaconda.com/distribution/#download-section) with python3.7.
2. Download and install Visual Studio Buildtools [here](https://visualstudio.microsoft.com/de/downloads/). (Scroll down a bit, you'll find tools for visual studio 2019, download the Buildtools)
3. Get the SpiderGUI sources.
..* Either Download [master.zip](https://github.com/MaxPensel/SpiderGUI/archive/master.zip) and unpack in your chosen installation directory.
__OR__
..* Install git and clone this repository. (This method is recommended to easily stay up to date with the development)
```ShellSession
git clone git@github.com:MaxPensel/SpiderGUI.git
```
4. Open up the anaconda prompt and navigate to your installation directory. Execute 
```ShellSession
pip install -r requirements.txt
```

# Documentation

This is a preliminary documentation about the code structure and some module interactions.
First of all, the main UI (user interface) is a modular platform. The core loads the modules that are present in the ```modules``` directory and activated in the ```settings.ini```. Each module contains a main PyQt5 Widget that represents its view component. Each main widget appears as a new tab in the core UI.
There is a well documented template module that contains further information on how to implement new modules.

## Module: Crawler

For the crawler module, there are two main components, the PyQt5 UI (the main widget of the crawler module), and a wrapper script executing the scrapy crawling process (scrapy_wrapper.py).
The main widget adheres to a model view controller (MVC) structure. The view is used to configure all parameters that specify a single run of the scrapy wrapper script. The controller generates this specification in the form of a .json file and executes the scrapy wrapper script.

The scrapy_wrapper is standalone in the sense that it takes a run specification json file as input, to determine what urls to crawl, how to process responses, where to store retrieved data, etc. (see [specification.json]).
Components such as the parsing of incoming http-responses and further processing of the parsed data (in pipelines) can be specified in the run specification, in order to keep extensibility of the scrapy wrapper as high as possible.

![scrapy wrapper component overview](doc/img/scrapy_wrapper_layout.svg "scrapy_wrapper Components")

## specification.json



```
{
    "blacklist": [
         "http://www.example.com/do-not-crawl-this"
    ],
    "mode": "new",
    "name": "test scrapy pipeline",
    "pipelines": {
        "modules.crawler.scrapy.pipelines.Paragraph2WorkspacePipeline": 300
    },
    "urls": [
        "http://www.example.com/start-crawling-this",
        "http://www.example.com/start-crawling-that"
    ],
    "workspace": "C:\\Path\\To\\A\\Local\\Workspace",
    "xpaths": [
        "//p",
        "//td"
    ]
}
```

* _blacklist_: contains a list of url strings, acts as a prefix-blacklist, i.e. urls starting with any of the here specified strings will not be crawled
* _mode_: currently allows for the values "new" and "continue", soon will allow to "recrawl_empty". Right now the mode parameter influences the list of urls to crawl, based on already existing data in the local workspace. Soon this feature will be exclusive for using the local workspace, i.e. when introducing other pipelines it is not clear how to determine scrapy's behaviour based on the given mode.
* _name_: The name of the crawl.
* _pipelines_: Specifies the scrapy pipelines setting, see the [scrapy documentation](https://docs.scrapy.org/en/latest/topics/item-pipeline.html)
* _urls_: contains a list of url strings, these will be the start urls, a single scrapy crawlspider is started for each given url
* _workspace_: For now, the workspace setting is linked together with the _mode_. Soon, these options will be deferred to the pipeline setting.
* _xpaths_: contains a list of xpath expressions to fetch paragraphs from. This specification will be exclusive to "paragraph-extracting" kind of parsers.
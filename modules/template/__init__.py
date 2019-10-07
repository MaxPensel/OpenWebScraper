""""
Use this as a cheat sheet for setting up new modules.
Modules are contained in the 'modules' directory, one folder per module, consisting of at least the __init__.py file.

Required fields:
 - MAIN_WIDGET must be assigned a class extending the QWidget class

Optional fields:
 - TITLE:str will be the title of the tab in the core UI, defaults to module descriptor (i.e. directory name)

Created on 27.08.2019

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

TITLE = "Template"
MAIN_WIDGET = "modules.template.view.TemplateWidget"
VERSION = "1.1.1"
COPYRIGHT = "2019 Maximilian Pensel"

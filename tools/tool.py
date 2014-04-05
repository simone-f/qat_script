#! /usr/bin/env jython
#
#  Copyright 2014 Simone F. <groppo8@gmail.com>
#
#  This file is part of qat_script.
#  qat_script is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

""" Define quality assurance tools properties.
    Tools: OSM Inspector, KeepRight, Errori OSM Italia Grp.
"""

#java import
from javax.swing import ImageIcon
from java.io import IOException, File
from java.net import URL, UnknownHostException, SocketException
from java.util import Locale, ResourceBundle
from java.net import URLClassLoader


class Tool():
    def __init__(self, app):
        #name: reference code for this tool used for exmaple in 'config.cfg'
        self.name = self.title.lower().replace(" ", "_")
        if self.name in app.toolsStatus:
            self.isActive = app.toolsStatus[self.name]
        else:
            self.isActive = True

        #localization
        if self.isTranslated:
            localeDir = File.separator.join([self.app.SCRIPTDIR,
                                             "tools",
                                             "data",
                                             self.title.replace(" ", ""),
                                             "locale"])
            urls = [File(localeDir).toURI().toURL()]
            loader = URLClassLoader(urls)
            currentLocale = Locale.getDefault()
            self.strings = ResourceBundle.getBundle("MessagesBundle",
                                                     currentLocale,
                                                     loader)
            if self.name == "favourites":
                self.title = self.strings.getString("Favourites")

        if self.name == "favourites":
            ref = "Favourites"
        else:
            ref = self.title.replace(" ", "")
        self.bigIcon = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                                      "tools",
                                                      "data",
                                                      ref,
                                                      "icons",
                                                      "tool_24.png"]))
        self.smallIcon = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                                        "tools",
                                                        "data",
                                                        ref,
                                                        "icons",
                                                        "tool_16.png"]))

        if not hasattr(self, "isLocal") or not self.isLocal:
            self.isLocal = False

        if self.name in app.toolsPrefs:
            self.update_preferences()

        self.views = []
        for viewName, checksList in self.toolInfo.iteritems():
            self.views.append(View(app, self, viewName, checksList))

    def update_preferences(self):
        self.prefs = self.app.toolsPrefs[self.name]

    def reportToToolServer(self, url):
        """Tell to the tool server when an error is fixed (user clicked
           on correctedBtn) or false positive (falsePositiveBtn).
           Tool instance must have either:
           self.fixedFeedbackMode = "url"
           self.falseFeedbackMode = "url"
        """
        try:
            url = URL(url)
            uc = url.openConnection()
            uc.getInputStream()
            uc.disconnect()
        except (UnknownHostException, IOException, SocketException):
            print url
            print "* I can't connect to the tool server."


class View():
    """A category with similar checks.
       For example: routing, tagging, roundabouts...
    """
    def __init__(self, app, tool, viewName, checksList):
        self.tool = tool

        #name and title
        self.name = viewName
        if self.tool.isTranslated:
            self.title = self.tool.strings.getString("w_%s" % self.name.lower().replace(" ", "_"))
        else:
            self.title = self.name

        self.checks = []
        for checkInfo in checksList:
            self.checks.append(Check(app, tool, self, checkInfo))


class Check():
    """A check.
       For example: disconnected highways, duplicate nodes...
    """
    def __init__(self, app, tool, view, (title, name, url, icon, marker)):
        self.tool = tool
        self.view = view

        #name and title
        if self.tool.isLocal:
            self.title = self.tool.title
            self.name = self.tool.name
            self.helpUrl = ""
        else:
            self.name = name
            if self.tool.isTranslated:
                self.title = self.tool.strings.getString("c_%s" % name)
            else:
                self.title = title
            self.helpUrl = self.tool.help_url(self)

        self.url = url

        if icon == "":
            self.icon = None
        else:
            self.icon = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                                       "tools",
                                                       "data",
                                                       self.tool.title.replace(" ", ""),
                                                       "icons",
                                                       "checks",
                                                       "%s.png" % icon]))
        if marker == "":
            self.marker = None
        else:
            self.marker = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                                         "tools",
                                                         "data",
                                                         self.tool.title.replace(" ", ""),
                                                         "icons",
                                                         "checks",
                                                         "%s.png" % marker]))

        self.bbox = None

        #self.currentErrorIndex = index of error currently being corrected in dialog
        self.currentErrorIndex = -1
        #self.reviewedIds, list of ids of objects that have been checked (by pressing the next button)
        self.reviewedIds = []
        #List of ids of OSM object that the user don't know how to correct
        #and that he/she doesn't want to see
        self.ignoreIds = []
        #List of errors instances of this type of check
        self.errors = None
        #Number of errors that must be checked
        self.toDo = None


class Error():
    """An error, an OSM primitive.
       For example: a specific node, with OSM id 123, bbox [1,2,3,4],
       belonging to the tool X as error ab123
    """
    def __init__(self, check, errorInfo):
        self.check = check
        (osmId, (lat, lon), bbox, errorId, desc, other) = errorInfo
        self.osmId = osmId
        self.bbox = bbox
        self.coords = (lat, lon)
        self.user = None    # it will be filled after error download and selection
        self.errorId = errorId
        self.url = None    # calculated with tool.error_url(error) when error info dialog is opened
        self.desc = desc
        self.other = other
        self.done = False

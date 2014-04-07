#! /usr/bin/env jython
# -*- coding: utf-8 -*-

"""
This is a fake tool that may be used as a teplate to add a new QA Tool to QATs
"""

# tool  : Housenumbervalidator
# author: Markus "Gulp21"
# webpage  : http://gulp21.bplaced.net/osm/housenumbervalidator/

from java.lang import Thread
from ...tool import Tool


class HousenumbervalidatorTool(Tool):
    def __init__(self, app):
        self.app = app

        #Tool name
        self.title = "Housenumbervalidator"

        #Tool url
        self.uri = "http://gulp21.bplaced.net/osm/housenumbervalidator/"
        #url: web site of the tool

        #Translations
        self.isTranslated = False
        #the translations for a tool are in tool directory/locale

        #Additional preferences for this tool
        self.prefsGui = None
        #There are additional preferences for this tool. See Osmose for example

        #Corrected errors
        self.fixedFeedbackMode = "url"
        #"url": the user can automatically report to the tool admin that an error has been corrected
        #(by clicking correctedBtn --> self.sayBugFixed())
        #None: the user cannot automatically report to the tool admin when an error has been corrected:

        #False positives
        self.falseFeedbackMode = "url"
        #"url": the user can automatically report to the tool admin that an error is not an error
        #(by clicking fixeddBtn --> self.sayFalseBug())
        #msg: the user can report manually, e.g. by e-mail, to the tool admin that an error is not an error:
        #In this case, when the user clicks on the "Not an error" button, the current error information
        #are collected and shown under the menu "QA Tools" --> "False positive",
        #so that the user can copy them and send the info manually to the tool admin.

        #Tool checks
        #... are listed in toolInfo and grouped in categories (called views)
        #(like "Tagging", "Routing..."), which are used to create submenus and
        #comboboxes in JOSM.
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "Duplicates": [
                           ["Dupes (very close)", "10", "0", "pin_pink", "pin_pink"],
                           ["Dupes (exact)", "11", "1", "pin_red", "pin_red"],
                           ["Dupes (similar)", "12", "2", "pin_blue", "pin_blue"]
                          ],
            "Problematic": [
                            ["Broken (easy)", "20", "0", "pin_circle_red", "pin_circle_red"],
                            ["Broken (difficult)", "21", "1", "pin_circle_blue", "pin_circle_blue"]
                           ]}
        Tool.__init__(self, app)

        #if there is not an icon for a check in 'tool directory/icons/checks/check name' a red dot is used.

    #MANDATORY
    def download_urls(self, (zoneBbox, checks)):
        """This method accepts a list of checks and returns
           a list of dictionaries like this:
           {"checks": checks list, "url": url}
           If the errors from all the checks can be downloaded with
           one url, a list with one dictionary must be returned
        """
        data = []
        for check in checks:
            url = "http://gulp21.bplaced.net/osm/housenumbervalidator/"
            if check.view.name == "Duplicates":
                url += "get_dupes"
            elif check.view.name == "Problematic":
                url += "get_problematic"
            url += ".php?format=gpx"
            url += "&prob_type=%s" % check.url
            url += "&bbox=%s" % ",".join([str(coord) for coord in zoneBbox])
            data.append({"checks": [check], "url": url})
        return data

    #optional: if self.fixedFeedbackMode == "url"
    def sayBugFixed(self, error, check):
        """Tell tool server that the current error is fixed.
           Not necessary if the tool does not support automatic report.
        """
        url = "http://gulp21.bplaced.net/osm/housenumbervalidator/report.php?"
        url += "id=%s" % error.osmId[1:]
        if error.osmId[0] == "n":
            #node
            url += "&type=0"
        else:
            #way
            url += "&type=1"
        if check.view.name == "Duplicates":
            table = "dupes"
        if check.view.name == "Problematic":
            table = "problematic"
        url += "&table=%s" % table
        self.reportToToolServer(url)

    #optional: if self.falseFeedbackMode == "url"
    def sayFalseBug(self, error, check):
        """Tell the tool server that current error is a false
           positive. Not necessary if the tool does not support automatic report.
        """
        url = "http://gulp21.bplaced.net/osm/housenumbervalidator/report.php?"
        url += "id=%s" % error.osmId[1:]
        if error.osmId[0] == "n":
            #node
            url += "&type=0"
        else:
            #way
            url += "&type=1"

        self.reportToToolServer(url)

    #optional: if there is a url to a specific error on the tool webpage
    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        url = "http://gulp21.bplaced.net/osm/housenumbervalidator/?"
        url += "id=%s" % error.osmId[1:]
        if error.osmId[0] == "n":
            #node
            url += "&type=0"
        else:
            #way
            url += "&type=1"
        return url

    #optional: if an help page exists
    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki about a specific check
        """
        #Example for Osmose: http://wiki.openstreetmap.org/wiki/Osmose/errors#1040
        url = "http://wiki.openstreetmap.org/wiki/User:Gulp21/housenumbervalidator#prob_type_%s" % check.name
        return url

    #MANDATORY. A method for error file parsing.
    #The error can be a GML (see: OSM Inspector, KeepRight) or JSON (see Osmose)
    def parse_error_file(self, parseTask):
        """Extract errors from GPX file
        """
        #List of features
        rootElement = parseTask.extractRootElement()
        listOfFeatures = rootElement.getElementsByTagName("wpt")
        featuresNumber = listOfFeatures.getLength()
        other = []
        #print "Total number of features: ", featuresNumber
        for i in range(featuresNumber):
            if Thread.currentThread().isInterrupted():
                return False
            featureNode = listOfFeatures.item(i)
            #errorId
            #nameNode = featureNode.getElementsByTagName("name")
            #name = str(nameNode.item(0).getFirstChild().getNodeValue().encode("utf-8"))
            #errorIdNode = featureNode.getElementsByTagName("id")
            errorId = ""
            #desc
            descNode = featureNode.getElementsByTagName("desc")
            desc = descNode.item(0).getFirstChild().getNodeValue()
            #osmObject
            osmObjectNode = featureNode.getElementsByTagName("object_type")
            osmObject = str(osmObjectNode.item(0).getFirstChild().getNodeValue())
            #osmId
            osmIdNode = featureNode.getElementsByTagName("object_id")
            osmId = osmObject[0] + str(osmIdNode.item(0).getFirstChild().getNodeValue())
            #errorType
            errorTypeNode = featureNode.getElementsByTagName("error_type")
            errorType = str(errorTypeNode.item(0).getFirstChild().getNodeValue())
            #geo
            lat = float(featureNode.getAttribute("lat"))
            lon = float(featureNode.getAttribute("lon"))
            bbox = parseTask.build_bbox(lat, lon)

            #Append to errors
            if errorType in parseTask.errors:
                parseTask.errors[errorType].append((osmId, (lat, lon), bbox, errorId, desc, other))

        return True

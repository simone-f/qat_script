#! /usr/bin/env jython
# -*- coding: utf-8 -*-

"""
Opening hours validate module. Addresses all tags using a opening_hours based syntax using pyopening_hours.
See http://wiki.openstreetmap.org/wiki/Key:opening_hours:specification for the syntax specification.
"""

from java.lang import Thread
from ...tool import Tool
# from osm_time.OpeningHours import OpeningHours, ParseException

# tool   : opening_hours_validator
# author : Robin `ypid` Schneider
# webpage: http://openingh.openstreetmap.de/evaluation_tool/


class OpeningHoursValidator(Tool):
    def __init__(self, app):
        self.app = app

        #Tool title
        self.title = 'opening_hours_validator'

        #Tool url
        self.uri = 'http://openingh.openstreetmap.de/evaluation_tool/'
        #url: web site of the tool

        #Translations
        self.isTranslated = False
        #the translations for a tool are in tool directory/locale


        #Additional preferences for this tool
        self.prefsGui = None
        #There are additional preferences for this tool. See Osmose for example

        #Marker position
        self.markerPosition = None
        #x: x position of marker relative to the error
        #y: y position of marker relative to the error
        #None: the marker's center will be positioned at the error coordinates
        #      useful for markers with the shape of a circle or a square

        #Corrected errors
        self.fixedFeedbackMode = None
        #"url": the user can automatically report to the tool admin that an error has been corrected
        #(by clicking correctedBtn --> self.sayBugFixed())
        #None: the user cannot automatically report to the tool admin when an error has been corrected:

        #False positives
        self.falseFeedbackMode = "https://github.com/ypid/opening_hours.js/issues"
        #"url": the user can automatically report to the tool admin that an error is not an error
        #(by clicking fixeddBtn --> self.sayFalseBug())
        #msg: the user can report manually, e.g. by e-mail, to the tool admin that an error is not an error:
        #In this case, when the user clicks on the "Not an error" button, current error information
        #are collected and shown under the menu "QA Tools" --> "False positives",
        #so that the user can copy them and send the info manually to the tool admin.

        #Tool checks
        #... are listed in toolInfo and grouped in categories (called views)
        #(like "Tagging", "Routing..."), which are used to create submenus and
        #comboboxes in JOSM.
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "opening_hours" : [
                 ["opening_hours warnings",
                  "opening_hours warnings",
                  "string used by create_url() to request errors from server",
                  ],
             ],
         }
        Tool.__init__(self, app)

        #if there is not an icon for a check in 'tool directory/icons/checks/check name' a red dot is used.

    #MANDATORY
    def download_urls(self, (zoneBbox, checks)):
        """This method accepts a list of checks and returns
           a list of {"checks": checks list, "url": url} for each request
           that is needed to download all the checks.
           If the errors from all the checks can be downloaded with just
           one url, a list with one dictionary must be returned.
        """
        #Example for KeepRight
        url = "http://keepright.ipax.at/export.php?format=gpx"
        url += "&left=%s&right=%s&top=%s&bottom=%s" % (str(zoneBbox[0]), str(zoneBbox[2]), str(zoneBbox[3]), str(zoneBbox[1]))
        url += "&ch=0,%s" % ",".join([check.url for check in checks])
        return [{"checks": checks, "url": url}]

    #optional: if self.fixedFeedbackMode == "url"
    def sayBugFixed(self, error, check):
        """Tell tool the server that the current error is fixed.
           Not necessary if the tool does not support automatic report.
        """
        return True

    #optional: if self.falseFeedbackMode == "url"
    def sayFalseBug(self, error, check):
        """Tell the tool server that current error is a false
           positive. Not necessary if the tool does not support automatic report.
        """
        return True

    #MANDATORY. Return "" if there isn't any web page
    def error_url(self, error):
        """Create a url to view an error in the web browser.
        """
        url = "http://keepright.ipax.at/report_map.php?"
        url += "schema=%s" % error.errorId.split(" ")[0]
        url += "&error=%s" % error.errorId.split(" ")[1]
        return url

    #MANDATORY. Return "" if there isn't any web page
    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki about a specific check.
        """
        #Example for Osmose: http://wiki.openstreetmap.org/wiki/Osmose/errors#1040
        url = "http://wiki.openstreetmap.org/wiki/Osmose/errors#%s" % check.name
        return url

    #MANDATORY. A method for error file parsing.
    #The error can be a GML (see: OSM Inspector, KeepRight...) or JSON (see Osmose)
    def parse_error_file(self, parseTask):
        """Extract errors from GPX file
        """
        checks = parseTask.checks
        #List of features
        checksWithoutSubs = [int(c.name) // 10 for c in checks if c.name[-1] == "0"]

        rootElement = parseTask.extractRootElement()
        listOfFeatures = rootElement.getElementsByTagName("wpt")
        featuresNumber = listOfFeatures.getLength()
        #print "Total number of features: ", featuresNumber
        for i in range(featuresNumber):
            if Thread.currentThread().isInterrupted():
                return False
            featureNode = listOfFeatures.item(i)
            #errorId
            schemaNode = featureNode.getElementsByTagName("schema")
            schema = str(schemaNode.item(0).getFirstChild().getNodeValue())
            errorIdNode = featureNode.getElementsByTagName("id")
            errorId = schema + " " + str(errorIdNode.item(0).getFirstChild().getNodeValue())
            #desc
            descNode = featureNode.getElementsByTagName("desc")
            desc = descNode.item(0).getFirstChild().getNodeValue()
            #comment
            commentNode = featureNode.getElementsByTagName("comment")
            if commentNode.getLength() != 0:
                comment = commentNode.item(0).getFirstChild().getNodeValue()
                other = [comment]
                desc += "<br>Comment - %s" % comment
            else:
                other = []
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
            #check if it is a subtype
            elif int(errorType) // 10 in checksWithoutSubs:
                et = str(int(errorType) // 10 * 10)
                parseTask.errors[et].append((osmId, (lat, lon), bbox, errorId, desc, other))
        return True

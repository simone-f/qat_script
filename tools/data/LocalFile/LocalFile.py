#! /usr/bin/env jython

# tool  : local file

from java.lang import Thread
from ...tool import Tool


class LocalFileTool(Tool):
    def __init__(self, app, filePath):
        self.app = app

        #Tool title
        self.title = filePath.getName()

        #Tool url
        self.uri = "http://wiki.openstreetmap.org/wiki/Quality_Assurance_Tools_script#Local_file"

        #Translations
        self.isTranslated = False

        #Corrected errors
        self.fixedFeedbackMode = None

        #False positives
        self.falseFeedbackMode = None

        self.isLocal = True
        self.fileName = filePath.toString()

        #Additional preferences for this tool
        self.prefsGui = None

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "View": [
                     ["", "", "", "", ""],
                    ]}

        Tool.__init__(self, app)

    def parse_error_file(self, parseTask):
        """Extract errors from GPX file
        """
        checks = parseTask.checks
        #List of features
        rootElement = parseTask.extractRootElement()
        listOfFeatures = rootElement.getElementsByTagName("wpt")
        featuresNumber = listOfFeatures.getLength()
        #print "\nTotal number of features: ", featuresNumber
        errorId = ""
        errorType = checks[0].name
        other = []
        for i in range(featuresNumber):
            if Thread.currentThread().isInterrupted():
                return False
            featureNode = listOfFeatures.item(i)
            #geo
            lat = float(featureNode.getAttribute("lat"))
            lon = float(featureNode.getAttribute("lon"))
            #osmId
            if featureNode.getElementsByTagName("ogr:osmid").item(0):
                osmIdNode = featureNode.getElementsByTagName("ogr:osmid")
                osmId = osmIdNode.item(0).getFirstChild().getNodeValue()
            else:
                osmId = ""
            #desc
            if featureNode.getElementsByTagName("desc").item(0):
                descNode = featureNode.getElementsByTagName("desc")
                desc = descNode.item(0).getFirstChild().getNodeValue()
            else:
                desc = ""
            #check if error is in zoneBbox
            if lon < parseTask.zoneBbox[0] or lat < parseTask.zoneBbox[1]\
             or lon > parseTask.zoneBbox[2] or lat > parseTask.zoneBbox[3]:
                continue
            bbox = parseTask.build_bbox(lat, lon)

            #Append to errors
            #print "type of error", errorType, type(errorType)
            if errorType in parseTask.errors:
                parseTask.errors[errorType].append((osmId, (lat, lon), bbox, errorId, desc, other))
        return True

    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        return ""

#! /usr/bin/env jython

# tool  : KeepRight
# author: Harald Kleiner
# webpage  : keepright.ipax.at/

from java.net import URLEncoder
from java.lang import Thread
from ...tool import Tool


class KeepRightTool(Tool):
    def __init__(self, app):
        self.app = app

        #Tool title
        self.title = "KeepRight"

        #Tool url
        self.uri = "http://keepright.ipax.at/"

        #Translations
        self.isTranslated = True

        #Corrected errors
        self.fixedFeedbackMode = "url"

        #False positives
        self.falseFeedbackMode = "url"

        #Additional preferences for this tool
        self.prefsGui = None

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "Other": [
                        ["20", "20", "20", "20"],
                        ["30", "30", "30", "30"],
                        ["40", "40", "40", "40"],
                        ["50", "50", "50", "50"],
                        ["60", "60", "60", "60"],
                        ["70", "70", "70", "70"],
                        ["90", "90", "90", "90"],
                        ["100", "100", "100", "100"],
                        ["110", "110", "110", "110"],
                        ["120", "120", "120", "120"],
                        ["130", "130", "130", "130"],
                        ["150", "150", "150", "150"],
                        ["160", "160", "160", "160"],
                        ["170", "170", "170", "170"],
                        ["180", "180", "180", "180"],
                        ["210", "210", "210", "210"],
                        ["220", "220", "220", "220"],
                        ["270", "270", "270", "270"],
                        ["300", "300", "300", "300"],
                        ["320", "320", "320", "320"],
                        ["350", "350", "350", "350"],
                        ["360", "360", "360", "360"],
                        ["370", "370", "370", "370"],
                        ["380", "380", "380", "380"],
                        ["390", "390", "390", "390"]
                        ],

            "Intersections without junctions": [
                        ["191", "191", "191", "190"],
                        ["192", "192", "192", "190"],
                        ["193", "193", "193", "190"],
                        ["194", "194", "194", "190"],
                        ["195", "195", "195", "190"],
                        ["196", "196", "196", "190"],
                        ["197", "197", "197", "190"],
                        ["198", "198", "198", "190"]
                        ],

            "Overlapping ways": [
                        ["201", "201", "201", "200"],
                        ["202", "202", "202", "200"],
                        ["203", "203", "203", "200"],
                        ["204", "204", "204", "200"],
                        ["205", "205", "205", "200"],
                        ["206", "206", "206", "200"],
                        ["207", "207", "207", "200"],
                        ["208", "208", "208", "200"]
                        ],

            "Layer conflicts": [
                        ["231", "231", "231", "230"],
                        ["232", "232", "232", "230"]
                        ],

            "Boundaries": [
                        ["281", "281", "281", "280"],
                        ["282", "282", "282", "280"],
                        ["283", "283", "283", "280"],
                        ["284", "284", "284", "280"],
                        ["285", "285", "285", "280"]
                        ],

           "Restrictions": [
                        ["291", "291", "291", "290"],
                        ["292", "292", "292", "290"],
                        ["293", "293", "293", "290"],
                        ["294", "294", "294", "290"]
                        ],

            "Roundabouts": [
                        ["311", "311", "311", "310"],
                        ["312", "312", "312", "310"],
                        ["313", "313", "313", "310"]
                        ],

            "Geometry glitches": [
                        ["401", "401", "401", "400"],
                        ["402", "402", "402", "400"]
                        ],

            "Website": [
                        ["411", "411", "411", "410"],
                        ["412", "412", "412", "410"],
                        ["413", "413", "413", "410"]
                       ]}
        #add markers
        for view, checksInfo in self.toolInfo.iteritems():
            for i, checkInfo in enumerate(checksInfo):
                icon = checkInfo[3]
                checksInfo[i].append(icon)
        Tool.__init__(self, app)

    def download_urls(self, (zoneBbox, checks)):
        """Returns checks and urls for errors downloading
        """
        url = "http://keepright.ipax.at/export.php?format=gpx"
        url += "&left=%s&right=%s&top=%s&bottom=%s" % (str(zoneBbox[0]), str(zoneBbox[2]), str(zoneBbox[3]), str(zoneBbox[1]))
        url += "&ch=0,%s" % ",".join([check.url for check in checks])
        return [{"checks": checks, "url": url}]

    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki
        """
        url = "http://wiki.openstreetmap.org/wiki/Keepright"
        return url

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

    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        url = "http://keepright.ipax.at/report_map.php?"
        url += "schema=%s" % error.errorId.split(" ")[0]
        url += "&error=%s" % error.errorId.split(" ")[1]
        return url

    def sayFalseBug(self, error, check):
        """Tell the tool server that current error is a false
           positive
        """
        url = "http://keepright.ipax.at/comment.php?"
        url += "st=ignore&"
        if len(error.other) != 0:
            #There is a comment on the error, copy it
            url += "co=%s&" % URLEncoder.encode(error.other[0], "UTF-8")
        url += "schema=%s&" % error.errorId.split(" ")[0]
        url += "id=%s" % error.errorId.split(" ")[1]

        self.reportToToolServer(url)

    def sayBugFixed(self, error, check):
        """Tell tool server that the current error is fixed
        """
        url = "http://keepright.ipax.at/comment.php?"
        url += "st=ignore_t&"
        if len(error.other) != 0:
            #There is a comment on the error, copy it
            url += "co=%s&" % URLEncoder.encode(error.other[0], "UTF-8")
        url += "schema=%s&" % error.errorId.split(" ")[0]
        url += "id=%s" % error.errorId.split(" ")[1]

        self.reportToToolServer(url)

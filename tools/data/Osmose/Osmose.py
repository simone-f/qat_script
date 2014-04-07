#! /usr/bin/env jython
# -*- coding: utf-8 -*-

# tool   : Osmose
# authors: Etienne Chové 2009-2010
#          Jocelyn Jaubert 2011-2013
#          Frédéric Rodrigo 2011-2013
# webpage: http://osmose.openstreetmap.fr/

from java.net import URLEncoder
from java.io import File

#local import
from ...tool import Tool
from Osmose_prefs_gui import PrefsPanel

#python import
import sys


class OsmoseTool(Tool):
    def __init__(self, app):
        self.app = app

        #Tool title
        self.title = "Osmose"

        #Tool url
        self.uri = "http://osmose.openstreetmap.fr/"

        #Translations
        self.isTranslated = True

        #Corrected errors
        self.fixedFeedbackMode = "url"

        #False positives
        self.falseFeedbackMode = "url"

        #Additional preferences for this tool
        self.prefsGui = PrefsPanel(self.app)

        #Marker position
        self.markerPosition = (- 8, - 35)
        #x: x position of marker relative to the error
        #y: y position of marker relative to the error
        #None: the marker's center will be positioned at the error coordinates
        #      useful for markers with the shape of a circle or a square

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
                  "10": [
                        ["0", "0", "0", "0"],
                        ["1010", "1010", "1010", "1010"],
                        ["1040", "1040", "1040", "1040"],
                        ["1050", "1050", "1050", "1050"],
                        ["1060", "1060", "1060", "1060"],
                        ["1070", "1070", "1070", "1070"],
                        ["1080", "1080", "1080", "1080"],
                        ["1090", "1090", "1090", "1090"],
                        ["1100", "1100", "1100", "1100"],
                        ["1110", "1110", "1110", "1110"],
                        ["1120", "1120", "1120", "1120"],
                        ["1140", "1140", "1140", "1140"],
                        ["1150", "1150", "1150", "1150"],
                        ["1160", "1160", "1160", "1160"],
                        ["1170", "1170", "1170", "1170"],
                        ["1180", "1180", "1180", "1180"],
                        ["1190", "1190", "1190", "1190"],
                        ["1200", "1200", "1200", "1200"],
                        ["1210", "1210", "1210", "1210"],
                        ["1220", "1220", "1220", "1220"],
                        ["1230", "1230", "1230", "1230"]
                        ],

                  "20": [
                        ["2010", "2010", "2010", "2010"],
                        ["2020", "2020", "2020", "2020"],
                        ["2030", "2030", "2030", "2030"],
                        ["2040", "2040", "2040", "2040"],
                        ["2060", "2060", "2060", "2060"],
                        ["2080", "2080", "2080", "2080"],
                        ["2090", "2090", "2090", "2090"],
                        ["2100", "2100", "2100", "2100"]
                        ],

                  "30": [
                        ["3010", "3010", "3010", "3010"],
                        ["3020", "3020", "3020", "3020"],
                        ["3030", "3030", "3030", "3030"],
                        ["3031", "3031", "3031", "3031"],
                        ["3032", "3032", "3032", "3032"],
                        ["3033", "3033", "3033", "3033"],
                        ["3040", "3040", "3040", "3040"],
                        ["3050", "3050", "3050", "3050"],
                        ["3060", "3060", "3060", "3060"],
                        ["3070", "3070", "3070", "3070"],
                        ["3080", "3080", "3080", "3080"],
                        ["3090", "3090", "3090", "3090"],
                        ["3091", "3091", "3091", "3091"],
                        ["3100", "3100", "3100", "3100"],
                        ["3110", "3110", "3110", "3110"],
                        ["3120", "3120", "3120", "3120"],
                        ["3150", "3150", "3150", "3150"],
                        ["3160", "3160", "3160", "3160"],
                        ["3161", "3161", "3161", "3161"],
                        ["3170", "3170", "3170", "3170"],
                        ["3180", "3180", "3180", "3180"],
                        ["3190", "3190", "3190", "3190"]
                        ],

                  "40": [
                        ["4010", "4010", "4010", "4010"],
                        ["4020", "4020", "4020", "4020"],
                        ["4030", "4030", "4030", "4030"],
                        ["4040", "4040", "4040", "4040"],
                        ["4060", "4060", "4060", "4060"],
                        ["4070", "4070", "4070", "4070"],
                        ["4080", "4080", "4080", "4080"],
                        ["4090", "4090", "4090", "4090"],
                        ["4100", "4100", "4100", "4100"]
                        ],

                  "50": [
                        ["5010", "5010", "5010", "5010"],
                        ["5020", "5020", "5020", "5020"],
                        ["5030", "5030", "5030", "5030"],
                        ["5040", "5040", "5040", "5040"],
                        ["5050", "5050", "5050", "5050"]
                        ],

                  "60": [
                        ["6010", "6010", "6010", "6010"],
                        ["6020", "6020", "6020", "6020"],
                        ["6030", "6030", "6030", "6030"],
                        ["6040", "6040", "6040", "6040"],
                        ["6050", "6050", "6050", "6050"],
                        ["6060", "6060", "6060", "6060"],
                        ["6070", "6070", "6070", "6070"]
                        ],

                  "70": [
                        ["7010", "7010", "7010", "7010"],
                        ["7011", "7011", "7011", "7011"],
                        ["7012", "7012", "7012", "7012"],
                        ["7020", "7020", "7020", "7020"],
                        ["7030", "7030", "7030", "7030"],
                        ["7040", "7040", "7040", "7040"],
                        ["7050", "7050", "7050", "7050"],
                        ["7060", "7060", "7060", "7060"],
                        ["7070", "7070", "7070", "7070"],
                        ["7080", "7080", "7080", "7080"],
                        ["7090", "7090", "7090", "7090"],
                        ["7100", "7100", "7100", "7100"],
                        ["7110", "7110", "7110", "7110"],
                        ["7120", "7120", "7120", "7120"],
                        ["7130", "7130", "7130", "7130"]
                        ],

                  "80": [
                        ["8010", "8010", "8010", "8010"],
                        ["8011", "8011", "8011", "8011"],
                        ["8020", "8020", "8020", "8020"],
                        ["8021", "8021", "8021", "8021"],
                        ["8030", "8030", "8030", "8030"],
                        ["8031", "8031", "8031", "8031"],
                        ["8040", "8040", "8040", "8040"],
                        ["8041", "8041", "8041", "8041"],
                        ["8050", "8050", "8050", "8050"],
                        ["8051", "8051", "8051", "8051"],
                        ["8060", "8060", "8060", "8060"],
                        ["8070", "8070", "8070", "8070"],
                        ["8080", "8080", "8080", "8080"],
                        ["8101", "8101", "8101", "8101"],
                        ["8110", "8110", "8110", "8110"],
                        ]}
        #add markers
        for view, checksInfo in self.toolInfo.iteritems():
            for i, checkInfo in enumerate(checksInfo):
                icon = checkInfo[3]
                checksInfo[i].append("marker-b-%s" % icon)

        Tool.__init__(self, self.app)

    def download_urls(self, (zoneBbox, checks)):
        """Returns checks and urls for errors downloading
        """
        #username
        username = self.app.toolsPrefs["osmose"]["username"]
        #level
        level = self.app.toolsPrefs["osmose"]["level"]

        #limit
        if (self.app.favouriteZoneStatus and self.app.favZone.zType in ("polygon", "boundary")) or len(checks) > 1:
            #if a limit exists it will be applied after the download
            limit = 500
        else:
            if self.app.toolsPrefs["osmose"]["limit"] != "":
                self.app.toolsPrefs["osmose"]["limit"] = int(self.app.toolsPrefs["osmose"]["limit"])
            limits = [self.app.maxErrorsNumber, self.app.toolsPrefs["osmose"]["limit"]]
            for i, l in enumerate(limits):
                if l == "" or l > 500:
                    limits[i] = 500
            limit = min(limits)

        url = "http://osmose.openstreetmap.fr/api/0.2/errors?"
        url += "bbox=%s" % ",".join([str(coord) for coord in zoneBbox])
        url += "&item=%s&full=true" % ",".join([check.url for check in checks])
        url += "&limit=%d" % limit
        url += "&level=%s" % level
        if username != "":
            url += "&username=%s" % URLEncoder.encode(username, "UTF-8")
        return [{"checks": checks, "url": url}]

    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki
        """
        url = "http://wiki.openstreetmap.org/wiki/Osmose/errors#%s" % check.name
        return url

    def parse_error_file(self, parseTask):
        """Extract errors from JSON file
        """
        #jyson import
        jysonModule = File.separator.join([parseTask.app.SCRIPTDIR, "tools", "jyson.jar"])
        if jysonModule not in sys.path:
            sys.path.append(jysonModule)
        from com.xhaus.jyson import JysonCodec as json
        data = json.loads(parseTask.app.errorsData)
        for e in data["errors"]:
            #lat, lon, errorId
            lat = float(e[0])
            lon = float(e[1])
            errorId = e[2]
            errorType = e[3]        # osmose item
            #osmId
            osmId = e[6]
            osmId = osmId.replace("node", "n")
            osmId = osmId.replace("way", "w")
            osmId = osmId.replace("relation", "r")
            other = [errorType]
            #desc
            if e[8] != "":
                desc = "%s %s" % (e[8], e[9])
            else:
                desc = e[9]
            #bbox
            bbox = parseTask.build_bbox(lat, lon)

            #Append to errors
            if errorType in parseTask.errors:
                parseTask.errors[errorType].append((osmId, (lat, lon), bbox, errorId, desc, other))
        return True

    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        url = "http://osmose.openstreetmap.fr/it/map/?zoom=18"
        url += "&lat=%s&lon=%s&layers=B000000FFFFFFFFFFFFFFFFFFT" % (error.coords[0],
                                                                     error.coords[1])
        url += "&item=%s&level=1,2,3" % error.other[0]
        return url

    def sayFalseBug(self, error, check):
        """Tell the tool server that current error is a false
           positive
        """
        url = "http://osmose.openstreetmap.fr/api/0.2/error/%s/false" % error.errorId
        self.reportToToolServer(url)

    def sayBugFixed(self, error, check):
        """Tell tool server that the current error is fixed
        """
        url = "http://osmose.openstreetmap.fr/api/0.2/error/%s/done" % error.errorId
        self.reportToToolServer(url)

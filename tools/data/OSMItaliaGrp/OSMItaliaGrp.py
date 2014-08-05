#! /usr/bin/env jython

# tool: Errori in OSM Italia
# webpage: http://dl.dropboxusercontent.com/u/41550819/OSM/Errori_in_Italia_Grp/index.html

from java.lang import Thread

#local import
from ...tool import Tool


class OSMItaliaGrpTool(Tool):
    def __init__(self, app):
        self.app = app

        #Tool title
        self.title = "OSM Italia Grp"

        #Tool url
        self.uri = "http://dl.dropboxusercontent.com/u/41550819/OSM/Errori_in_Italia_Grp/index.html"

        #Translations
        self.isTranslated = False

        #Corrected errors
        self.fixedFeedbackMode = None

        #False positives
        self.falseFeedbackMode = "url"

        #Additional preferences for this tool
        self.prefsGui = None

        #Marker position
        self.markerPosition = (- 8, - 37)
        #x: x position of marker relative to the error
        #y: y position of marker relative to the error
        #None: the marker's center will be positioned at the error coordinates
        #      useful for markers with the shape of a circle or a square

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "Tagging": [
                         ["Ref non conformi", "wrong_refs", "https://bit.ly/17jY71V", "wrong_refs"],
                         ["Ref nel nome", "no_ref", "https://bit.ly/10bCraW", "no_ref"],
                         ["Nomi non conformi", "name_via", "https://bit.ly/XPMfG3", "name_via"],
                         ["Spazi nel nome", "wrong_spaces_in_hgw_name", "https://bit.ly/YQI1xF", "wrong_spaces_in_hgw_name"],
                         ["Numeri telefonici", "phone_numbers", "https://bit.ly/15iJoIj", "phone_numbers"],
                         ["Wikipedia no lang", "wikipedia_lang", "https://bit.ly/11agjdJ", "wikipedia_lang"]
                         ],
            "Geometrie": [
                         ["Nodi duplicati (Veneto)", "duplicate_build_land_barr_nodes", "https://bit.ly/XEHiOh", "duplicate_build_land_barr_nodes"],
                         ["Edifici duplicati (Veneto)", "duplicate_build_land_barrier", "https://bit.ly/Z0KuEV", "duplicate_build_land_barrier"],
                         ["Nodi solitari", "lonely_nodes", "https://bit.ly/11beU42", "lonely_nodes"],
                         ["Strade duplicate", "duplicate_highways", "https://bit.ly/YQF7ca", "duplicate_highways"],
                         ["Rotatorie sospette", "wrong_roundabout_exit_entry", "https://bit.ly/13hVq0g", "wrong_roundabout_exit_entry"]#,
                         #["Uscita rotatoria senza dir obbligata", "missing_no_turn_on_roundabout_exit", "https://bit.ly/17EzZKj", "missing_no_turn_on_roundabout_exit"],
                         #["Strade non connesse (GEOFABRIK)", "disconnected_highways", "https://bit.ly/disconnected_highways", "disconnected_highways"]
                         ]}
        #add markers
        for view, checksInfo in self.toolInfo.iteritems():
            for i, checkInfo in enumerate(checksInfo):
                icon = checkInfo[3]
                checksInfo[i].append("marker_%s" % icon)

        Tool.__init__(self, app)

    def download_urls(self, (zoneBbox, checks)):
        """Returns checks and urls for errors downloading
        """
        data = []
        for check in checks:
            data.append({"checks": [check], "url": check.url})
        return data

    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki
        """
        url = "http://dl.dropboxusercontent.com/u/41550819/OSM/Errori_in_Italia_Grp/index.html"
        return url

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
            if checks[0].name == "lonely_nodes":
                osmId = ""
                #desc
                desc = "lonely node"
                errorId = "%f,%f" % (lat, lon)
            else:
                #osmId
                osmIdNode = featureNode.getElementsByTagName("ogr:osmid")
                osmId = osmIdNode.item(0).getFirstChild().getNodeValue()
                #desc
                descNode = featureNode.getElementsByTagName("desc")
                desc = descNode.item(0).getFirstChild().getNodeValue()
            #check if error is in zoneBbox
            if lon < parseTask.zoneBbox[0] or lat < parseTask.zoneBbox[1] or lon > parseTask.zoneBbox[2] or lat > parseTask.zoneBbox[3]:
                continue
            bbox = parseTask.build_bbox(lat, lon)

            #Append to errors
            #print "type of error", errorType, type(errorType)
            if errorType in parseTask.errors:
                parseTask.errors[errorType].append((osmId, (lat, lon), bbox, errorId, desc, other))
        return True

    def sayFalseBug(self, error, check):
        """Tell the tool server that current error is a false
           positive
        """
        url = "http://www.forsi.it/osm/errors-in-osm/flag_error.php?"
        url += "check=%s&" % check.name
        url += "osmid=%s" % error.osmId

        self.reportToToolServer(url)

    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        return ""

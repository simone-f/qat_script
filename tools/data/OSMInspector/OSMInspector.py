#! /usr/bin/env jython

# tool  : OSM Inspector
# author: GEOFABRIK
# webpage  : tools.geofabrik.de/osmi/

from java.lang import Thread

#local import
from ...tool import Tool


class OSMInspectorTool(Tool):
    def __init__(self, app):
        self.app = app
        #not usable checks: island, it gives one feature for every seegment of 2 nodes
        #checks to add    : "addresses street not found", http://tools.geofabrik.de/osmi/view/NAME_OF_VIEW/wxs?

        #Tool title
        self.title = "OSM Inspector"

        #Tool url
        self.uri = "http://tools.geofabrik.de/osmi/"

        #Translations
        self.isTranslated = True

        #Corrected errors
        self.fixedFeedbackMode = None

        #False positives
        self.falseFeedbackMode = "msg"

        #Additional preferences for this tool
        self.prefsGui = None

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {
            "Routing": [
                         ["Unconnected major 1", "unconnected_major1", "unconnected_major1", "rout_maj1"],
                         ["Unconnected major 2", "unconnected_major2", "unconnected_major2", "rout_maj2"],
                         ["Unconnected major 5", "unconnected_major5", "unconnected_major5", "rout_maj5"],
                         ["Unconnected minor 1", "unconnected_minor1", "unconnected_minor1", "rout_min1"],
                         ["Unconnected minor 2", "unconnected_minor2", "unconnected_minor2", "rout_min2"],
                         ["Unconnected minor 5", "unconnected_minor5", "unconnected_minor5", "rout_min5"],
                         ["Duplicate ways", "duplicate_ways", "duplicate_ways", "rout_duplicate"],
                         ],

            "Geometry": [
                         ["Self intersecting ways","self_intersection_ways", "self_intersection_ways", "geom_self_intersection"],
                         ["Way with single node", "single_node_in_way", "single_node_in_way", "geom_single_node_in_way"]
                         ],
            "Addresses": [
                         ["No addr street", "no_addr_street", "no_addr_street", "addr_no_addr_street"],
                         ["Street not found", "street_not_found", "street_not_found", "addr_street_not_found"],
                         ["Interpolation errors", "interpolation_errors", "interpolation_errors", "addr_interpolation"]
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
        #collect checks per view
        viewChecks = {}
        for check in checks:
            view = check.view
            if view not in viewChecks:
                viewChecks[view] = []
            viewChecks[view].append(check)
        for view, checksList in viewChecks.iteritems():
            url = "http://tools.geofabrik.de/osmi/view/%s" % view.name.lower()
            url += "/wxs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&BBOX=%s" % ",".join([str(x) for x in zoneBbox])
            url += "&TYPENAME=%s" % ",".join([check.url for check in checksList])
            data.append({"checks": checksList, "url": url})
        return data

    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki
        """
        viewName = check.view.name
        url = "http://wiki.openstreetmap.org/wiki/OSM_Inspector/Views/%s" % viewName.capitalize()
        return url

    def parse_error_file(self, parseTask):
        """Extract errors from WFS
        """
        other = []
        #List of features
        rootElement = parseTask.extractRootElement()
        listOfFeatures = rootElement.getElementsByTagName("gml:featureMember")
        featuresNumber = listOfFeatures.getLength()
        #print "Total number of features: ", featuresNumber
        #desc
        desc = ""
        for i in range(featuresNumber):
            if Thread.currentThread().isInterrupted():
                return False
            featureNode = listOfFeatures.item(i)
            errorNode = featureNode.getFirstChild().getNextSibling()
            errorType = errorNode.getTagName()[3:]
            other.append(errorType)
            #childNodes = errorNode.getChildNodes()
            #osmObject
            if errorType in ("unconnected_major1", "unconnected_major2", "unconnected_major5",
                              "unconnected_minor1", "unconnected_minor2", "unconnected_minor5"):
                osmObject = "node"
            elif errorType == "duplicate_ways":
                osmObject = "way"
            elif errorType in ("self_intersection_ways", "single_node_in_way"):
                osmObject = "way"
            elif errorType in ("no_addr_street", "street_not_found"):
                for osmObject in ("node", "way"):
                    osmIdNode = errorNode.getElementsByTagName("ms:%s_id" % osmObject)
                    if osmIdNode.item(0).getFirstChild() is not None:
                        break
            elif errorType == "interpolation_errors":
                osmObject = "way"
                descNode = featureNode.getElementsByTagName("ms:error")
                desc = descNode.item(0).getFirstChild().getNodeValue()

            #osmId
            osmIdNode = errorNode.getElementsByTagName("ms:%s_id" % osmObject)
            osmId = osmObject[0] + str(osmIdNode.item(0).getFirstChild().getNodeValue())
            #errorId, id of the error in tool database
            if errorType in ("unconnected_major1", "unconnected_major2", "unconnected_major5",
                             "unconnected_minor1", "unconnected_minor2", "unconnected_minor5",
                             "duplicate_ways"):
                errorIdNode = errorNode.getElementsByTagName("ms:problem_id")
                errorId = str(errorIdNode.item(0).getFirstChild().getNodeValue())
            else:
                errorId = ""
            #geo
            bboxNodes = errorNode.getElementsByTagName("gml:coordinates")
            bboxString = bboxNodes.item(0).getFirstChild().getNodeValue()
            bbox = [float(x) for x in bboxString.replace(" ", ",").split(",")]
            if errorType in ("no_addr_street", "street_not_found"):
                (lat, lon) = (bbox[1], bbox[0])
                bbox = parseTask.build_bbox(lat, lon)
            else:
                if osmObject == "node":
                    (lat, lon) = (bbox[1], bbox[0])
                    bbox = parseTask.build_bbox(lat, lon)
                elif osmObject == "way":
                    lat = ((bbox[3] - bbox[1]) / 2) + bbox[1]
                    lon = ((bbox[2] - bbox[0]) / 2) + bbox[0]

                    bbox = parseTask.check_bbox_width(lat, lon, bbox)

            ##
            #if lon < parseTask.zoneBbox[0] or lat < parseTask.zoneBbox[1] or\
            #   lon > parseTask.zoneBbox[2] or lat > parseTask.zoneBbox[3]:
            #    continue

            #Append to errors
            if errorType in parseTask.errors:
                parseTask.errors[errorType].append((osmId, (lat, lon), bbox, errorId, desc, other))
        return True

    def error_url(self, error):
        """Create a url to view an error in the web browser
        """
        #http://tools.geofabrik.de/osmi/?view=routing&lon=13.87375&lat=42.95380&zoom=18&opacity=0.59
        url = "http://tools.geofabrik.de/osmi/?"
        url += "view=%s" % error.check.view.name.lower()
        url += "&overlays=%s" % error.other[0]
        url += "&zoom=18&opacity=0.59"
        url += "&lat=%f" % error.coords[0]
        url += "&lon=%f" % error.coords[1]
        return url

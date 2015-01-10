#!/usr/bin/env jython
# -*- coding: utf-8 -*-

"""
Opening hours validate module. Addresses all tags using a opening_hours based syntax using pyopening_hours.
See http://wiki.openstreetmap.org/wiki/Key:opening_hours:specification for the syntax specification.
"""

import sys
#import logging

from java.lang import Thread
from java.io import File
from ...tool import Tool

# tool   : opening_hours_validator
# author : Robin `ypid` Schneider
# webpage: http://openingh.openstreetmap.de/evaluation_tool/

#logging.basicConfig(
#    format='%(levelname)s (OpeningHoursValidatorTool): %(message)s',
#    level=logging.DEBUG,
#    # level=logging.INFO,
#)

class OpeningHoursValidatorTool(Tool):

    # OPENING_HOURS_SERVER_URL = 'http://localhost:8080/api/oh_interpreter'
    OPENING_HOURS_SERVER_URL = 'http://openingh.openstreetmap.de/api/oh_interpreter'

    # OPENING_HOURS_SERVER_TIMEOUT = 60
    # set server side.

    def __init__(self, app):
        self.app = app

        # Tool title
        self.title = 'Opening Hours Validator'

        # Tool url
        self.uri = 'http://openingh.openstreetmap.de/evaluation_tool/'
        # url: web site of the tool

        # Translations
        self.isTranslated = True
        # the translations for a tool are in tool directory/locale

        # Additional preferences for this tool
        self.prefsGui = None
        # There are additional preferences for this tool. See Osmose for example

        # Marker position
        self.markerPosition = None
        # x: x position of marker relative to the error
        # y: y position of marker relative to the error
        # None: the marker's center will be positioned at the error coordinates
        #      useful for markers with the shape of a circle or a square

        # Corrected errors
        self.fixedFeedbackMode = None
        # "url": the user can automatically report to the tool admin that an error has been corrected
        # (by clicking correctedBtn --> self.sayBugFixed())
        # None: the user cannot automatically report to the tool admin when an error has been corrected:

        # False positives
        self.falseFeedbackMode = "msg"
        # "url": the user can automatically report to the tool admin that an error is not an error
        # (by clicking fixeddBtn --> self.sayFalseBug())
        # msg: the user can report manually, e.g. by e-mail, to the tool admin that an error is not an error:
        # In this case, when the user clicks on the "Not an error" button, current error information
        # are collected and shown under the menu "QA Tools" --> "False positives",
        # so that the user can copy them and send the info manually to the tool admin.

        # Tool checks
        # ... are listed in toolInfo and grouped in categories (called views)
        # (like "Tagging", "Routing..."), which are used to create submenus and
        # comboboxes in JOSM.
        # {view: [title, name, url, icon, marker], ...}
        # Names correspond to https://github.com/ypid/opening_hours.js/blob/c22baae9270dcd1625aeaf901dcb63a424f09abe/js/i18n-resources.js#L28
        self.toolInfo = {
            "opening_hours": [
                [
                    "error",        # errors and warnings
                    "opening_hours_error",
                    "opening_hours",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "opening_hours_warnOnly",
                    "opening_hours",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "opening_hours_errorOnly",
                    "opening_hours",
                    "circle_err",
                    "circle_err",
                ],
            ],

            "collection_times": [
                [
                    "error",        # errors and warnings
                    "collection_times_error",
                    "collection_times",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "collection_times_warnOnly",
                    "collection_times",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "collection_times_errorOnly",
                    "collection_times",
                    "circle_err",
                    "circle_err",
                ],
            ],
            "lit": [
                [
                    "error",        # errors and warnings
                    "lit_error",
                    "lit",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "lit_warnOnly",
                    "lit",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "lit_errorOnly",
                    "lit",
                    "circle_err",
                    "circle_err",
                ],
            ],
            "smoking_hours": [
                [
                    "error",        # errors and warnings
                    "smoking_hours_error",
                    "smoking_hours",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "smoking_hours_warnOnly",
                    "smoking_hours",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "smoking_hours_errorOnly",
                    "smoking_hours",
                    "circle_err",
                    "circle_err",
                ],
            ],
            "service_times": [
                [
                    "error",        # errors and warnings
                    "service_times_error",
                    "service_times",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "service_times_warnOnly",
                    "service_times",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "service_times_errorOnly",
                    "service_times",
                    "circle_err",
                    "circle_err",
                ],
            ]

        }
        Tool.__init__(self, app)

    # MANDATORY
    def download_urls(self, (zoneBbox, checks)):
        """This method accepts a list of checks and returns
           a list of {"checks": checks list, "url": url} for each request
           that is needed to download all the checks.
           If the errors from all the checks can be downloaded with just
           one url, a list with one dictionary must be returned.
        """
        # https://github.com/ypid/opening_hours_server.js/blob/master/ohs.js
        # E.g.
        # http://localhost:8080/api/oh_interpreter?tag=opening_hours&s=51.249&w=7.149&n=51.251&e=7.151&filter=errorOnly
        requests = []
        tagsAndChecks = {}
        # Divide requests by tag
        for check in checks:
            tag = check.url
            if tag not in tagsAndChecks:
                tagsAndChecks[tag] = []
            tagsAndChecks[tag].append(check)
        for tag, checksList in tagsAndChecks.iteritems():
            ohs_query_url = self.OPENING_HOURS_SERVER_URL
            ohs_query_url += '?&tag=%s' % tag
            ohs_query_url += '&s=%s&w=%s&n=%s&e=%s' % (
                zoneBbox[1], zoneBbox[0],
                zoneBbox[3], zoneBbox[2])
            ohs_query_url += '&filter=%s' % check.name.split("_")[-1]
            requests.append({"checks": checksList,
                             "url": ohs_query_url})
        return requests

    # MANDATORY. Return "" if there isn't any web page
    def error_url(self, error):
        """Create a url to view an error in the web browser.
        """
        from java.net import URL, URLEncoder
        # Custom variables:
        # https://github.com/ypid/opening_hours.js#library-api
        if error.check.url in ("opening_hours", "lit", "smoking_hours"):
            oh_mode = 0
        elif error.check.url in ("collection_times", "service_times"):
            oh_mode = 2
        return '%s?EXP=%s&lat=%f&lon=%f&mode=%d' % (
            self.uri,
            URLEncoder.encode(error.other['oh_value'], "UTF-8").replace("+", "%20"),
            error.coords[0],
            error.coords[1],
            oh_mode
        )

    # MANDATORY. Return "" if there isn't any web page
    def help_url(self, check):
        """Create a url to show some info/help on this check, for example
           a webpage on the OSM Wiki about a specific check.
        """
        return self.uri

    # MANDATORY. A method for error file parsing.
    # The error can be a GML (see: OSM Inspector, KeepRight...) or JSON (see Osmose)
    def parse_error_file(self, parseTask):
        """Extract errors from JSON file. Implementation based on OsmoseTool.
        """
        # Errors reported from:
        # https://github.com/ypid/opening_hours_server.js/blob/master/ohs.js
        # check_osm_key = opening_hours || collection_times || lit
        #                 || smoking_hours || service_times
        check_osm_key = parseTask.checks[0].url
        #logging.debug("parse_error_file for tag %s", check_osm_key)
        #logging.debug("parseTask.errors: %s", parseTask.errors)
        #logging.debug("parseTask.tool: %s", parseTask.tool)
        jysonModule = File.separator.join([parseTask.app.SCRIPTDIR,
                                           "tools",
                                           "jyson.jar"])
        if jysonModule not in sys.path:
            sys.path.append(jysonModule)
        from com.xhaus.jyson import JysonCodec as json
        overpass_json_object = json.loads(parseTask.app.errorsData)

        for element in overpass_json_object['elements']:
            if check_osm_key not in element['tags']:
                # logging.error('opening_hours_server.js returned \
                # element which did not contain queried tag.')
                continue

            #if 'name' in element['tags']:
            #    logging.debug("Tag name: %s", element['tags']['name'])
            oh_value = element['tags'][check_osm_key]
            lat = None
            lon = None
            if 'center' in element:
                lat = float(element['center']['lat'])
                lon = float(element['center']['lon'])
            else:
                lat = float(element['lat'])
                lon = float(element['lon'])
            osmId = "%s%d" % (element['type'][:1], element['id'])
            bbox = parseTask.build_bbox(lat, lon)

            errorID = None
            errorType = ""
            if element['tag_problems'][check_osm_key]['error']:
                #logging.debug("Value error")
                errorType = 'errorOnly'
            else:
                #logging.debug("Value warning")
                errorType = 'warnOnly'

            user_message = ""
            if element['tag_problems'][check_osm_key]['eval_notes'] \
            and element['tag_problems'][check_osm_key]['eval_notes'] != [{}]:
                if errorType == 'errorOnly':
                    user_message = "Error: Value (%s) could not be parsed, reason:<br>%s" % (
                        oh_value,
                        "<br>".join(element['tag_problems'][check_osm_key]['eval_notes'])
                        )
                else:
                    user_message = "Warning: The following warning%s occurred for value (%s):<br>%s" % (
                        's' if len(element['tag_problems'][check_osm_key]['eval_notes']) > 1 else '',
                        oh_value,
                        '<br>'.join(element['tag_problems'][check_osm_key]['eval_notes'])
                        )

            # print "check_osm_key: ", element['tag_problems'][check_osm_key]
            # print "osm id: ", osmId
            # print "errorType: ", errorType
            # print "user_message:", user_message

            #logging.debug('Appending')
            errorData = (osmId, (lat, lon), bbox, errorID, user_message,
                         {'oh_value': oh_value})
            for check_name in (check_osm_key + '_error',
                               check_osm_key + "_" + errorType):
                if check_name in parseTask.errors:
                    parseTask.errors[check_name].append(errorData)

        return True

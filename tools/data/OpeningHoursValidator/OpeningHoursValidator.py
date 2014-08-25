#!/usr/bin/env jython
# -*- coding: utf-8 -*-

"""
Opening hours validate module. Addresses all tags using a opening_hours based syntax using pyopening_hours.
See http://wiki.openstreetmap.org/wiki/Key:opening_hours:specification for the syntax specification.
"""

import sys
import urllib
import urllib2
import logging

from java.lang import Thread
from java.io import File
from ...tool import Tool

# tool   : opening_hours_validator
# author : Robin `ypid` Schneider
# webpage: http://openingh.openstreetmap.de/evaluation_tool/

logging.basicConfig(
    format='%(levelname)s (OpeningHoursValidatorTool): %(message)s',
    level=logging.DEBUG,
    # level=logging.INFO,
)

class OpeningHoursValidatorTool(Tool):

    # OPENING_HOURS_SERVER_URL = 'http://localhost:8080/api/oh_interpreter'
    OPENING_HOURS_SERVER_URL = 'http://openingh.openstreetmap.de:12355/api/oh_interpreter'

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

        # # Custom variables:

        # Current mode of opening_hours.js: https://github.com/ypid/opening_hours.js#library-api
        self.oh_mode = 0

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
                    "error",
                    "error",
                    "string used by create_url() to request errors from server",
                    "circle_err",
                    "circle_err",
                ], [
                    "warnOnly",
                    "warnOnly",
                    "string used by create_url() to request errors from server",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "errorOnly",
                    "errorOnly",
                    "string used by create_url() to request errors from server",
                    "circle_err",
                    "circle_err",
                ],
            ],
        }
        Tool.__init__(self, app)

        # if there is not an icon for a check in 'tool directory/icons/checks/check name' a red dot is used.

    # MANDATORY
    def download_urls(self, (zoneBbox, checks)):
        """This method accepts a list of checks and returns
           a list of {"checks": checks list, "url": url} for each request
           that is needed to download all the checks.
           If the errors from all the checks can be downloaded with just
           one url, a list with one dictionary must be returned.
        """

        check_osm_key = 'opening_hours'

        # http://localhost:8080/api/oh_interpreter?tag=opening_hours&s=51.249&w=7.149&n=51.251&e=7.151&filter=errorOnly
        logging.debug("Downloading data for checks %s.", checks)
        ohs_query_url = self.OPENING_HOURS_SERVER_URL \
            + '?&tag=%s' % urllib2.quote(check_osm_key) \
            + '&s=%s&w=%s&n=%s&e=%s' % (
                zoneBbox[1], zoneBbox[0],
                zoneBbox[3], zoneBbox[2])
        return [{"checks": checks, "url": ohs_query_url}]

    # MANDATORY. Return "" if there isn't any web page
    def error_url(self, error):
        """Create a url to view an error in the web browser.
        """
        return '%s?EXP=%s&lat=%f&lon=%f&mode=%d' % (
            self.uri,
            urllib.quote(error.other['oh_value']),
            error.other['lat'],
            error.other['lon'],
            error.other['oh_mode'],
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

        check_osm_key = 'opening_hours'
        logging.debug("parse_error_file for tag %s", check_osm_key)

        print parseTask
        logging.debug("parseTask.errors: %s", parseTask.errors)
        logging.debug("parseTask.tool: %s", parseTask.tool)
        jysonModule = File.separator.join([parseTask.app.SCRIPTDIR, "tools", "jyson.jar"])
        if jysonModule not in sys.path:
            sys.path.append(jysonModule)
        from com.xhaus.jyson import JysonCodec as json
        overpass_json_object = json.loads(parseTask.app.errorsData)
        print overpass_json_object
        for element in overpass_json_object['elements']:
            if check_osm_key not in element['tags']:
                logging.error('opening_hours_server.js returned element which did not contain queried tag.')
                continue

            if 'name' in element['tags']:
                logging.debug("Tag name: %s", element['tags']['name'])
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

            oh_value = element['tags'][check_osm_key]
            user_message = None

            errorID = None
            if element['tag_problems'][check_osm_key]['error']:
                logging.debug("Value error")
                errorID = 'errorOnly'
                user_message = "%s\n\n: Value (%s) could not be parsed, reason:\n%s" % (
                    "Error",
                    oh_value,
                    '\n'.join(element['tag_problems'][check_osm_key]['eval_notes'])
                    )
            elif element['tag_problems'][check_osm_key]['eval_notes']:
                logging.debug("Value warning")
                errorID = 'warnOnly'
                user_message = "%s\n\nThe following warning%s occurred for value (%s):\n%s" % (
                    "Warning",
                    's' if len(element['tag_problems'][check_osm_key]['eval_notes']) > 1 else '',
                    oh_value,
                    '\n'.join(element['tag_problems'][check_osm_key]['eval_notes'])
                    )

            if errorID in parseTask.errors or ('error' in parseTask.errors and (errorID == 'warnOnly' or errorID == 'errorOnly')):
                logging.debug('Appending')
                parseTask.errors['error'].append(
                    (
                        osmId,
                        (lat, lon),
                        bbox,
                        errorID,
                        user_message,
                        {
                            'lat': lat,
                            'lon': lon,
                            'oh_value': oh_value,
                            'oh_mode': self.oh_mode,
                        },
                    )
                )

        return True

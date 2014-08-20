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

# import pyopening_hours
# ImportError: No module named pyopening_hours

# tool   : opening_hours_validator
# author : Robin `ypid` Schneider
# webpage: http://openingh.openstreetmap.de/evaluation_tool/

logging.basicConfig(
    format='%(levelname)s (OpeningHoursValidatorTool): %(message)s',
    level=logging.DEBUG,
    # level=logging.INFO,
)

class OpeningHoursValidatorTool(Tool):

    OVERPASS_API_URL = 'http://overpass-api.de/api/interpreter'
    OVERPASS_API_TIMEOUT = 60

    def __init__(self, app):
        self.app = app

        # Tool title
        self.title = 'opening_hours_validator'

        # Tool url
        self.uri = 'http://openingh.openstreetmap.de/evaluation_tool/'
        # url: web site of the tool

        # Translations
        self.isTranslated = False
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
                    "filter_error",
                    "filter_error",
                    "string used by create_url() to request errors from server",
                    "circle_err",
                    "circle_err",
                ], [
                    "filter_warnOnly",
                    "filter_warnOnly",
                    "string used by create_url() to request errors from server",
                    "circle_red_warn",
                    "circle_red_warn",
                ], [
                    "filter_errorOnly",
                    "filter_errorOnly",
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

        overpass_query_url = self.OVERPASS_API_URL \
            + '?&data=' \
            + urllib2.quote("[out:json][timeout:%d][bbox:%f,%f,%f,%f];" % (
                self.OVERPASS_API_TIMEOUT,
                zoneBbox[1], zoneBbox[0],
                zoneBbox[3], zoneBbox[2]
            ) + "(node['%s'];way['%s'];);out body center;" % (check_osm_key, check_osm_key))
        return [{"checks": checks, "url": overpass_query_url}]

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

        print parseTask
        logging.debug("parseTask.errors: %s", parseTask.errors)
        logging.debug("parseTask.tool: %s", parseTask.tool)
        jysonModule = File.separator.join([parseTask.app.SCRIPTDIR, "tools", "jyson.jar"])
        if jysonModule not in sys.path:
            sys.path.append(jysonModule)
        from com.xhaus.jyson import JysonCodec as json
        overpass_json_object = json.loads(parseTask.app.errorsData)
        for element in overpass_json_object['elements']:
            if check_osm_key not in element['tags']:
                logging.error('Overpass API returned element which did not contain queried tag.')
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
            errorID = ''

            oh_value = element['tags'][check_osm_key]
            user_error_message = None
            # try:
            #     oh = pyopening_hours.OpeningHours(oh_value)
            # except pyopening_hours.ParseException:
            #     # print(error.message)
            #     # print(self._return_tuple_for_element(element))
            #     interesting_elements['errorOnly'].append(self._return_tuple_for_element(element))
            #     continue
            # if oh.getWarnings():
            #     # for line in oh.getWarnings():
            #         # print('  ' + line)
            #     # print(self._return_tuple_for_element(element))
            #     interesting_elements['warnOnly'].append(self._return_tuple_for_element(element))
            user_error_message = "%s\n\nValue could not be parsed, reason:\n%s" % (oh_value, "error")

            if 'error' in parseTask.errors:
                parseTask.errors['error'].append(
                    (
                        osmId,
                        (lat, lon),
                        bbox,
                        errorID,
                        user_error_message,
                        {
                            'lat': lat,
                            'lon': lon,
                            'oh_value': oh_value,
                            'oh_mode': self.oh_mode,
                        },
                    )
                )

            # if 'error' in checks:
            # if 'errorOnly' in checks:
            # if 'warnOnly' in checks:
        return True

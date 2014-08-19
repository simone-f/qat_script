#!/usr/bin/env python
# encoding: utf-8

"""Since developing this QA module based on raw data from the OverpassAPI would
insole big changes to qat_script and I am not very faimiar with it, I am just
providing a prove of concept in this file."""

import urllib2
import json
import codecs

import pyopening_hours

class Testing():

    OVERPASS_API_URL = u'http://overpass-api.de/api/interpreter'
    OVERPASS_API_TIMEOUT = 60

    # MANDATORY
    def download_urls(self, (zoneBbox, checks)):
        """This method accepts a list of checks and returns
           a list of {"checks": checks list, "url": url} for each request
           that is needed to download all the checks.
           If the errors from all the checks can be downloaded with just
           one url, a list with one dictionary must be returned.
        """

        for check in enumerate(checks):
            osm_tag_key = u'opening_hours'

            overpass_query_url = self.OVERPASS_API_URL \
                + u'?&data=' \
                + urllib2.quote(u"[out:json][timeout:{}][bbox:{},{},{},{}];".format(
                    self.OVERPASS_API_TIMEOUT,
                    zoneBbox[3], zoneBbox[0],
                    zoneBbox[2], zoneBbox[1]
                ) + "(node['{}'];way['{}'];);out body center;".format(osm_tag_key, osm_tag_key))
            print(overpass_query_url)

            try:
                tmp_file_fh = codecs.open('tmp', encoding='UTF-8', mode='r')
            except IOError:
                tmp_file_fh = codecs.open('tmp', encoding='UTF-8', mode='w')
                overpass_answer = urllib2.urlopen(overpass_query_url)
                if overpass_answer.getcode() == 200:
                    overpass_json_answer = overpass_answer.read().decode('UTF-8')
                    print(type(overpass_json_answer))
                    tmp_file_fh.write(overpass_json_answer)
                    tmp_file_fh.close()
                    tmp_file_fh = codecs.open('tmp', encoding='UTF-8', mode='r')
                else:
                    raise Exception('Overpass API status code: ' + overpass_answer.getcode())

            overpass_json_object = json.load(tmp_file_fh)
            interesting_elements = {'warnOnly': [], 'errorOnly': []}
            for element in overpass_json_object['elements']:
                tag_value_to_check = element['tags'][osm_tag_key]
                try:
                    oh = pyopening_hours.OpeningHours(tag_value_to_check)
                except pyopening_hours.ParseException as error:
                    # print(error.message)
                    # print(self._return_tuple_for_element(element))
                    interesting_elements['errorOnly'].append(self._return_tuple_for_element(element))
                    continue
                if oh.getWarnings():
                    # for line in oh.getWarnings():
                        # print('  ' + line)
                    # print(self._return_tuple_for_element(element))
                    interesting_elements['warnOnly'].append(self._return_tuple_for_element(element))

            if 'error' in checks:
                return interesting_elements['warnOnly'] + interesting_elements['errorOnly']
            if 'errorOnly' in checks:
                return interesting_elements['errorOnly']
            if 'warnOnly' in checks:
                return interesting_elements['warnOnly']

    def _return_tuple_for_element(self, element):
        pos = ()
        if 'center' in element:
            pos = (element['center']['lat'], element['center']['lon'])
        else:
            pos = (element['lat'], element['lon'])
        return {
            'type': element['type'],
            'id':   element['id'],
            'lat':  pos[0],
            'lon':  pos[1],
        }

testing = Testing()

print testing.download_urls(((7.040687260055539, 7.17552727165229, 50.750245522813856, 50.730039610993515), ('error', )))

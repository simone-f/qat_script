#! /usr/bin/env jython
#
#  Copyright 2014 Simone F. <groppo8@gmail.com>
#
#  This file is part of qat_script.
#  qat_script is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


#java import
from javax.swing import JOptionPane, SwingWorker
from java.util.concurrent import CancellationException
from java.io import InputStreamReader, BufferedReader, IOException,\
                    FileNotFoundException, File
from java.net import URL, UnknownHostException, SocketException
from java.lang import StringBuilder, System
from javax.xml.parsers import DocumentBuilderFactory
from java.io import StringReader
from org.xml.sax import InputSource
from java.util import Collections

#josm import
from org.openstreetmap.josm import Main

#local import
from tools.tool import Error


##### Download errors thread ###########################################
class DownloadTask(SwingWorker):
    """SwingWorker task used to download data and update progress dialog
    """
    def __init__(self, app):
        self.app = app
        SwingWorker.__init__(self)

    def doInBackground(self):
        """Download errors data
        """
        #Download and parse errors
        self.tool = self.app.downloadingTool
        self.checks = self.app.downloadingChecks

        #Initialize progress property.
        progress = 0
        self.super__setProgress(progress)

        progress = 1
        self.super__setProgress(progress)

        #debug
        offline = False
        writeToFile = False

        if offline or self.tool.isLocal:
            if offline and not self.tool.isLocal:
                fileName = File.separator.join([self.app.SCRIPTDIR,
                                                "%s_errors.gfs" % self.tool.name])
            else:
                fileName = self.tool.fileName
            print "\n  read errors from file: %s" % fileName

            inFile = open(fileName, "r")
            self.app.errorsData = inFile.read()
            inFile.close()
        else:
            try:
                print "\n  url: ", self.app.downloadingUrl
                url = URL(self.app.downloadingUrl)
                uc = url.openConnection()
                ins = uc.getInputStream()
                inb = BufferedReader(InputStreamReader(ins))
                builder = StringBuilder()
                line = inb.readLine()
                while line is not None and not self.isCancelled():
                    builder.append(line)
                    builder.append(System.getProperty("line.separator"))
                    line = inb.readLine()
                if self.isCancelled():
                    if inb is not None:
                        inb.close()
                    if uc is not None:
                        uc.disconnect()
                    return
                inb.close()
                uc.disconnect()
                self.app.errorsData = builder.toString()
            except (UnknownHostException, FileNotFoundException, IOException, SocketException):
                msg = self.app.strings.getString("connection_not_working")
                self.app.downloadAndReadDlg.progressBar.setIndeterminate(False)
                self.app.downloadAndReadDlg.dispose()
                JOptionPane.showMessageDialog(Main.parent, msg)
                self.cancel(True)
                return

        if writeToFile:
            f = open(File.separator.join([self.app.SCRIPTDIR,
                                          "%s_errors.gfs" % self.tool.name]), "w")
            f.write(self.app.errorsData.encode("utf-8"))
            f.close()
            print "errors file saved", File.separator.join([self.app.SCRIPTDIR,
                                                            "%s_errors.gfs" % self.tool.name])

    def done(self):
        try:
            self.get()  # raise exception if abnormal completion
            #print "  done"
            progress = 50
            self.super__setProgress(progress)
            self.app.execute_parsing()
        except CancellationException:
            print "  download canceled."


##### Parse errors thread ##############################################
class ParseTask(SwingWorker):
    """SwingWorker task for errors parsing
    """
    def __init__(self, app):
        self.app = app
        self.tool = self.app.downloadingTool
        self.checks = self.app.downloadingChecks
        SwingWorker.__init__(self)

    def explain(self, nodeList):
        """This method is used to debug the parsing of a new tool error type
           Show the type of node and data of childNodes of a ListNodes
        """
        nodeListLength = nodeList.getLength()
        print "numero child nodes: ", nodeListLength
        for n in range(nodeListLength):
            childNode = nodeList.item(n)
            #print "nodo", childNode
            if childNode.getNodeType() == 1:
                print "ELEMENT, tagName: ", childNode.getTagName()
            elif childNode.getNodeType() == 2:
                print "ATTRIBUTE"
            elif childNode.getNodeType() == 3:
                print "TEXT, nodeValue: ", childNode.getNodeValue()
            else:
                print "none of former"

    def doInBackground(self):
        """Parse downloaded errors
        """
        self.zoneBbox = self.app.zoneBbox

        progress = 51
        self.super__setProgress(progress)

        #temporary dictionary {errorType : errors list}
        self.errors = dict((x.name, []) for x in self.checks)

        result = self.tool.parse_error_file(self)
        if not result:
            return

        for check in self.checks:
            check.bbox = self.zoneBbox
            if len(self.errors[check.name]) == 0:
                check.errors = []
                check.toDo = 0
            else:
                self.append_to_errors(self.errors[check.name], check)

        #print "\nErrors to review: "
        #for check in self.checks:
        #    print "Check:", check.name, "to do:", check.toDo

    def append_to_errors(self, errorsList, check):
        """Clean errors list from duplicate errors and ids that must be
           ignored
        """
        if errorsList[0][0] == "":
            #osmId == "", this tool doesn't give id of OSM objects
            check.errors = [Error(check, e) for e in errorsList]
        else:
            if check.ignoreIds != []:
                #remove OSM objects that the user wants to ignore
                check.errors = [Error(check, e) for e in errorsList if e[0] not in check.ignoreIds]

                #remove duplicate ids
                #check.errors = dict((e.osmId, e) for e in check.errors).values()
            else:
                #copy all errors and remove duplicate ids
                #check.errors = dict((e[0], Error(e)) for e in errorsList).values()
                check.errors = [Error(check, e) for e in errorsList]

            #Remove from the list of errors those that have been reviewed yet
            #while clicking the "Next" button
            check.errors = [e for e in check.errors if e.osmId not in check.reviewedIds]

        #print "\n- errors of selected check in current zone:", [e.osmId for e in check.errors]

        #Randomize the errors so that different users don't start
        #correcting the same errors
        Collections.shuffle(check.errors)

        #Filter errors in favourite zone
        if self.app.favouriteZoneStatus and self.app.favZone.zType != "rectangle":
            #not rectangular favourite area, use jts
            from com.vividsolutions.jts.geom import Coordinate, GeometryFactory
            polygon = self.app.favZone.wktGeom
            errorsInPolygon = []
            for error in check.errors:
                (lat, lon) = error.coords
                point = GeometryFactory().createPoint(Coordinate(lon, lat))
                if polygon.contains(point):
                    if error not in errorsInPolygon:
                        errorsInPolygon.append(error)
            check.errors = errorsInPolygon

        #Apply limits from preferences
        #max number of errors
        limits = []
        if self.app.maxErrorsNumber != "":
            limits.append(self.app.maxErrorsNumber)
        try:
            if self.tool.prefs["limit"] != "":
                limits.append(int(self.tool.prefs["limit"]))
        except:
            pass
        if limits != []:
            check.errors = check.errors[:min(limits)]

        #Reset index of current error
        check.currentErrorIndex = -1
        check.toDo = len(check.errors)

    def done(self):
        try:
            self.get()  # raise exception if abnormal completion
            progress = 100
            self.super__setProgress(progress)
            #Download and parse the next list of checks
            self.app.checksListIdx += 1
            self.app.execute_download()
        except CancellationException:
            print "\n- Parsing canceled."

### utilities ##########################################################
    def check_bbox_width(self, lat, lon, bbox):
        """If a bbox is very little return a bigger bbox with default
           values for width and/or height
        """
        default = 0.0010
        minLon, minLat, maxLon, maxLat = bbox
        if maxLon - minLon < default:
            minLon = lon - default
            maxLon = lon + default
        if maxLat - minLat < default:
            minLat = lat - default
            maxLat = lat + default
        return [minLon, minLat, maxLon, maxLat]

    def build_bbox(self, lat, lon):
        """Return a bbox of a chosen size from a couple of coordinates
        """
        # d_lon and d_lat: limits of the area downloaded by JOSM
        # for an error
        d_lat = 0.0010
        d_lon = 0.0010
        return (lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat)

    def extractRootElement(self):
        """Setup an XML parser
        """
        dbf = DocumentBuilderFactory.newInstance()
        dbf.setNamespaceAware(1)
        domparser = dbf.newDocumentBuilder()
        doc = domparser.parse(InputSource(StringReader(self.app.errorsData)))
        rootElement = doc.getDocumentElement()
        return rootElement

    def print_error(self, check, bbox, osmId):
        """Print error info. Old code for debugging
        """
        print "\n*New feature"
        print "check: ", check.title
        print "coordinates: ", bbox
        print "osmId: ", osmId
        raw_input("read next?")

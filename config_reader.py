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
from java.util import Properties
from java.io import FileInputStream, FileOutputStream, File
from java.lang import Integer, NumberFormatException

#local import
from gui.NewZoneDialog import Zone


##### Configurations ###################################################
class ConfigLoader:
    def __init__(self, app):
        """Read preferences from config.properties file
        """
        self.app = app
        app.SCRIPTWEBSITE = "http://wiki.openstreetmap.org/wiki/Quality_Assurance_Tools_script"
        app.GITWEBSITE = "https://github.com/simone-f/qat_script/tree/development"
        app.users = {}

        #Script and tools data versions
        #mode = "stable" | "development"
        app.mode = "development"
        if app.mode == "stable":
            app.scriptVersionUrl = "https://raw.githubusercontent.com/simone-f/qat_script/master/VERSIONS.properties"
            app.toolsListUrl = "https://raw.githubusercontent.com/simone-f/qat_script/master/tools/tools_list.properties"
            app.jarBaseUrl = "https://github.com/simone-f/qat_script/raw/master/tools/jar"
        elif app.mode == "development":
            app.scriptVersionUrl = "https://raw.githubusercontent.com/simone-f/qat_script/development/VERSIONS.properties"
            app.toolsListUrl = "https://raw.githubusercontent.com/simone-f/qat_script/development/tools/tools_list.properties"
            app.jarBaseUrl = "https://github.com/simone-f/qat_script/raw/development/tools/jar"
        else:
            app.scriptVersionUrl = ""
            app.toolsListUrl = ""
            app.jarBaseUrl = ""

        #Read script and tools version
        self.versionsFileName = File.separator.join([app.SCRIPTDIR,
                                                "VERSIONS.properties"])
        app.SCRIPTVERSION, app.TOOLSVERSION = self.read_versions()

        #Configurations in config.properties
        app.configFileName = File.separator.join([app.SCRIPTDIR,
                                                  "configuration",
                                                  "config.properties"])
        app.properties = Properties()
        fin = FileInputStream(app.configFileName)
        app.properties.load(fin)

        #check for update
        app.checkUpdate = app.properties.getProperty("check_for_update")

        #active tools names
        app.toolsStatus = {}
        for key in app.properties.keys():
            if key.startswith("tool.") \
                and len(key.split(".")) == 2:
                toolName = key.split(".")[1]
                if app.properties.getProperty(key) == "on":
                    value = True
                else:
                    value = False
                app.toolsStatus[toolName] = value
        app.toolsStatus["favourites"] = True

        #layers managing
        app.layersModes = ("hide_other_layers",
                           "remove_other_layers",
                           "hide_layers_with_the_same_name",
                           "remove_layers_with_the_same_name")
        app.layersMode = app.properties.getProperty("layers_mode")

        #max errors number
        app.maxErrorsNumber = app.properties.getProperty("max_errors_number")
        if app.maxErrorsNumber != "":
            app.maxErrorsNumber = int(app.maxErrorsNumber)

        # warning for tools with limited downloadable errors
        if app.properties.getProperty("favourite_area.errors_warning") == "on":
            app.favAreaErrorsWarning = True
        else:
            app.favAreaErrorsWarning = False

        #tools preferences
        app.toolsPrefs = {}
        for key in app.properties.keys():
            if key.startswith("tool") and len(key.split(".")) > 2:
                toolName = key.split(".")[1]
                toolPref = key.split(".")[2]
                value = app.properties.getProperty(key)
                if toolName not in app.toolsPrefs:
                    app.toolsPrefs[toolName] = {}
                app.toolsPrefs[toolName][toolPref] = value
        if hasattr(app, "allTools"):
            #check if tools have been already instantiated
            #prefs of a tool are stored as tool attribute
            for tool in app.allTools:
                if hasattr(tool, "prefs"):
                    tool.update_preferences()

        #favourite zones
        # status
        if app.properties.getProperty("favourite_area.status") == "on":
            app.favouriteZoneStatus = True
        else:
            app.favouriteZoneStatus = False

        # name
        app.favZoneName = app.properties.getProperty("favourite_area.name")

        fin.close()

        if app.favouriteZoneStatus:
            if app.zones is None:
                #it is not necessary to read again the zones when preferences change
                load_zones(app)

    def read_versions(self):
        versionsProperties = Properties()
        fin = FileInputStream(self.versionsFileName)
        versionsProperties.load(fin)
        scriptVersion = versionsProperties.getProperty("script")
        toolsVersion = versionsProperties.getProperty("tools")
        fin.close()
        return scriptVersion, toolsVersion

    def save_versions(self):
        print "save versions"
        versionsProperties = Properties()
        outFile = FileOutputStream(self.versionsFileName)
        versionsProperties.setProperty("script", self.app.SCRIPTVERSION)
        versionsProperties.setProperty("tools", self.app.TOOLSVERSION)
        versionsProperties.store(outFile, None)
        outFile.close()


def load_zones(app):
    """Read favourite zones
    """
    app.zones = []
    favZonesDir = File(File.separator.join([app.SCRIPTDIR,
                                            "configuration",
                                            "favourite_zones"]))
    for zoneFile in sorted(favZonesDir.listFiles()):
        name = zoneFile.getName()[:-4]
        fileName = zoneFile.getPath()
        zoneFile = open(fileName)
        fileContent = zoneFile.read()
        if len(fileContent.split("|")) == 2:
            geomString, country = fileContent.split("|")
            country = country.upper().decode("utf-8")
        else:
            geomString = fileContent
            country = ""
        zoneFile.close()
        zType = "rectangle"
        try:
            Integer.parseInt(geomString[0])
        except NumberFormatException:
            zType = "polygon"
        zone = Zone(app, name, zType, geomString, country)
        app.zones.append(zone)
        if name == app.favZoneName:
            app.favZone = zone

    #Fav zone is active but its data is missing
    if app.favouriteZoneStatus and app.favZone is None:
        app.favouriteZoneStatus = False

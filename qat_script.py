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

"""This script downloads errors from some quality assurance tools for
   OpenStreetMap, shows them as markers in JOSM and lets the user review
   each error in sequence.

   Dependencies: JOSM Scripting Plugin (User:Gubaer), Jython engine,
   JOSM jts Plugin
"""


#java import
from javax.swing import JOptionPane, JPanel, JLabel, JTextField
from java.beans import PropertyChangeListener
from java.util import Locale, ResourceBundle
from java.io import FileNotFoundException,\
                    FileOutputStream, File
from java.net import URL, UnknownHostException, SocketException,\
                    URLClassLoader
from java.lang import Runnable, String
from java.text import MessageFormat
from java.awt import Desktop, GridLayout

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.plugins import PluginHandler
from org.openstreetmap.josm.Main.main import menu
from org.openstreetmap.josm.plugins import PluginHandler
from org.openstreetmap.josm.gui.layer import OsmDataLayer
from org.openstreetmap.josm.data.osm import DataSet, User
from org.openstreetmap.josm.data.gpx import GpxData, WayPoint
from org.openstreetmap.josm.data.coor import LatLon
from org.openstreetmap.josm.gui.util import GuiHelper
from org.openstreetmap.josm.actions import AutoScaleAction
from org.openstreetmap.josm.data.osm import OsmPrimitiveType

#python import
import sys
from jarray import array


def get_script_directory_from_scripting_plugin():
    """Get the qat-script directory path from Scripting Plugin
       MostRecentlyRunScriptsModel
    """
    from org.openstreetmap.josm.plugins.scripting.ui import MostRecentlyRunScriptsModel
    action = MostRecentlyRunScriptsModel.getInstance().getRunScriptActions()[0]
    scriptDir = action.getValue(action.SHORT_DESCRIPTION)
    if scriptDir.endswith('qat_script.py'):
        return scriptDir.strip('qat_script.py')
    return None


def check_if_script_in_default_directory():
    """Check if qat_script directory is a subdir of Scripting Plugin directory
    """
    print "- Checking if qat_script directory is in scripting directory"
    scriptingPluginDir = PluginHandler.getPlugin("scripting").getPluginDir()
    scriptDir = File.separator.join([scriptingPluginDir, "qat_script"])
    if File(scriptDir).exists() and File(scriptDir).isDirectory():
        print "directory found."
        return scriptDir
    else:
        print "directory not found."
        return None


def move_script_warning():
    """Warn the user to move qat_script directory into Scripting Plugin
       directory
    """
    scriptingPluginDir = PluginHandler.getPlugin("scripting").getPluginDir()
    pane = JPanel(GridLayout(3, 1, 5, 5))
    warningTitle = "Warning: qat_script directory not found"
    pane.add(JLabel("Please, move qat_script directory to the following location and start the script again:\n"))
    defaultPathTextField = JTextField(scriptingPluginDir,
                                      editable=0,
                                      border=None,
                                      background=None)
    pane.add(defaultPathTextField)

    if not Desktop.isDesktopSupported():
        JOptionPane.showMessageDialog(
            Main.parent,
            pane,
            warningTitle,
            JOptionPane.WARNING_MESSAGE)
    else:
        #add a button to open default path with the files manager
        pane.add(JLabel("Do you want to open this folder?"))
        options = ["No", "Yes"]
        answer = JOptionPane.showOptionDialog(
            Main.parent,
            pane,
            warningTitle,
            JOptionPane.YES_NO_OPTION,
            JOptionPane.QUESTION_MESSAGE,
            None,
            options,
            options[1])
        if answer == 1:
            Desktop.getDesktop().open(File(scriptingPluginDir))


##### Application ######################################################
class App(PropertyChangeListener):
    """qat_script main class
    """
    def __init__(self):
        self.SCRIPTDIR = SCRIPTDIR

        #Localization
        urls = [File(File.separator.join([self.SCRIPTDIR, "data", "locale"])).toURI().toURL()]
        loader = URLClassLoader(urls)
        currentLocale = Locale.getDefault()
        self.strings = ResourceBundle.getBundle("MessagesBundle",
                                                 currentLocale,
                                                 loader)

        #Read config
        self.favZone = None
        self.zones = None
        self.config = ConfigLoader(self)

        """Build tools instances"""
        self.allTools = AllTools(self).tools
        for tool in self.allTools:
            if tool.name == "favourites":
                self.favouritesTool = tool
                break
        self.realTools = [tool for tool in self.allTools if tool.name not in ("favourites", "localfile")]

        #remove tools disabled from config file
        self.tools = [tool for tool in self.allTools if tool.isActive or
                      tool.name in ("favourites")]

        #add favourite checks to Favourites tool
        if "favourites" in self.toolsPrefs:
            favChecks = self.toolsPrefs["favourites"]["checks"]
            if favChecks != "":
                for favCheck in favChecks.split("|"):
                    (toolName, viewName, checkName) = favCheck.split(".")
                    for tool in self.tools:
                        if tool.name == toolName:
                            for view in tool.views:
                                if view.name == viewName:
                                    for check in view.checks:
                                        if check.name == checkName:
                                            self.favouritesTool.views[0].checks.append(check)

        """Build dialog for manual reporting of false positive"""
        self.falsePositiveDlg = FalsePositiveDialog(
            Main.parent,
            self.strings.getString("false_positives_title"),
            True, self)

        """Build qat_script toggleDialog"""
        #BUG: it steals icon from validator.
        #Is it possible ot use an icon not from 'dialogs' dir?
        icon = "validator.png"
        self.dlg = QatDialog(self.strings.getString("qat_dialog_title"),
                             icon,
                             "Show ",
                             None,
                             250,
                             self)
        self.create_new_dataset_if_empty()
        Main.map.addToggleDialog(self.dlg)

        """Build processing dialog"""
        self.downloadAndReadDlg = DownloadAndReadDialog(Main.parent,
                                      self.strings.getString("download_dialog_title"),
                                      False,
                                      self)

        """Build quality assurance tools menu"""
        self.menu = QatMenu(self, "QA Tools")
        menu.add(self.menu)
        menu.repaint()

        """Initialization"""
        #Read ids of OSM objects that the user wants to be ignored
        self.ignore_file = File.separator.join([self.SCRIPTDIR,
                                                "data",
                                                "ignoreids.csv"])
        self.read_ignore()
        self.falsePositive = []     # info regarding false positive

        self.selectedTool = self.tools[0]
        self.selectedView = self.selectedTool.views[0]      # first view
        self.selectedTableModel = self.selectedView.tableModel
        self.selectedChecks = []
        self.downloadingChecks = []
        self.clickedError = None
        self.errorsData = None
        self.zoneBbox = None        # bbox of current JOSM view
        self.selectedError = None
        self.url = None             # url of errors
        self.errorLayers = []       # list of layers with error markers
        self.selectionChangedFromMenuOrLayer = False
        self.dlg.toolsCombo.setSelectedIndex(0)
        print "\nINFO: Quality Assurance Tools script is running: ", self.SCRIPTVERSION

        # Check if using the latest version
        if self.checkUpdate == "on":
            update_checker.Updater(self, "auto")

    def save_config(self):
        """Save preferences to config file
        """
        out = FileOutputStream(app.configFileName)
        app.properties.store(out, None)
        out.close()
        #load new preferences
        self.config = ConfigLoader(self)

    def get_mapview(self):
        """Returns the Main.main.map.mapView if present
        """
        if Main.main and Main.main.map:
            return Main.main.map.mapView
        else:
            return None

    def create_new_dataset_if_empty(self):
        """Create a new mapView if there is None
        """
        self.mv = self.get_mapview()
        if self.mv is None:
            Main.main.addLayer(OsmDataLayer(DataSet(),
                                            OsmDataLayer.createNewName(),
                                            None))
            self.mv = self.get_mapview()
            GuiHelper.executeByMainWorkerInEDT(ZoomToDownloadInPref())

    def on_selection_changed(self, source, selection=None, error=None):
        """Change the selected tools, views, and checks according to
           the user input from QA Tools menu, errors layer or dialog
        """
        if source in ("menu", "layer", "add favourite"):
            tool, view, check = selection
            self.selectedTool = tool
            self.selectedView = view
            self.selectedChecks = [check]
            self.selectedTableModel = self.selectedView.tableModel
            self.dlg.change_selection(source)
        else:
            #get selected tool
            self.selectedTool = self.dlg.toolsComboModel.getSelectedItem()
            #get selected view
            if source in ("toolsCombo", "viewsCombo"):
                if source == "toolsCombo":
                    self.selectedView = self.selectedTool.views[0]
                elif source == "viewsCombo":
                    viewIndex = self.dlg.viewsCombo.selectedIndex
                    self.selectedView = self.selectedTool.views[viewIndex]
                    self.selectedTableModel = self.selectedView.tableModel
                self.dlg.change_selection(source)
                return
            elif source == "checksTable":
                checksIndexes = self.dlg.checksTable.getSelectedRows()
                if len(checksIndexes) != 0:
                    self.selectedChecks = []
                    for index in checksIndexes:
                        self.selectedChecks.append(self.selectedView.checks[index])
                    self.reset_selected_error()
                    self.dlg.update_checks_buttons()

        #debug
        #self.print_selection()

        #Procede after selection
        if source == "menu":
            #Download errors, parse them, write the number in table
            #and show them in a new layer
            self.on_downloadBtn_clicked()
        elif source == "layer":
            self.goToNext(error)

    def print_selection(self):
        """Print on terminal the new selection
        """
        print "\n* Selection changed."
        print "- Tool : ", self.selectedTool.title
        print "- View : ", self.selectedView.title
        if self.selectedChecks != []:
            print "- Checks: ", ",".join([check.title for check in self.selectedChecks])
        else:
            print "-Check", None

    def get_frame_bounds(self):
        """Get bbox of current visible area in JOSM
        """
        bounds = self.mv.getRealBounds()

        minCoord = bounds.getMin()
        maxCoord = bounds.getMax()

        minLon = minCoord.lon()
        minLat = minCoord.lat()
        maxLon = maxCoord.lon()
        maxLat = maxCoord.lat()
        return [minLon, minLat, maxLon, maxLat]

    def read_ignore(self):
        """Read errors that the user ignored and add them as
           attributes to a Check instance
        """
        if File(self.ignore_file).exists():
            ifile = open(self.ignore_file, "r")
            rows = ifile.readlines()
            if rows != [] and rows != ["\n"]:
                for row in rows:
                    info = row.strip().replace("\"", "").split("\t")
                    toolTitle, viewName, checkName = info[:3]
                    ids = info[3:]
                    for tool in self.tools:
                        if tool.title == toolTitle:
                            for view in tool.views:
                                if view.name == viewName:
                                    for check in view.checks:
                                        if check.name == checkName:
                                            check.ignoreIds = ids
            ifile.close()

    def reset_selected_error(self, source=None):
        """Reset currently selected error
        """
        self.selectedError = None

        #Update information in gui
        if len(self.selectedChecks) == 1 and self.selectedChecks[0].toDo == 0:
            statusText = "review end"
            errorTabStatus = False
        elif len(self.selectedChecks) > 1 or \
             (len(self.selectedChecks) == 1 and self.selectedChecks[0].errors is None) or \
             self.clickedError is not None:
            statusText = "reset"
            errorTabStatus = False
        else:
            #some error still needs to be corrected
            #in the selected check
            statusText = "show stats"
            errorTabStatus = True
        self.dlg.update_text_fields(statusText)
        self.dlg.activate_error_tab(errorTabStatus)

        self.dlg.update_error_buttons(statusText)

##### Donwload and parse the selected error type #######################
    def on_downloadBtn_clicked(self, event=None):
        """On download button clicked download the errors in current or
           favourite area
        """
        #Get bbox from JOSM mapview
        self.mv = self.get_mapview()
        if self.mv is None:
            self.create_new_dataset_if_empty()
            Main.map.addToggleDialog(self.dlg)
            if self.favouriteZoneStatus:
                self.zoneBbox = self.favZone.bbox
            else:
                tmpbbox = [float(x) for x in Main.pref.get("osm-download.bounds").split(";")]
                self.zoneBbox = [tmpbbox[1], tmpbbox[0], tmpbbox[3], tmpbbox[2]]
        else:
            if self.favouriteZoneStatus:
                self.zoneBbox = self.favZone.bbox
            else:
                self.zoneBbox = self.get_frame_bounds()

        #Warn the user when using a polygon or boundaries as favoutire area
        #for the first time, and a tool with a limited number of errors
        #that can be downloaded (KeepRight, Osmose) it could happen that
        # not all the errors are shown
        if self.favouriteZoneStatus and self.favZone.zType in ("polygon", "boundary")\
            and self.favAreaErrorsWarning and self.selectedTool.name in ("osmose", "keepright"):
            msg = self.strings.getString("favourite_area_errors_warning")
            JOptionPane.showMessageDialog(Main.parent, "<html><body><p style='width: 400px;'>%s</body></html>" % msg)
            self.properties.setProperty("favourite_area.errors_warning", "off")
            self.save_config(self)

        #Ask confirmation before errors downloading
        #msg = "Do you really want to downalod error data now?"
        #answer = JOptionPane.showConfirmDialog(Main.parent, msg)
        #if answer != 0:
        #    return

        #Show dialog with downloading and parsing progressbar
        self.downloadAndReadDlg.visible = True
        self.downloadAndReadDlg.progressBar.setIndeterminate(True)

        #Create download queue
        self.queue = []
        downloadsDict = {}
        for check in self.selectedChecks:
            tool = check.tool
            if tool not in downloadsDict:
                downloadsDict[tool] = []
            downloadsDict[tool].append(check)
        self.queue = []
        for tool, checksList in downloadsDict.iteritems():
            if tool.isLocal and tool.name != "favourites":
                self.queue = [{"checks": checksList, "url": ""}]
            else:
                self.queue.extend(tool.download_urls((self.zoneBbox,
                                                      checksList)))

        #self.print_queue()

        #Download and parse errors
        self.checksListIdx = 0
        self.execute_download()

    def print_queue(self):
        print "\nQueue:"
        for item in self.queue:
            print "\ntool:", item["checks"][0].tool.title
            print "checks:", ", ".join([c.title for c in item["checks"]])
            print "url:", item["url"]

    def execute_download(self):
        """Execute task for errors downloading
        """
        if self.checksListIdx <= len(self.queue) - 1:
            checksList = self.queue[self.checksListIdx]["checks"]
            self.downloadingTool = checksList[0].tool
            self.downloadingChecks = checksList
            self.downloadingUrl = self.queue[self.checksListIdx]["url"]
            self.status = "downloading"
            self.downloadTask = DownloadTask(self)
            self.downloadTask.addPropertyChangeListener(self)
            self.downloadTask.execute()

    def execute_parsing(self):
        """Execute for errors parsing
        """
        self.status = "parsing"
        self.parseTask = ParseTask(self)
        self.parseTask.addPropertyChangeListener(self)
        #debug
        #self.t1 = time.time()
        self.parseTask.execute()

    def on_cancelBtn_clicked(self, e):
        """Cancel the task (downloading or parsing) when cancel button
           is pressed
        """
        #print "\mCancel button clicked: ", self.status
        self.downloadAndReadDlg.dispose()
        if self.status == "downloading":
            self.downloadTask.cancel(True)
        elif self.status == "parsing":
            self.parseTask.cancel(True)

    def propertyChange(self, e):
        """Invoked when task's (download or parsing) progress property
           changes.
        """
        if e.propertyName == "progress":
            if self.status == "downloading":
                progress = e.newValue
                if progress == 1:
                    print "  downloading..."
                    self.downloadAndReadDlg.progressLbl.text = self.strings.getString("Downloading...")
            elif self.status == "parsing":
                progress = e.newValue
                if progress == 51:
                    self.downloadAndReadDlg.progressLbl.text = self.strings.getString("Parsing...")
                    print "  parsing..."
                elif progress == 100:
                    #debug
                    #print "\n- errors data downloaded and parsed"
                    #t2 = time.time()
                    #print self.t1, t2, type(t2), type (self.t1)
                    #print '\n==took %0.3f ms' % ((t2-self.t1)*1000.0)
                    self.downloadAndReadDlg.progressBar.setIndeterminate(True)
                    self.downloadAndReadDlg.dispose()
                    #Reset selected error
                    self.selectedError = None
                    self.update_gui_after_download()
                    self.downloadingChecks = []

    def update_gui_after_download(self):
        """After the errors have been downloaded and parsed,
           update checksTable and create a layer with error
        """
        #Update checksTable
        for check in self.selectedChecks:
            view = check.view
            errorsNumber = len(check.errors)
            rowIndex = view.checks.index(check)
            view.tableModel.setValueAt(errorsNumber, rowIndex, 2)
            #favourite checks
            if check in self.favouritesTool.views[0].checks:
                rowIndex = self.favouritesTool.views[0].checks.index(check)
                self.favouritesTool.views[0].tableModel.setValueAt(errorsNumber, rowIndex, 2)

        errorsNumber = sum(len(c.errors) for c in self.selectedChecks if c.errors is not None)
        if errorsNumber == 0:
            #Text fields
            if self.favouriteZoneStatus:
                checksText = self.strings.getString("No_errors_in_favourite_area.")
            else:
                checksText = self.strings.getString("No_errors_in_current_area.")
            self.dlg.set_checksTextFld_color("green")
            self.dlg.checksTextFld.text = checksText
            self.dlg.errorTextFld.text = ""

            #Error tab
            self.dlg.activate_error_tab(False)
        else:
            #Text fields
            checksText = "%s " % str(errorsNumber)
            if errorsNumber == 1:
                checksText += self.strings.getString("error.")
            else:
                checksText += self.strings.getString("errors.")
            if len(self.downloadingChecks) == 1:
                errorText = checksText
            else:
                errorText = ""

            self.dlg.set_checksTextFld_color("red")
            self.dlg.checksTextFld.text = checksText
            self.dlg.errorTextFld.text = errorText

            #Checks buttons
            self.dlg.update_checks_buttons()

            #Error tab
            self.dlg.activate_error_tab(True)
            self.dlg.tabbedPane.setSelectedIndex(0)

        self.dlg.update_statsPanel_status()

        #Create error layers
        newlayers = []
        for check in self.selectedChecks:
            if len(check.errors) != 0:
                errorLayer = self.create_layer(check)
                newlayers.append(errorLayer)
        self.errorLayers.extend(newlayers)

        #If working on the favourite area, zoom to it after showing errors
        if self.favouriteZoneStatus:
            josmUrl = "http://127.0.0.1:8111/"
            josmUrl += "zoom?left=%f&bottom=%f&right=%f&top=%f" % tuple(self.selectedChecks[0].bbox)
            self.send_to_josm(josmUrl)

    def create_layer(self, check):
        """Create a layer with errors
        """
        gpxdata = GpxData()
        for error in check.errors:
            (lat, lon) = error.coords
            gpxdata.waypoints.add(WayPoint(LatLon(lat, lon)))
        errorLayer = ErrorLayer(gpxdata, self, check)
        #Manage other layers
        removeLayers = []
        newLayersNames = [x.title for x in self.selectedChecks]

        for layer in self.errorLayers:
            if self.layersMode == "hide_other_layers":
                layer.setVisible(False)
            elif self.layersMode == "remove_other_layers":
                removeLayers.append(layer)
            elif self.layersMode == "hide_layers_with_the_same_name" and layer.name in newLayersNames:
                layer.setVisible(False)
            elif self.layersMode == "remove_layers_with_the_same_name" and layer.name in newLayersNames:
                removeLayers.append(layer)
        for layer in removeLayers:
            self.errorLayers.remove(layer)
            self.mv.removeLayer(layer)

        self.mv.addLayer(errorLayer)
        self.mv.moveLayer(errorLayer, 0)
        self.mv.addMouseListener(errorLayer)
        return errorLayer

##### Errors fixing ####################################################
    def on_startBtn_clicked(self, event):
        """Activate second tab
        """
        self.dlg.activate_error_tab(True)
        self.dlg.tabbedPane.setSelectedIndex(1)
        if self.selectedError is None:
            #go straight to the first error
            self.goToNext()

    def on_errorInfoBtn_clicked(self, event):
        """Open a dialog with information about currently selected error.
           The text can be copied, so to inform the user who made the error
        """
        if not hasattr(self, "errorInfoDlg"):
            self.errorInfoDlg = ErrorInfoDialog(self)
        self.errorInfoDlg.update()

    def on_correctedBtn_clicked(self, event):
        """Tell the tool server that selected error has been corrected
        """
        check = self.selectedError.check
        tool = check.tool
        if tool.fixedFeedbackMode:
            #the tool supports automatic reporting
            tool.sayBugFixed(self.selectedError, check)
            self.editDone()
        else:
            return

    def on_falsePositiveBtn_clicked(self, event):
        """Tell the tool server that selected error is a false positive
        """
        check = self.selectedError.check
        tool = check.tool
        if tool.falseFeedbackMode == "url":
            #the tool supports automatic reporting
            if self.properties.getProperty("false_positive_warning.%s" % tool.name) == "on":
                messageArguments = array([tool.title], String)
                formatter = MessageFormat("")
                formatter.applyPattern(self.strings.getString("false_positive_confirmation"))
                msg = formatter.format(messageArguments)
                options = [self.strings.getString("yes_do_not_ask_the_next_time"),
                           self.strings.getString("Yes"),
                           self.strings.getString("No")]
                answer = JOptionPane.showOptionDialog(Main.parent,
                    msg,
                    self.strings.getString("flagging_a_false_positive"),
                    JOptionPane.YES_NO_CANCEL_OPTION,
                    JOptionPane.WARNING_MESSAGE,
                    None,
                    options,
                    options[2])
                if answer == 0:
                    #don't ask again
                    self.properties.setProperty("false_positive_warning.%s" % tool.name,
                                                "off")
                    self.save_config(self)
                elif answer == 2:
                    #don't flag as false positive
                    return
            tool.sayFalseBug(self.selectedError, check)

        elif tool.falseFeedbackMode == "msg":
            #the tool supports manual reporting of false positives
            if self.properties.getProperty("false_positive_warning.%s" % tool.name) == "on":
                messageArguments = array([tool.title], String)
                formatter = MessageFormat("")
                formatter.applyPattern(self.strings.getString("manual_false_positive_confirmation"))
                msg = formatter.format(messageArguments)
                options = [self.strings.getString("yes_do_not_ask_the_next_time"),
                           self.strings.getString("Yes"),
                           self.strings.getString("No")]
                answer = JOptionPane.showOptionDialog(Main.parent,
                    msg,
                    self.strings.getString("flagging_a_false_positive"),
                    JOptionPane.YES_NO_CANCEL_OPTION,
                    JOptionPane.WARNING_MESSAGE,
                    None,
                    options,
                    options[2])
            errorInfo = [tool.title,
                         check.name,
                         self.selectedError.errorId,
                         self.selectedError.osmId]
            self.falsePositiveDlg.tableModel.addRow(errorInfo)
        else:
            #the tool does not support feedback
            return
        self.editDone()

    def on_ignoreBtn_clicked(self, event):
        """Ignore this osm object the next time
        """
        osmId = self.selectedError.osmId
        check = self.selectedError.check
        check.ignoreIds.append(osmId)

        check.done = True
        check.reviewedIds.append(osmId)

        print "Save file with ids that should be ignored the next time"
        #This file is completely rewritten every time ignoreBtn is clicked
        ofile = open(self.ignore_file, "w")
        for tool in self.tools:
            for view in tool.views:
                for check in view.checks:
                    if check.ignoreIds != []:
                        row = '"%s"\t"%s"\t"%s"\t' % (tool.title, view.name, check.name)
                        row += "\t".join(['"%s"' % osmid for osmid in check.ignoreIds])
                        row += "\n"
                        ofile.write(row)
        ofile.close()
        self.editDone()

    def on_nextBtn_clicked(self, event=None):
        """Move to the next error
        """
        if self.selectedError is None:
            #this is the first time the button is clicked
            self.goToNext()
        else:
            #an error has been reviewed
            self.editDone()

    def editDone(self):
        """After an error has been corrected or ignored or reported as
           fixed or false positive
        """
        check = self.selectedError.check
        view = check.view
        if not self.selectedError.done:
            #(the error could have been already marked as done
            #if the user clicked over an already reviewed error)
            self.selectedError.done = True
            check.reviewedIds.append(self.selectedError.osmId)
            check.toDo -= 1
            #update checksTable
            errorsNumber = len(check.errors)
            counter = "%d/%d" % (check.toDo, errorsNumber)
            rowIndex = view.checks.index(check)
            view.tableModel.setValueAt(counter, rowIndex, 2)
            #favourite checks
            if check in self.favouritesTool.views[0].checks:
                rowIndex = self.favouritesTool.views[0].checks.index(check)
                self.favouritesTool.views[0].tableModel.setValueAt(counter, rowIndex, 2)

        if self.clickedError is not None:
            self.reset_selected_error()
            return
        else:
            check.currentErrorIndex += 1
            if check.toDo == 0:
                print "End of review."
                if check.bbox is not None:
                    #Zoom back to the reviewed area
                    josmUrl = "http://127.0.0.1:8111/"
                    josmUrl += "zoom?left=%f&bottom=%f&right=%f&top=%f" % tuple(check.bbox)
                    self.send_to_josm(josmUrl)
                self.reset_selected_error()
                self.dlg.update_checks_buttons()
                return
        self.goToNext()

    def goToNext(self, clickedError=None):
        """Send JOSM to the next error
        """
        if hasattr(self, "errorInfoDlg") and self.errorInfoDlg.isVisible():
            self.errorInfoDlg.hide()

        print "\n- Errors to review: ", self.selectedChecks[0].toDo
        self.clickedError = clickedError    # marker clicked
        errors = self.selectedChecks[0].errors

        if clickedError is not None:
            #An error has been selected with mouse click from JOSM view,
            #just zoom to the clicked marker and show error info
            self.selectedError = clickedError
            self.dlg.activate_error_tab(True)
            self.dlg.tabbedPane.setSelectedIndex(1)
        else:
            #Prepare the next error from the errors list
            i = self.selectedChecks[0].currentErrorIndex + 1
            self.selectedError = errors[i]
            if self.selectedError.done:
                #this error has already been reviewed by clicking on
                #its marker
                self.selectedChecks[0].currentErrorIndex = i
                self.goToNext()
                return

        #Collect error info
        errorInfo = ""
        osmId = self.selectedError.osmId
        if osmId != "":
            osmIdExtended = osmId
            osmIdExtended = osmIdExtended.replace("n", "node")
            osmIdExtended = osmIdExtended.replace("w", "way")
            osmIdExtended = osmIdExtended.replace("r", "relation")
            osmIdExtended = osmIdExtended.replace("_", ",")
            errorInfo = "%s %s, " % (self.strings.getString("editing"),
                                     osmIdExtended)
        bbox = self.selectedError.bbox

        #JOSM remote control url
        josmUrl = "http://127.0.0.1:8111/"
        josmUrl += "load_and_zoom?"
        bboxString = "left=%f&bottom=%f&right=%f&top=%f&zoom_mode=download" % tuple(bbox)
        josmUrl += bboxString
        if osmId != "":
            #we also know the OSM id. Select the object after download
            josmUrl += "&select=%s" % osmIdExtended
        #send command to JOSM
        response = self.send_to_josm(josmUrl)
        if response is False:
            print "josm is not running"
            return

        #Update user name of selected error
        if osmId != "":
            singleOsmId = osmId.split("_")[0]
            mv = self.get_mapview()
            if mv is not None:
                GuiHelper.executeByMainWorkerInEDT(GetUserOfSelectedPrimitive(self,
                                                                              mv,
                                                                              singleOsmId))

        #Update text fields and buttons
        self.dlg.update_checks_buttons()
        self.dlg.update_error_buttons("new error")
        self.dlg.update_text_fields("show stats", errorInfo)

    def send_to_josm(self, url):
        """Remote control command to make JOSM download the area nearby
           the error
        """
        try:
            url = URL(url)
            uc = url.openConnection()
            uc.getInputStream()
            return True
        except UnknownHostException:
            return False
        except FileNotFoundException:
            return False
        except SocketException:
            print "\n* Please, enable JOSM remote from Preferences"
            return False

    def open_preferences(self, mode):
        try:
            self.preferencesFrame
        except AttributeError:
            #Read zones
            if self.zones is None:
                load_zones(self)
            #build preferences dialog
            self.preferencesFrame = PreferencesFrame(
                None,
                self.strings.getString("preferences_title"),
                #True,
                self)
        self.preferencesFrame.update_gui_from_preferences()
        self.preferencesFrame.show()

        if mode == "from favourite area indicator":
            self.preferencesFrame.tabbedPane.setSelectedIndex(1)


class ZoomToDownloadInPref(Runnable):
    def __init__(self):
        self.func = AutoScaleAction.autoScale

    def run(self):
        self.func("download")


class GetUserOfSelectedPrimitive(Runnable):
    def __init__(self, app, mv, osmId):
        self.app = app
        self.mv = mv
        self.osmId = osmId

    def run(self):
        numericOsmId = int(self.osmId[1:])
        osmTypes = {"n": OsmPrimitiveType.NODE,
                    "w": OsmPrimitiveType.WAY,
                    "r": OsmPrimitiveType.RELATION}
        osmType = osmTypes[self.osmId[0]]
        osmObject = self.mv.editLayer.data.getPrimitiveById(numericOsmId, osmType)
        if osmObject is not None and osmObject.getUser() is not None and\
           osmObject.getUser() != User.getAnonymous():
            self.app.selectedError.user = osmObject.getUser()
            self.app.selectedError.changeset = str(osmObject.getChangesetId())


########################################################################
"""
#For debugging:
sys.modules.clear()
index = menu.getMenuCount()
menu.remove(index - 1)
"""
SCRIPTDIR = None
try:
    #Try to catch scriptdir from scripting plugin
    SCRIPTDIR = get_script_directory_from_scripting_plugin()
except:
    pass

if SCRIPTDIR is None:
    #Check if qat_script directory is in Scripting Plugin directory
    SCRIPTDIR = check_if_script_in_default_directory()

if SCRIPTDIR is None:
    #Pop up a message telling the user to move the script
    #to a default dir
    move_script_warning()
else:
    #Procede with local import
    #print "- qat_script directory:", SCRIPTDIR
    sys.path.append(SCRIPTDIR)

    #Check that jts plugin is present (needed for favourite zone feature)
    if PluginHandler.getPlugin("jts") is None:
        JOptionPane.showMessageDialog(Main.parent,
                                      "Please, install 'jts' plugin from JOSM Preferences.",
                                      "Missing plugin: jts",
                                      JOptionPane.WARNING_MESSAGE)
    else:
        from config_reader import ConfigLoader, load_zones
        import update_checker
        from tools.allTools import AllTools
        from download_and_parse import DownloadTask, ParseTask
        from gui.QatMenu import QatMenu
        from gui.QatDialog import QatDialog
        from gui.OtherDialogs import DownloadAndReadDialog,\
                                     FalsePositiveDialog
        from gui.ErrorInfoDialog import ErrorInfoDialog
        from gui.PreferencesFrame import PreferencesFrame
        from error_layer import ErrorLayer
        app = App()

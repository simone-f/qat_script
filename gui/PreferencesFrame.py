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


from javax.swing import JPanel, JButton, JLabel, JTable, JOptionPane,\
                        JTextField, JTabbedPane, BorderFactory, Box,\
                        BoxLayout, JFrame, JScrollPane, ImageIcon
from javax.swing.table import DefaultTableModel
from java.awt import BorderLayout, GridLayout, Dimension, Color,\
                    Component, FlowLayout, Container, Font
from java.awt.event import ActionListener, WindowListener, ItemListener
from javax.swing.event import DocumentListener, ListSelectionListener,\
                    HyperlinkListener, HyperlinkEvent
#from java.awt.event import KeyEvent
from java.lang import Integer, NumberFormatException, String
from java.io import File

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.tools import ImageProvider, OpenBrowser
from org.openstreetmap.josm.gui.widgets import HtmlPanel
from org.openstreetmap.gui.jmapviewer import JMapViewer, MapPolygonImpl,\
                    MapRectangleImpl, Coordinate

#local import
from NewZoneDialog import NewZoneDialog
from NewZoneDialog import Zone
import update_checker


#### PreferencesFrame ##################################################
class ZonesTableModel(DefaultTableModel):
    """A table model with non-editable cells
    """
    def getColumnClass(self, column):
        if column == 1:
            return ImageIcon
        else:
            return String

    def isCellEditable(self, rowIndex, columnIndex):
        return False


class ZonesTableListener(ListSelectionListener):
    def __init__(self, preferencesFrame):
        self.app = preferencesFrame.app
        self.preferencesFrame = preferencesFrame

    def valueChanged(self, event):
        if event.getValueIsAdjusting():
            return
        elif len(self.preferencesFrame.zonesTable.getSelectedRows()) != 0:
            self.preferencesFrame.check_removeBtn_status()
            #Code credit: gui.preferences.imagery.ImageryPreference.java
            #Show the shape of the selected favourite zone on a map
            zoneIdx = self.preferencesFrame.zonesTable.getSelectedRows()[0]
            zonesMap = self.preferencesFrame.zonesMap
            self.preferencesFrame.clean_map()

            zone = self.app.tempZones[zoneIdx]
            if zone.polygons == []:
                #Create zone polygons if needed
                if zone.zType == "rectangle":
                    topLeft = Coordinate(zone.bbox[3], zone.bbox[0])
                    bottomRight = Coordinate(zone.bbox[1], zone.bbox[2])
                    zone.polygons = [MapRectangleImpl(topLeft, bottomRight)]
                else:
                    if zone.wktGeom is None:
                        zone.wktGeom = zone.read_wktGeom()
                    zone.polygons = []
                    polygonType = zone.wktGeom.getGeometryType()
                    if polygonType == "Polygon":
                        polygon = self.create_map_polygon(zone.wktGeom.getExteriorRing())
                        zone.polygons.append(polygon)
                    elif polygonType == "MultiPolygon":
                        for i in range(zone.wktGeom.getNumGeometries()):
                            geom = zone.wktGeom.getGeometryN(i).getExteriorRing()
                            polygon = self.create_map_polygon(geom)
                            zone.polygons.append(polygon)
            for polygon in zone.polygons:
                if zone.zType == "rectangle":
                    zonesMap.addMapRectangle(polygon)
                else:
                    zonesMap.addMapPolygon(polygon)
            zonesMap.setDisplayToFitMapElements(False, True, True)
            zonesMap.zoomOut()

    def create_map_polygon(self, polygon):
        coords = [Coordinate(c.y, c.x) for c in polygon.getCoordinates()]
        mapPolygon = MapPolygonImpl(coords)
        return mapPolygon


class ErrNumTextListener(DocumentListener):
    def __init__(self, dlg):
        self.dlg = dlg
        self.textfield = self.dlg.maxErrorsNumberTextField
        self.defaultborder = self.dlg.maxErrorsNumberTFieldDefaultBorder

    def removeUpdate(self, e):
        self.warn(e)

    def insertUpdate(self, e):
        self.warn(e)

    def warn(self, e):
        errorNumber = self.textfield.getText()
        if errorNumber == "":
            self.textfield.setBorder(self.defaultborder)
            return
        try:
            Integer.parseInt(errorNumber)
        except NumberFormatException:
            self.textfield.setBorder(BorderFactory.createLineBorder(Color.RED, 1))
            return
        self.textfield.setBorder(BorderFactory.createLineBorder(Color.GREEN, 1))


class PreferencesFrame(JFrame, ActionListener, WindowListener, ItemListener, HyperlinkListener):
    """Dialog with preferences
    """
    def __init__(self, parent, title, app):
        from javax.swing import JCheckBox, JRadioButton, ButtonGroup
        self.app = app
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        self.getContentPane().setBorder(border)
        self.getContentPane().setLayout(BorderLayout(0, 5))
        self.tabbedPane = JTabbedPane()

        #1 Tab: general
        panel1 = JPanel()
        panel1.setBorder(BorderFactory.createEmptyBorder(7, 7, 7, 7))
        panel1.setLayout(BoxLayout(panel1, BoxLayout.PAGE_AXIS))

        #Checkbutton to enable/disable update check when script starts
        self.updateCBtn = JCheckBox(self.app.strings.getString("updateCBtn"))
        self.updateCBtn.setToolTipText(self.app.strings.getString("updateCBtn_tooltip"))

        #Download tools
        downloadBtn = JButton(self.app.strings.getString("updatesBtn"),
                              ImageProvider.get("dialogs", "refresh"),
                              actionPerformed=self.on_downloadBtn_clicked)
        downloadBtn.setToolTipText(self.app.strings.getString("updatesBtn_tooltip"))

        #Checkbuttons for enabling/disabling tools
        toolsPanel = JPanel(BorderLayout(0, 5))
        title = self.app.strings.getString("enable_disable_tools")
        toolsPanel.setBorder(BorderFactory.createTitledBorder(title))
        infoLbl = JLabel(self.app.strings.getString("JOSM_restart_warning"))
        infoLbl.setFont(infoLbl.getFont().deriveFont(Font.ITALIC))
        toolsPanel.add(infoLbl, BorderLayout.PAGE_START)

        toolsStatusPane = JPanel(GridLayout(len(self.app.realTools), 0))
        self.toolsCBtns = []
        for tool in self.app.realTools:
            toolCBtn = JCheckBox()
            toolCBtn.addItemListener(self)
            toolLbl = JLabel(tool.title, tool.bigIcon, JLabel.LEFT)
            self.toolsCBtns.append(toolCBtn)

            toolPane = JPanel()
            toolPane.setLayout(BoxLayout(toolPane, BoxLayout.X_AXIS))
            toolPane.add(toolCBtn)
            toolPane.add(toolLbl)
            toolsStatusPane.add(toolPane)
        toolsPanel.add(toolsStatusPane, BorderLayout.CENTER)

        #Radiobuttons for enabling/disabling layers when a new one
        #is added
        layersPanel = JPanel(GridLayout(0, 1))
        title = self.app.strings.getString("errors_layers_manager")
        layersPanel.setBorder(BorderFactory.createTitledBorder(title))
        errorLayersLbl = JLabel(self.app.strings.getString("errors_layers_info"))
        errorLayersLbl.setFont(errorLayersLbl.getFont().deriveFont(Font.ITALIC))
        layersPanel.add(errorLayersLbl)
        self.layersRBtns = {}
        group = ButtonGroup()
        for mode in self.app.layersModes:
            layerRBtn = JRadioButton(self.app.strings.getString("%s" % mode))
            group.add(layerRBtn)
            layersPanel.add(layerRBtn)
            self.layersRBtns[mode] = layerRBtn

        #Max number of errors text field
        self.maxErrorsNumberTextField = JTextField()
        self.maxErrorsNumberTextField.setToolTipText(self.app.strings.getString("maxErrorsNumberTextField_tooltip"))
        self.maxErrorsNumberTFieldDefaultBorder = self.maxErrorsNumberTextField.getBorder()
        self.maxErrorsNumberTextField.getDocument().addDocumentListener(ErrNumTextListener(self))

        #layout
        self.updateCBtn.setAlignmentX(Component.LEFT_ALIGNMENT)
        panel1.add(self.updateCBtn)
        panel1.add(Box.createRigidArea(Dimension(0, 15)))
        downloadBtn.setAlignmentX(Component.LEFT_ALIGNMENT)
        panel1.add(downloadBtn)
        panel1.add(Box.createRigidArea(Dimension(0, 15)))
        toolsPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        panel1.add(toolsPanel)
        panel1.add(Box.createRigidArea(Dimension(0, 15)))
        layersPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        panel1.add(layersPanel)
        panel1.add(Box.createRigidArea(Dimension(0, 15)))
        maxErrP = JPanel(BorderLayout(5, 0))
        maxErrP.add(JLabel(self.app.strings.getString("max_errors_number")), BorderLayout.LINE_START)
        maxErrP.add(self.maxErrorsNumberTextField, BorderLayout.CENTER)
        p = JPanel(BorderLayout())
        p.add(maxErrP, BorderLayout.PAGE_START)
        p.setAlignmentX(Component.LEFT_ALIGNMENT)
        panel1.add(p)

        self.tabbedPane.addTab(self.app.strings.getString("tab_1_title"),
                          None,
                          panel1,
                          None)

        #2 Tab: favourite zones
        panel2 = JPanel(BorderLayout(5, 15))
        panel2.setBorder(BorderFactory.createEmptyBorder(7, 7, 7, 7))

        #status
        topPanel = JPanel()
        topPanel.setLayout(BoxLayout(topPanel, BoxLayout.Y_AXIS))
        infoPanel = HtmlPanel(self.app.strings.getString("fav_zones_info"))
        infoPanel.getEditorPane().addHyperlinkListener(self)
        infoPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.favZoneStatusCBtn = JCheckBox(self.app.strings.getString("activate_fav_area"),
                                           actionListener=self)
        self.favZoneStatusCBtn.setToolTipText(self.app.strings.getString("activate_fav_area_tooltip"))
        self.favZoneStatusCBtn.setAlignmentX(Component.LEFT_ALIGNMENT)
        topPanel.add(infoPanel)
        topPanel.add(Box.createRigidArea(Dimension(0, 10)))
        topPanel.add(self.favZoneStatusCBtn)
        #table
        self.zonesTable = JTable()
        tableSelectionModel = self.zonesTable.getSelectionModel()
        tableSelectionModel.addListSelectionListener(ZonesTableListener(self))
        columns = ["",
                   self.app.strings.getString("Type"),
                   self.app.strings.getString("Name")]
        tableModel = ZonesTableModel([], columns)
        self.zonesTable.setModel(tableModel)
        self.scrollPane = JScrollPane(self.zonesTable)
        #map
        self.zonesMap = JMapViewer()
        self.zonesMap.setZoomContolsVisible(False)
        self.zonesMap.setMinimumSize(Dimension(100, 200))

        #buttons
        self.removeBtn = JButton(self.app.strings.getString("Remove"),
                            ImageProvider.get("dialogs", "delete"),
                            actionPerformed=self.on_removeBtn_clicked)
        self.removeBtn.setToolTipText(self.app.strings.getString("remove_tooltip"))
        newBtn = JButton(self.app.strings.getString("New"),
                         ImageProvider.get("dialogs", "add"),
                         actionPerformed=self.on_newBtn_clicked)
        newBtn.setToolTipText(self.app.strings.getString("new_tooltip"))

        #layout
        panel2.add(topPanel, BorderLayout.PAGE_START)
        panel2.add(self.scrollPane, BorderLayout.LINE_START)
        panel2.add(self.zonesMap, BorderLayout.CENTER)
        self.buttonsPanel = JPanel()
        self.buttonsPanel.add(self.removeBtn)
        self.buttonsPanel.add(newBtn)
        panel2.add(self.buttonsPanel, BorderLayout.PAGE_END)

        self.tabbedPane.addTab(self.app.strings.getString("tab_2_title"),
                          None,
                          panel2,
                          None)

        #3 Tab Tools options
        panel3 = JPanel()
        panel3.setLayout(BoxLayout(panel3, BoxLayout.Y_AXIS))
        panel3.setBorder(BorderFactory.createEmptyBorder(7, 7, 7, 7))
        for tool in self.app.realTools:
            if hasattr(tool, 'prefs'):
                p = JPanel(FlowLayout(FlowLayout.LEFT))
                p.setBorder(BorderFactory.createTitledBorder(tool.title))
                p.add(tool.prefsGui)
                panel3.add(p)

        self.tabbedPane.addTab(self.app.strings.getString("tab_3_title"),
                          None,
                          panel3,
                          None)

        self.add(self.tabbedPane, BorderLayout.CENTER)

        exitPanel = JPanel()
        saveBtn = JButton(self.app.strings.getString("OK"),
                          ImageProvider.get("ok"),
                          actionPerformed=self.on_saveBtn_clicked)
        cancelBtn = JButton(self.app.strings.getString("cancel"),
                            ImageProvider.get("cancel"),
                            actionPerformed=self.on_cancelBtn_clicked)
        saveBtn.setToolTipText(self.app.strings.getString("save_preferences"))
        saveBtn.setAlignmentX(0.5)
        exitPanel.add(saveBtn)
        exitPanel.add(cancelBtn)
        self.add(exitPanel, BorderLayout.PAGE_END)

        self.addWindowListener(self)
        self.pack()

    def windowClosing(self, windowEvent):
        self.on_cancelBtn_clicked()

    def hyperlinkUpdate(self, e):
        if e.getEventType() == HyperlinkEvent.EventType.ACTIVATED:
            OpenBrowser.displayUrl(e.getURL().toString())

    def itemStateChanged(self, e):
        """A ttol has been activated/deactivated.
           Check if at least one tool is on.
        """
        if all(not button.isSelected() for button in self.toolsCBtns):
            JOptionPane.showMessageDialog(
                Main.parent,
                self.app.strings.getString("tools_disabled_warning"),
                self.app.strings.getString("tools_disabled_warning_title"),
                JOptionPane.WARNING_MESSAGE)
            source = e.getItemSelectable()
            source.setSelected(True)

    def actionPerformed(self, e=None):
        """Enable/disable favourite zones panel
        """
        for container in (self.scrollPane, self.buttonsPanel):
            self.enableComponents(container, self.favZoneStatusCBtn.isSelected())
        if self.favZoneStatusCBtn.isSelected():
            self.check_removeBtn_status()

    def enableComponents(self, container, enable):
        components = container.getComponents()
        for component in components:
            component.setEnabled(enable)
            if isinstance(component, Container):
                self.enableComponents(component, enable)

    def on_downloadBtn_clicked(self, e):
        update_checker.Updater(self.app, "manual")

    def clean_map(self):
        """Remove all rectangles and polygons from the map
        """
        self.zonesMap.removeAllMapRectangles()
        self.zonesMap.removeAllMapPolygons()

    def update_gui_from_preferences(self):
        """Update gui status of preferences frame from config file
        """
        #print "\n- updating Preferences gui"
        onOff = {"on": True, "off": False}
        #1 Tab
        #check for update
        self.updateCBtn.setSelected(onOff[self.app.checkUpdate])

        #tools status, enabled or not
        for toolIndex, tool in enumerate(self.app.realTools):
            if "tool.%s" % tool.name in self.app.properties.keys():
                configstatus = self.app.properties.getProperty("tool.%s" % tool.name)
            else:
                configstatus = "on"     # new tool
            self.toolsCBtns[toolIndex].setSelected(onOff[configstatus])

        #layers preferences
        for mode, button in self.layersRBtns.iteritems():
            button.setSelected(mode == self.app.layersMode)

        #max errors number
        self.maxErrorsNumberTextField.setText(str(self.app.maxErrorsNumber))

        #stats panel
        self.app.dlg.update_favourite_zone_indicator()

        #2 Tab
        #favourite area
        self.update_favourite_area_gui_from_preferences()
        self.app.dlg.update_statsPanel_status()

        #3 Tab
        #tools preferences
        for tool in self.app.allTools:
            if hasattr(tool, 'prefs') and tool.prefsGui is not None:
                tool.prefsGui.update_gui(tool.prefs)

    def update_favourite_area_gui_from_preferences(self):
        #status
        self.favZoneStatusCBtn.setSelected(self.app.favouriteZoneStatus)
        #table
        #store zones to a temporary list, used to store changes
        #and save them when preferences dialog is closed
        self.app.tempZones = list(self.app.zones)
        self.zonesTable.getModel().setNumRows(0)
        for zone in self.app.tempZones:
            self.zonesTable.getModel().addRow([zone.country,
                                               zone.icon,
                                               zone.name])
        if self.app.favZone is not None:
            selectedRow = self.app.tempZones.index(self.app.favZone)
            self.zonesTable.setRowSelectionInterval(selectedRow, selectedRow)
        self.zonesTable.getColumnModel().getColumn(0).setMaxWidth(30)
        self.zonesTable.getColumnModel().getColumn(1).setMaxWidth(50)
        #enable or disable favourite zone buttons
        self.actionPerformed()

### fav area editing buttons ###########################################
    def on_removeBtn_clicked(self, e):
        rowsNum = self.zonesTable.getSelectedRows()
        rowsNum.reverse()
        for rowNum in rowsNum:
            del self.app.tempZones[rowNum]
            self.zonesTable.getModel().removeRow(rowNum)
        if len(self.app.tempZones) != 0:
            if rowNum == 0:
                self.zonesTable.setRowSelectionInterval(0, 0)
            else:
                self.zonesTable.setRowSelectionInterval(rowNum - 1, rowNum - 1)
        self.check_removeBtn_status()

    def check_removeBtn_status(self):
        if self.app.tempZones != [] and len(self.zonesTable.getSelectedRows()) != 0:
            self.removeBtn.setEnabled(True)
        else:
            self.removeBtn.setEnabled(False)
            self.clean_map()

    def on_newBtn_clicked(self, e):
        try:
            self.newZoneDialog
        except AttributeError:
            from java.awt import Dialog
            self.newZoneDialog = NewZoneDialog(Main.parent,
                                               self.app.strings.getString("Create_a_new_favourite_zone"),
                                               Dialog.ModalityType.APPLICATION_MODAL,
                                               self.app)
        bbox = self.app.get_frame_bounds()
        self.app.newZone = Zone(self.app,
                                self.app.strings.getString("New_zone"),
                                "rectangle",
                                ",".join(["%0.4f" % x for x in bbox]),
                                "")
        self.newZoneDialog.update_gui_from_preferences()
        self.newZoneDialog.show()
        self.setEnabled(False)

### Exit from preferences ##############################################
    def on_cancelBtn_clicked(self, event=None):
        if hasattr(self, "newZoneDialog") and self.newZoneDialog.isVisible():
            self.newZoneDialog.close_dialog()
        self.dispose()

    def on_saveBtn_clicked(self, event):
        """Read preferences from gui and save them to config.properties
           file
        """
        #print "\n- saving preferences to config file"
        onOff = {True: "on", False: "off"}

        #1 Tab
        #check for update
        self.app.properties.setProperty("check_for_update",
                                        onOff[self.updateCBtn.isSelected()])
        #tools status
        for toolIndex, tool in enumerate(self.app.realTools):
            prop = "tool.%s" % tool.name
            toolCBtn = self.toolsCBtns[toolIndex]
            self.app.properties.setProperty(prop,
                                            onOff[toolCBtn.isSelected()])

        #layers preferences
        for mode, button in self.layersRBtns.iteritems():
            if button.isSelected():
                self.app.properties.setProperty("layers_mode", mode)
                break

        #max errors number
        try:
            num = Integer.parseInt(self.maxErrorsNumberTextField.getText())
        except NumberFormatException:
            num = ""
        self.app.properties.setProperty("max_errors_number", str(num))

        #2 Tab
        #Favourite zones
        changes = {"new": [z for z in self.app.tempZones if not z in self.app.zones],
                   "deleted": [z for z in self.app.zones if not z in self.app.tempZones]}
        #delete files of removed favourite zones
        for zone in changes["deleted"]:
            f = File(File.separator.join([self.app.SCRIPTDIR,
                                          "configuration",
                                          "favourite_zones",
                                          "%s.txt" % zone.name]))
            f.delete()
        #create files for new favourite zones
        for zone in changes["new"]:
            print "\nsave new zone", zone.name
            fileName = File.separator.join([self.app.SCRIPTDIR,
                                            "configuration",
                                            "favourite_zones",
                                            "%s.txt" % zone.name])
            f = open(fileName, "w")
            zoneData = zone.geomString
            if zone.country != "":
                zoneData += "|" + zone.country
            f.write(zoneData)
            f.close()

        self.app.zones = self.app.tempZones
        if len(self.app.zones) == 0:
            self.app.favZone = None
            self.app.properties.setProperty("favourite_area.name",
                                            "")
            self.favZoneStatusCBtn.setSelected(False)
        else:
            if len(self.zonesTable.getSelectedRows()) == 0:
                self.app.favZone = self.app.zones[0]
            else:
                self.app.favZone = self.app.zones[self.zonesTable.getSelectedRows()[0]]
            self.app.properties.setProperty("favourite_area.name",
                                            self.app.favZone.name)
        favZoneStatus = self.favZoneStatusCBtn.isSelected()
        self.app.properties.setProperty("favourite_area.status", onOff[favZoneStatus])
        self.app.favouriteZoneStatus = favZoneStatus

        #stats panel
        self.app.dlg.update_favourite_zone_indicator()
        self.app.dlg.update_statsPanel_status()

        #3 Tab
        #tools preferences
        for tool in self.app.allTools:
            if hasattr(tool, 'prefs') and tool.prefsGui is not None:
                for pref, value in tool.prefsGui.read_gui().iteritems():
                    prefKey = "tool.%s.%s" % (tool.name, pref)
                    self.app.properties.setProperty(prefKey, value)

        self.app.save_config()
        self.dispose()

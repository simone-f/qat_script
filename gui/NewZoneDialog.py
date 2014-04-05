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
from javax.swing import JPanel, JButton, JLabel, JComboBox,\
                        JTextField, JOptionPane, DefaultComboBoxModel,\
                        BorderFactory, Box, BoxLayout,\
                        JRadioButton, ButtonGroup, JDialog,\
                        ImageIcon
from java.awt import BorderLayout, GridLayout, Dimension, Color, Font,\
                    Component
from java.awt.event import ActionListener, WindowListener
from javax.swing.event import DocumentListener
from java.io import File
#from java.awt.event import KeyEvent
from java.lang import Double, NumberFormatException
from java.net import URLEncoder

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.tools import OpenBrowser, ImageProvider
from org.openstreetmap.josm.gui.layer import OsmDataLayer
from org.openstreetmap.josm.data.osm import DataSet
from org.openstreetmap.josm.gui.widgets import JMultilineLabel
from com.vividsolutions.jts.operation.polygonize import Polygonizer
from org.openstreetmap.josm.plugins.jts import JTSConverter
from com.vividsolutions.jts.geom import GeometryFactory
from com.vividsolutions.jts.io import WKTWriter


#### NewZoneDialog ###############################################
class TextListener(DocumentListener):
    """Text listener for manually configured favourite bbox
    """
    def __init__(self, dlg):
        self.dlg = dlg
        self.textfield = self.dlg.bboxTextField
        self.defaultborder = self.dlg.bboxTextFieldDefaultBorder

    def removeUpdate(self, e):
        self.warn()

    def insertUpdate(self, e):
        self.warn()

    def warn(self):
        bboxString = self.textfield.getText()
        if bboxString == "":
            self.textfield.setBorder(self.defaultborder)
            return
        if len(bboxString.split(",")) != 4:
            self.wrongEntry()
        else:
            for i, coordString in enumerate(bboxString.split(",")):
                try:
                    coord = Double.parseDouble(coordString)
                except NumberFormatException:
                    self.wrongEntry()
                    return
                minmax = {0: (-180, 180), 1: (-90, 90),
                          2: (-180, 180), 3: (-90, 90)}
                if not minmax[i][0] <= coord <= minmax[i][1]:
                    self.wrongEntry()
                    return
            self.textfield.setBorder(self.defaultborder)
            self.dlg.bboxPreviewTextField.setText(bboxString)

    def wrongEntry(self):
        self.textfield.setBorder(BorderFactory.createLineBorder(Color.RED, 1))


class NewZoneDialog(JDialog, ActionListener, WindowListener):
    """Dialog for favourite zone editing
    """
    def __init__(self, parent, title, modal, app):
        from java.awt import CardLayout
        self.app = app
        border = BorderFactory.createEmptyBorder(5, 7, 7, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))

        self.FAVAREALAYERNAME = "Favourite zone editing"

        info = JLabel(self.app.strings.getString("Create_a_new_favourite_zone"))
        info.setAlignmentX(Component.LEFT_ALIGNMENT)

        #Name
        nameLbl = JLabel(self.app.strings.getString("fav_zone_name"))
        self.nameTextField = JTextField(20)
        self.nameTextField.setMaximumSize(self.nameTextField.getPreferredSize())
        self.nameTextField.setToolTipText(self.app.strings.getString("fav_zone_name_tooltip"))
        namePanel = JPanel()
        namePanel.setLayout(BoxLayout(namePanel, BoxLayout.X_AXIS))
        namePanel.add(nameLbl)
        namePanel.add(Box.createHorizontalGlue())
        namePanel.add(self.nameTextField)

        #Country
        countryLbl = JLabel(self.app.strings.getString("fav_zone_country"))
        self.countryTextField = JTextField(20)
        self.countryTextField.setMaximumSize(self.countryTextField.getPreferredSize())
        self.countryTextField.setToolTipText(self.app.strings.getString("fav_zone_country_tooltip"))
        countryPanel = JPanel()
        countryPanel.setLayout(BoxLayout(countryPanel, BoxLayout.X_AXIS))
        countryPanel.add(countryLbl)
        countryPanel.add(Box.createHorizontalGlue())
        countryPanel.add(self.countryTextField)

        #Type
        modeLbl = JLabel(self.app.strings.getString("fav_zone_type"))
        RECTPANEL = "rectangle"
        POLYGONPANEL = "polygon"
        BOUNDARYPANEL = "boundary"
        self.modesStrings = [RECTPANEL, POLYGONPANEL, BOUNDARYPANEL]
        modesComboModel = DefaultComboBoxModel()
        for i in (self.app.strings.getString("rectangle"),
                  self.app.strings.getString("delimited_by_a_closed_way"),
                  self.app.strings.getString("delimited_by_an_administrative_boundary")):
            modesComboModel.addElement(i)
        self.modesComboBox = JComboBox(modesComboModel,
                                       actionListener=self,
                                       editable=False)

        #- Rectangle
        self.rectPanel = JPanel()
        self.rectPanel.setLayout(BoxLayout(self.rectPanel, BoxLayout.Y_AXIS))

        capturePane = JPanel()
        capturePane.setLayout(BoxLayout(capturePane, BoxLayout.X_AXIS))
        capturePane.setAlignmentX(Component.LEFT_ALIGNMENT)

        josmP = JPanel()
        self.captureRBtn = JRadioButton(self.app.strings.getString("capture_area"))
        self.captureRBtn.addActionListener(self)
        self.captureRBtn.setSelected(True)
        self.bboxFromJosmBtn = JButton(self.app.strings.getString("get_current_area"),
                                       actionPerformed=self.on_bboxFromJosmBtn_clicked)
        self.bboxFromJosmBtn.setToolTipText(self.app.strings.getString("get_capture_area_tooltip"))
        josmP.add(self.bboxFromJosmBtn)
        capturePane.add(self.captureRBtn)
        capturePane.add(Box.createHorizontalGlue())
        capturePane.add(self.bboxFromJosmBtn)

        manualPane = JPanel()
        manualPane.setLayout(BoxLayout(manualPane, BoxLayout.X_AXIS))
        manualPane.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.manualRBtn = JRadioButton(self.app.strings.getString("use_this_bbox"))
        self.manualRBtn.addActionListener(self)
        self.bboxTextField = JTextField(20)
        self.bboxTextField.setMaximumSize(self.bboxTextField.getPreferredSize())
        self.bboxTextField.setToolTipText(self.app.strings.getString("fav_bbox_tooltip"))
        self.bboxTextFieldDefaultBorder = self.bboxTextField.getBorder()
        self.bboxTextField.getDocument().addDocumentListener(TextListener(self))
        manualPane.add(self.manualRBtn)
        manualPane.add(Box.createHorizontalGlue())
        manualPane.add(self.bboxTextField)

        group = ButtonGroup()
        group.add(self.captureRBtn)
        group.add(self.manualRBtn)

        previewPane = JPanel()
        previewPane.setLayout(BoxLayout(previewPane, BoxLayout.X_AXIS))
        previewPane.setAlignmentX(Component.LEFT_ALIGNMENT)
        bboxPreviewInfo = JTextField(self.app.strings.getString("coordinates"),
                                     editable=0,
                                     border=None)
        bboxPreviewInfo.setMaximumSize(bboxPreviewInfo.getPreferredSize())
        self.bboxPreviewTextField = JTextField(20,
                                               editable=0,
                                               border=None)
        self.bboxPreviewTextField.setMaximumSize(self.bboxPreviewTextField.getPreferredSize())
        previewPane.add(bboxPreviewInfo)
        previewPane.add(Box.createHorizontalGlue())
        previewPane.add(self.bboxPreviewTextField)

        self.rectPanel.add(capturePane)
        self.rectPanel.add(Box.createRigidArea(Dimension(0, 10)))
        self.rectPanel.add(manualPane)
        self.rectPanel.add(Box.createRigidArea(Dimension(0, 20)))
        self.rectPanel.add(previewPane)

        #- Polygon (closed way) drawn by hand
        self.polygonPanel = JPanel(BorderLayout())
        self.polygonPanel.setLayout(BoxLayout(self.polygonPanel, BoxLayout.Y_AXIS))

        polyInfo = JLabel("<html>%s</html>" % self.app.strings.getString("polygon_info"))
        polyInfo.setFont(polyInfo.getFont().deriveFont(Font.ITALIC))
        polyInfo.setAlignmentX(Component.LEFT_ALIGNMENT)

        editPolyPane = JPanel()
        editPolyPane.setAlignmentX(Component.LEFT_ALIGNMENT)
        editPolyBtn = JButton(self.app.strings.getString("create_fav_layer"),
                              actionPerformed=self.create_new_zone_editing_layer)
        editPolyBtn.setToolTipText(self.app.strings.getString("create_fav_layer_tooltip"))
        editPolyPane.add(editPolyBtn)

        self.polygonPanel.add(polyInfo)
        self.polygonPanel.add(Box.createRigidArea(Dimension(0, 15)))
        self.polygonPanel.add(editPolyPane)
        self.polygonPanel.add(Box.createRigidArea(Dimension(0, 15)))

        #- Administrative Boundary
        self.boundaryPanel = JPanel()
        self.boundaryPanel.setLayout(BoxLayout(self.boundaryPanel, BoxLayout.Y_AXIS))

        boundaryInfo = JLabel("<html>%s</html>" % app.strings.getString("boundary_info"))
        boundaryInfo.setFont(boundaryInfo.getFont().deriveFont(Font.ITALIC))
        boundaryInfo.setAlignmentX(Component.LEFT_ALIGNMENT)

        boundaryTagsPanel = JPanel(GridLayout(3, 3, 5, 5))
        boundaryTagsPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        boundaryTagsPanel.add(JLabel("name ="))
        self.nameTagTextField = JTextField(20)
        boundaryTagsPanel.add(self.nameTagTextField)
        boundaryTagsPanel.add(JLabel("admin_level ="))
        self.adminLevelTagTextField = JTextField(20)
        self.adminLevelTagTextField.setToolTipText(self.app.strings.getString("adminLevel_tooltip"))
        boundaryTagsPanel.add(self.adminLevelTagTextField)
        boundaryTagsPanel.add(JLabel(self.app.strings.getString("other_tag")))
        self.optionalTagTextField = JTextField(20)
        self.optionalTagTextField.setToolTipText("key=value")
        boundaryTagsPanel.add(self.optionalTagTextField)

        downloadBoundariesPane = JPanel()
        downloadBoundariesPane.setAlignmentX(Component.LEFT_ALIGNMENT)
        downloadBoundariesBtn = JButton(self.app.strings.getString("download_boundary"),
                                        actionPerformed=self.on_downloadBoundariesBtn_clicked)
        downloadBoundariesBtn.setToolTipText(self.app.strings.getString("download_boundary_tooltip"))
        downloadBoundariesPane.add(downloadBoundariesBtn)

        self.boundaryPanel.add(boundaryInfo)
        self.boundaryPanel.add(Box.createRigidArea(Dimension(0, 15)))
        self.boundaryPanel.add(boundaryTagsPanel)
        self.boundaryPanel.add(Box.createRigidArea(Dimension(0, 10)))
        self.boundaryPanel.add(downloadBoundariesPane)

        self.editingPanels = {"rectangle": self.rectPanel,
                              "polygon": self.polygonPanel,
                              "boundary": self.boundaryPanel}

        #Main buttons
        self.okBtn = JButton(self.app.strings.getString("OK"),
                             ImageProvider.get("ok"),
                             actionPerformed=self.on_okBtn_clicked)
        self.cancelBtn = JButton(self.app.strings.getString("cancel"),
                                 ImageProvider.get("cancel"),
                                 actionPerformed=self.close_dialog)
        self.previewBtn = JButton(self.app.strings.getString("Preview_zone"),
                                  actionPerformed=self.on_previewBtn_clicked)
        self.previewBtn.setToolTipText(self.app.strings.getString("preview_zone_tooltip"))
        okBtnSize = self.okBtn.getPreferredSize()
        viewBtnSize = self.previewBtn.getPreferredSize()
        viewBtnSize.height = okBtnSize.height
        self.previewBtn.setPreferredSize(viewBtnSize)

        #layout
        self.add(info)
        self.add(Box.createRigidArea(Dimension(0, 15)))

        namePanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(namePanel)
        self.add(Box.createRigidArea(Dimension(0, 15)))

        countryPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(countryPanel)
        self.add(Box.createRigidArea(Dimension(0, 15)))

        modeLbl.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(modeLbl)
        self.add(Box.createRigidArea(Dimension(0, 5)))

        self.add(self.modesComboBox)
        self.modesComboBox.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(Box.createRigidArea(Dimension(0, 15)))

        self.configPanel = JPanel(CardLayout())
        self.configPanel.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5))
        self.configPanel.add(self.rectPanel, RECTPANEL)
        self.configPanel.add(self.polygonPanel, POLYGONPANEL)
        self.configPanel.add(self.boundaryPanel, BOUNDARYPANEL)
        self.configPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(self.configPanel)
        buttonsPanel = JPanel()
        buttonsPanel.add(self.okBtn)
        buttonsPanel.add(self.cancelBtn)
        buttonsPanel.add(self.previewBtn)
        buttonsPanel.setAlignmentX(Component.LEFT_ALIGNMENT)
        self.add(buttonsPanel)

        self.addWindowListener(self)
        self.pack()

    def update_gui_from_preferences(self):
        self.nameTextField.setText(self.app.newZone.name)
        #Reset rectangle mode
        bboxStr = ",".join(["%0.4f" % x for x in self.app.newZone.bbox])
        self.bboxTextField.setText(bboxStr)
        self.bboxPreviewTextField.setText(bboxStr)
        self.bboxFromJosmBtn.setEnabled(True)
        self.bboxTextField.setEnabled(False)

        #Reset polygon mode
        self.polygonAsString = ""

        #Reset boundary mode
        self.boundaryAsString = ""

        self.modesComboBox.setSelectedIndex(0)

    def actionPerformed(self, e):
        #Show the panel for configuring the favourite area of the
        #selected type
        if e.getSource() == self.modesComboBox:
            cl = self.configPanel.getLayout()
            selectedMode = self.modesStrings[self.modesComboBox.selectedIndex]
            cl.show(self.configPanel, selectedMode)
        #Activate bbox input for rectangular favourite zone mode
        elif e.getSource() == self.captureRBtn:
            self.bboxFromJosmBtn.setEnabled(True)
            self.bboxTextField.setEnabled(False)
        else:
            self.bboxFromJosmBtn.setEnabled(False)
            self.bboxTextField.setEnabled(True)

    def on_bboxFromJosmBtn_clicked(self, widget):
        """Read bbox currently shown in JOSM
        """
        bbox = self.app.get_frame_bounds()
        self.bboxPreviewTextField.setText(",".join(["%0.4f" % x for x in bbox]))

### Manage layer for creating a new favourite zone from polygon or boundary
    def create_new_zone_editing_layer(self, e=None):
        """Open a new dataset where the user can draw a closed way to
           delimit the favourite area
        """
        layer = self.get_new_zone_editing_layer()
        if layer is not None:
            self.app.mv.setActiveLayer(layer)
        else:
            Main.main.addLayer(OsmDataLayer(DataSet(), self.FAVAREALAYERNAME, None))
        Main.main.parent.toFront()

    def get_new_zone_editing_layer(self):
        """Check if the layer for editing the favourite area yet exists
        """
        for layer in self.app.mv.getAllLayers():
            if layer.getName() == self.FAVAREALAYERNAME:
                return layer
        return None

    def remove_new_zone_editing_layer(self):
        layer = self.get_new_zone_editing_layer()
        if layer is not None:
            self.app.mv.removeLayer(layer)

    def on_zone_edited(self):
        """Read ways that delimit the favourite area and convert them to
           jts geometry
        """
        if self.modesComboBox.getSelectedIndex() == 0:
            mode = "rectangle"
        elif self.modesComboBox.getSelectedIndex() == 1:
            mode = "polygon"
        elif self.modesComboBox.getSelectedIndex() == 2:
            mode = "boundary"

        if mode in ("polygon", "boundary"):
            layer = self.get_new_zone_editing_layer()
            if layer is not None:
                self.app.mv.setActiveLayer(layer)
            else:
                if mode == "polygon":
                    msg = self.app.strings.getString("polygon_fav_layer_missing_msg")
                else:
                    msg = self.app.strings.getString("boundary_fav_layer_missing_msg")
                JOptionPane.showMessageDialog(self,
                                              msg,
                                              self.app.strings.getString("Warning"),
                                              JOptionPane.WARNING_MESSAGE)
                return

            dataset = self.app.mv.editLayer.data
            areaWKT = self.read_area_from_osm_ways(mode, dataset)
            if areaWKT is None:
                print "I could not read the new favourite area."
            else:
                if mode == "polygon":
                    self.polygonAsString = areaWKT
                else:
                    self.boundaryAsString = areaWKT
        return mode

    def read_area_from_osm_ways(self, mode, dataset):
        """Read way in favourite area editing layer and convert them to
           WKT
        """
        converter = JTSConverter(False)
        lines = [converter.convert(way) for way in dataset.ways]
        polygonizer = Polygonizer()
        polygonizer.add(lines)
        polygons = polygonizer.getPolygons()
        multipolygon = GeometryFactory().createMultiPolygon(list(polygons))
        multipolygonWKT = WKTWriter().write(multipolygon)
        if multipolygonWKT == "MULTIPOLYGON EMPTY":
            if mode == "polygon":
                msg = self.app.strings.getString("empty_ways_polygon_msg")
            else:
                msg = self.app.strings.getString("empty_ways_boundaries_msg")
            JOptionPane.showMessageDialog(self,
                msg,
                self.app.strings.getString("Warning"),
                JOptionPane.WARNING_MESSAGE)
            return
        return multipolygonWKT

    def on_downloadBoundariesBtn_clicked(self, e):
        """Download puter ways of administrative boundaries from
           Overpass API
        """
        adminLevel = self.adminLevelTagTextField.getText()
        name = self.nameTagTextField.getText()
        optional = self.optionalTagTextField.getText()
        if (adminLevel, name, optional) == ("", "", ""):
            JOptionPane.showMessageDialog(self,
                                          self.app.strings.getString("enter_a_tag_msg"),
                                          self.app.strings.getString("Warning"),
                                          JOptionPane.WARNING_MESSAGE)
            return
        optTag = ""
        if optional.find("=") != -1:
            if len(optional.split("=")) == 2:
                key, value = optional.split("=")
                optTag = '["%s"="%s"]' % (URLEncoder.encode(key, "UTF-8"),
                                          URLEncoder.encode(value.replace(" ", "%20"), "UTF-8"))
        self.create_new_zone_editing_layer()
        overpassurl = 'http://127.0.0.1:8111/import?url='
        overpassurl += 'http://overpass-api.de/api/interpreter?data='
        overpassquery = 'relation["admin_level"="%s"]' % adminLevel
        overpassquery += '["name"="%s"]' % URLEncoder.encode(name, "UTF-8")
        overpassquery += '%s;(way(r:"outer");node(w););out meta;' % optTag
        overpassurl += overpassquery.replace(" ", "%20")
        print overpassurl
        self.app.send_to_josm(overpassurl)

### Buttons ############################################################
    def create_new_zone(self, mode):
        """Read data entered on gui and create a new zone
        """
        name = self.nameTextField.getText()
        country = self.countryTextField.getText().upper()

        #error: name
        if name.replace(" ", "") == "":
            JOptionPane.showMessageDialog(self,
                                          self.app.strings.getString("missing_name_warning"),
                                          self.app.strings.getString("missing_name_warning_title"),
                                          JOptionPane.WARNING_MESSAGE)
            return False
        if name in [z.name for z in self.app.tempZones]:
            JOptionPane.showMessageDialog(self,
                                          self.app.strings.getString("duplicate_name_warning"),
                                          self.app.strings.getString("duplicate_name_warning_title"),
                                          JOptionPane.WARNING_MESSAGE)
            return False

        #zone type
        zType = mode
        #error: geometry type not defined
        if zType == "polygon" and self.polygonAsString == ""\
            or zType == "boundary" and self.boundaryAsString == "":
            JOptionPane.showMessageDialog(self,
                                          self.app.strings.getString("zone_not_correctly_build_warning"),
                                          self.app.strings.getString("zone_not_correctly_build_warning_title"),
                                          JOptionPane.WARNING_MESSAGE)
            return False

        #geometry string
        if zType == "rectangle":
            geomString = self.bboxPreviewTextField.getText()
        elif zType == "polygon":
            geomString = self.polygonAsString
        else:
            geomString = self.boundaryAsString

        self.app.newZone = Zone(self.app, name, zType, geomString, country)
        #self.app.newZone.print_info()
        return True

    def on_okBtn_clicked(self, event):
        """Add new zone to temp zones
        """
        mode = self.on_zone_edited()
        if self.create_new_zone(mode):
            self.app.tempZones.append(self.app.newZone)
            self.app.preferencesFrame.zonesTable.getModel().addRow([self.app.newZone.country,
                                                                    self.app.newZone.icon,
                                                                    self.app.newZone.name])
            maxIndex = len(self.app.tempZones) - 1
            self.app.preferencesFrame.zonesTable.setRowSelectionInterval(maxIndex,
                                                                         maxIndex)
            self.close_dialog()
            self.app.preferencesFrame.check_removeBtn_status()
            self.app.preferencesFrame.zonesTable.scrollRectToVisible(
                self.app.preferencesFrame.zonesTable.getCellRect(
                    self.app.preferencesFrame.zonesTable.getRowCount() - 1, 0, True))

    def on_previewBtn_clicked(self, e):
        """Show the favourite area on a map
        """
        mode = self.on_zone_edited()
        if not self.create_new_zone(mode):
            return
        zone = self.app.newZone

        if zone.zType == "rectangle":
            wktString = zone.bbox_to_wkt_string()
        else:
            wktString = zone.wktGeom
        script = '/*http://stackoverflow.com/questions/11954401/wkt-and-openlayers*/'
        script += '\nfunction init() {'
        script += '\n    var map = new OpenLayers.Map({'
        script += '\n        div: "map",'
        script += '\n        projection: new OpenLayers.Projection("EPSG:900913"),'
        script += '\n        displayProjection: new OpenLayers.Projection("EPSG:4326"),'
        script += '\n        layers: ['
        script += '\n            new OpenLayers.Layer.OSM()'
        script += '\n            ]'
        script += '\n    });'
        script += '\n    var wkt = new OpenLayers.Format.WKT();'
        script += '\n    var polygonFeature = wkt.read("%s");' % wktString
        script += '\n    var vectors = new OpenLayers.Layer.Vector("Favourite area");'
        script += '\n    map.addLayer(vectors);'
        script += '\n    polygonFeature.geometry.transform(map.displayProjection, map.getProjectionObject());'
        script += '\n    vectors.addFeatures([polygonFeature]);'
        script += '\n    map.zoomToExtent(vectors.getDataExtent());'
        script += '\n};'
        scriptFile = open(File.separator.join([self.app.SCRIPTDIR,
                                              "html",
                                              "script.js"]), "w")
        scriptFile.write(script)
        scriptFile.close()
        OpenBrowser.displayUrl(File.separator.join([self.app.SCRIPTDIR,
                                                   "html",
                                                   "favourite_area.html"]))

    def windowClosing(self, windowEvent):
        self.close_dialog()

    def close_dialog(self, e=None):
        #delete favourite zone editing layer if present
        self.remove_new_zone_editing_layer()
        self.dispose()
        self.app.preferencesFrame.setEnabled(True)
        self.app.preferencesFrame.toFront()


### Favourite zone #####################################################
class Zone:
    def __init__(self, app, name, zType, geomString, country):
        self.name = name
        self.zType = zType
        self.icon = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                                   "images",
                                                   "icons",
                                                   "%s.png" % self.zType]))
        self.country = country
        self.geomString = geomString
        self.wktGeom = None

        if zType == "rectangle":
            self.bbox = [float(x) for x in geomString.split(",")]
        else:
            self.bbox = self.calculateBbox()

        self.polygons = []      # shapes used in zones map

    def read_wktGeom(self):
        from com.vividsolutions.jts.io import WKTReader
        return WKTReader().read(self.geomString)

    def calculateBbox(self):
        self.wktGeom = self.read_wktGeom()
        envelope = self.wktGeom.getEnvelopeInternal()
        bbox = [envelope.getMinX(),
                envelope.getMinY(),
                envelope.getMaxX(),
                envelope.getMaxY()]
        return bbox

    def bbox_to_wkt_string(self):
        """Convert bbox of a rectangular favourite zone to a WKT string
        """
        string = "%s %s,%s %s,%s %s,%s %s" % (self.bbox[0], self.bbox[1],
                                              self.bbox[2], self.bbox[1],
                                              self.bbox[2], self.bbox[3],
                                              self.bbox[0], self.bbox[3])
        return "POLYGON((%s)" % string

    def print_info(self):
        print "\nFavourite zone info:"
        print "name: ", self.name
        print "type: ", self.zType
        print "geometry string: ", self.geomString
        print "bbox: ", self.bbox

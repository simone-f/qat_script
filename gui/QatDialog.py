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
from javax.swing import JPanel, ImageIcon, JButton, JLabel, JComboBox,\
                        JTable, JTextField, DefaultComboBoxModel,\
                        JScrollPane, JTabbedPane, BorderFactory,\
                        ListSelectionModel, JPopupMenu, JMenuItem
from java.awt import BorderLayout, GridLayout, Color
from java.awt.event import ActionListener, MouseAdapter, MouseEvent
from javax.swing.table import DefaultTableModel, DefaultTableCellRenderer
from javax.swing.event import ListSelectionListener
from java.awt.image import BufferedImage
from java.text import MessageFormat
from java.io import File
from jarray import array
#from java.awt.event import KeyEvent
from java.lang import String

#josm import
from org.openstreetmap.josm.gui.dialogs import ToggleDialog
from org.openstreetmap.josm.tools import ImageProvider, OpenBrowser


#### Main Dialog #######################################################
class IconRenderer(DefaultTableCellRenderer):
    """IconRenderer for checks table
    """
    def __init(self):
        pass

    def setValue(self, value):
        if value == "":
            img = BufferedImage(16, 16, BufferedImage.TYPE_INT_ARGB)
            g = img.getGraphics()
            g.setColor(Color.RED)
            g.fillOval(2, 2, 10, 10)
            self.setIcon(ImageIcon(img))
        else:
            self.setIcon(value)


class MyTableModel(DefaultTableModel):
    """A table model with non-editable cells
    """
    def isCellEditable(self, checkIndex, columnIndex):
        return False


class ToolsComboListener(ActionListener):
    def __init__(self, app):
        self.app = app

    def actionPerformed(self, event):
        if not self.app.selectionChangedFromMenuOrLayer:
            self.app.on_selection_changed("toolsCombo")


class ViewsComboListener(ActionListener):
    def __init__(self, app):
        self.app = app

    def actionPerformed(self, event):
        if not self.app.selectionChangedFromMenuOrLayer:
            self.app.on_selection_changed("viewsCombo")


class ChecksTableListener(ListSelectionListener):
    def __init__(self, app):
        self.app = app

    def valueChanged(self, event):
        if event.getValueIsAdjusting():
            return
        else:
            self.app.on_selection_changed("checksTable")


class ChecksTableClickListener(MouseAdapter):
    def __init__(self, app, checkPopup, checksTable):
        self.app = app
        self.popup = checkPopup
        self.table = checksTable

    def mouseClicked(self, event):
        """Double-click on a checksTable row
        """
        #table = mousevent.getSource()
        #row = table.getSelectedRow()
        if event.getClickCount() == 2:
            self.app.on_downloadBtn_clicked(None)

    def mousePressed(self, event):
        table = event.getSource()
        point = event.getPoint()
        if point is not None and table.rowAtPoint(point) >= 0 and \
            event.getButton() == MouseEvent.BUTTON3:
            #selects the row at which point the mouse is clicked
            currentRow = table.rowAtPoint(point)
            table.setRowSelectionInterval(currentRow, currentRow)

            if self.app.selectedChecks[0].helpUrl == "":
                self.app.dlg.menuItemHelp.setEnabled(False)
            else:
                self.app.dlg.menuItemHelp.setEnabled(True)

            if self.app.selectedTool == self.app.favouritesTool:
                self.app.dlg.menuItemAdd.setEnabled(False)
                self.app.dlg.menuItemRemove.setEnabled(True)
            elif self.app.selectedTool.isLocal:
                self.app.dlg.menuItemAdd.setEnabled(False)
                self.app.dlg.menuItemRemove.setEnabled(False)
            else:
                if self.app.selectedChecks[0] in self.app.favouritesTool.views[0].checks:
                    self.app.dlg.menuItemAdd.setEnabled(False)
                    self.app.dlg.menuItemRemove.setEnabled(True)
                else:
                    self.app.dlg.menuItemAdd.setEnabled(True)
                    self.app.dlg.menuItemRemove.setEnabled(False)

            self.popup.show(self.table, event.getX(), event.getY())


class PopupActionListener(ActionListener):
    def __init__(self, app):
        self.app = app

    def actionPerformed(self, event):
        """Click ont the checksTable popup
        """
        check = self.app.selectedChecks[0]
        source = event.getSource()
        if source in (self.app.dlg.menuItemAdd,
                      self.app.dlg.menuItemRemove):
            tool = self.app.favouritesTool
            view = tool.views[0]
            if source == self.app.dlg.menuItemAdd:
                #Add a check to Favourites tool
                if check not in tool.views[0].checks:
                    view.checks.append(check)
                    #add to checks table
                    if check.errors is not None:
                        errorsNumber = len(check.errors)
                    else:
                        errorsNumber = ""
                    view.tableModel.addRow([check.icon,
                                            check.title,
                                            errorsNumber])
                    #add to menu
                    self.app.menu.add_check_item(tool,
                                                 view,
                                                 check,
                                                 self.app.favouritesMenu)
                    if self.app.selectedTool != tool:
                        selection = (tool, view, check)
                        self.app.on_selection_changed("add favourite", selection)
            elif source == self.app.dlg.menuItemRemove:
                #Remove a check from Favourites tool
                if check in view.checks:
                    checkIndex = view.checks.index(check)
                    #remove from checks table
                    view.tableModel.removeRow(checkIndex)
                    #remove from menu
                    self.app.favouritesMenu.remove(checkIndex)
                    view.checks.remove(check)
            #Save favourites checks to preferences
            prop = "tool.%s.checks" % tool.name
            favChecks = ""
            for i, check in enumerate(view.checks):
                if i != 0:
                    favChecks += "|"
                favChecks += "%s.%s.%s" % (check.tool.name, check.view.name, check.name)
            self.app.properties.setProperty(prop, favChecks)
            self.app.save_config()
        elif source == self.app.dlg.menuItemHelp:
            OpenBrowser.displayUrl(check.helpUrl)


class FavAreaIndicatorListener(MouseAdapter):
    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        """Click on favourite area status indicator
        """
        self.app.open_preferences("from favourite area indicator")


class QatDialog(ToggleDialog):
    """ToggleDialog for error type selection and buttons for reviewing
       errors in sequence
    """
    def __init__(self, name, iconName, tooltip, shortcut, height, app):
        ToggleDialog.__init__(self, name, iconName, tooltip, shortcut, height)
        self.app = app
        tools = app.tools

        #Main panel of the dialog
        mainPnl = JPanel(BorderLayout())
        mainPnl.setBorder(BorderFactory.createEmptyBorder(0, 1, 1, 1))

### First tab: errors selection and download ###########################
        #ComboBox with tools names
        self.toolsComboModel = DefaultComboBoxModel()
        for tool in tools:
            self.add_data_to_models(tool)
        self.toolsCombo = JComboBox(self.toolsComboModel,
                                    actionListener=ToolsComboListener(app))
        self.toolsCombo.setToolTipText(app.strings.getString("Select_a_quality_assurance_tool"))
        #ComboBox with categories names ("views"), of the selected tool
        self.viewsCombo = JComboBox(actionListener=ViewsComboListener(app))
        self.viewsCombo.setToolTipText(app.strings.getString("Select_a_category_of_error"))

        #Popup for checks table
        self.checkPopup = JPopupMenu()
        #add favourite check
        self.menuItemAdd = JMenuItem(self.app.strings.getString("Add_to_favourites"))
        self.menuItemAdd.setIcon(ImageIcon(File.separator.join([self.app.SCRIPTDIR,
                                                                "tools",
                                                                "data",
                                                                "Favourites",
                                                                "icons",
                                                                "tool_16.png"])))
        self.menuItemAdd.addActionListener(PopupActionListener(self.app))
        self.checkPopup.add(self.menuItemAdd)
        #remove favourite check
        self.menuItemRemove = JMenuItem(self.app.strings.getString("Remove_from_favourites"))
        self.menuItemRemove.setIcon(ImageIcon(File.separator.join([self.app.SCRIPTDIR,
                                                                   "tools",
                                                                   "data",
                                                                   "Favourites",
                                                                   "icons",
                                                                   "black_tool_16.png"])))
        self.menuItemRemove.addActionListener(PopupActionListener(self.app))
        self.checkPopup.add(self.menuItemRemove)
        #Help link for selected check
        self.menuItemHelp = JMenuItem(self.app.strings.getString("check_help"))
        self.menuItemHelp.setIcon(ImageIcon(File.separator.join([self.app.SCRIPTDIR,
                                                                 "images",
                                                                 "icons",
                                                                 "info_16.png"])))
        self.checkPopup.add(self.menuItemHelp)
        self.menuItemHelp.addActionListener(PopupActionListener(self.app))

        #Table with checks of selected tool and view
        self.checksTable = JTable()
        self.iconrenderer = IconRenderer()
        self.iconrenderer.setHorizontalAlignment(JLabel.CENTER)
        scrollPane = JScrollPane(self.checksTable)
        self.checksTable.setFillsViewportHeight(True)

        tableSelectionModel = self.checksTable.getSelectionModel()
        tableSelectionModel.addListSelectionListener(ChecksTableListener(app))

        self.checksTable.addMouseListener(ChecksTableClickListener(app,
            self.checkPopup,
            self.checksTable))

        #Favourite area status indicator
        self.favAreaIndicator = JLabel()
        self.update_favourite_zone_indicator()
        self.favAreaIndicator.addMouseListener(FavAreaIndicatorListener(app))

        #label with OSM id of the object currently edited and number of
        #errors still to review
        self.checksTextFld = JTextField("",
                                        editable=0,
                                        border=None,
                                        background=None)

        #checks buttons
        btnsIconsDir = File.separator.join([app.SCRIPTDIR, "images", "icons"])
        downloadIcon = ImageIcon(File.separator.join([btnsIconsDir, "download.png"]))
        self.downloadBtn = JButton(downloadIcon,
                                   actionPerformed=app.on_downloadBtn_clicked,
                                   enabled=0)
        startIcon = ImageIcon(File.separator.join([btnsIconsDir, "start_fixing.png"]))
        self.startBtn = JButton(startIcon,
                                actionPerformed=app.on_startBtn_clicked,
                                enabled=0)
        self.downloadBtn.setToolTipText(app.strings.getString("Download_errors_in_this_area"))
        self.startBtn.setToolTipText(app.strings.getString("Start_fixing_the_selected_errors"))

        #tab layout
        panel1 = JPanel(BorderLayout(0, 1))

        comboboxesPnl = JPanel(GridLayout(0, 2, 5, 0))
        comboboxesPnl.add(self.toolsCombo)
        comboboxesPnl.add(self.viewsCombo)

        checksPnl = JPanel(BorderLayout(0, 1))
        checksPnl.add(scrollPane, BorderLayout.CENTER)
        self.statsPanel = JPanel(BorderLayout(4, 0))
        self.statsPanel_def_color = self.statsPanel.getBackground()
        self.statsPanel.add(self.checksTextFld, BorderLayout.CENTER)
        self.statsPanel.add(self.favAreaIndicator, BorderLayout.LINE_START)
        checksPnl.add(self.statsPanel, BorderLayout.PAGE_END)

        checksButtonsPnl = JPanel(GridLayout(0, 2, 0, 0))
        checksButtonsPnl.add(self.downloadBtn)
        checksButtonsPnl.add(self.startBtn)

        panel1.add(comboboxesPnl, BorderLayout.PAGE_START)
        panel1.add(checksPnl, BorderLayout.CENTER)
        panel1.add(checksButtonsPnl, BorderLayout.PAGE_END)

### Second tab: errors fixing ##########################################
        #label with error stats
        self.errorTextFld = JTextField("",
                                       editable=0,
                                       border=None,
                                       background=None)
        #label with current error description
        self.errorDesc = JLabel("")
        self.errorDesc.setAlignmentX(0.5)

        #error buttons
        errorInfoBtnIcon = ImageProvider.get("info")
        self.errorInfoBtn = JButton(errorInfoBtnIcon,
                                    actionPerformed=app.on_errorInfoBtn_clicked,
                                    enabled=0)
        notErrorIcon = ImageIcon(File.separator.join([btnsIconsDir, "not_error.png"]))
        self.notErrorBtn = JButton(notErrorIcon,
                                   actionPerformed=app.on_falsePositiveBtn_clicked,
                                   enabled=0)
        ignoreIcon = ImageIcon(File.separator.join([btnsIconsDir, "skip.png"]))
        self.ignoreBtn = JButton(ignoreIcon,
                                 actionPerformed=app.on_ignoreBtn_clicked,
                                 enabled=0)
        correctedIcon = ImageIcon(File.separator.join([btnsIconsDir, "corrected.png"]))
        self.correctedBtn = JButton(correctedIcon,
                                    actionPerformed=app.on_correctedBtn_clicked,
                                    enabled=0)
        nextIcon = ImageIcon(File.separator.join([btnsIconsDir, "next.png"]))
        self.nextBtn = JButton(nextIcon,
                               actionPerformed=app.on_nextBtn_clicked,
                               enabled=0)
        #self.nextBtn.setMnemonic(KeyEvent.VK_RIGHT)
        self.errorInfoBtn.setToolTipText(app.strings.getString("open_error_info_dialog"))
        self.notErrorBtn.setToolTipText(app.strings.getString("flag_false_positive"))
        self.ignoreBtn.setToolTipText(app.strings.getString("Skip_and_don't_show_me_this_error_again"))
        self.correctedBtn.setToolTipText(app.strings.getString("flag_corrected_error"))
        self.nextBtn.setToolTipText(app.strings.getString("Go_to_next_error"))

        #tab layout
        self.panel2 = JPanel(BorderLayout())

        self.panel2.add(self.errorTextFld, BorderLayout.PAGE_START)
        self.panel2.add(self.errorDesc, BorderLayout.CENTER)

        errorButtonsPanel = JPanel(GridLayout(0, 5, 0, 0))
        errorButtonsPanel.add(self.errorInfoBtn)
        errorButtonsPanel.add(self.notErrorBtn)
        errorButtonsPanel.add(self.ignoreBtn)
        errorButtonsPanel.add(self.correctedBtn)
        errorButtonsPanel.add(self.nextBtn)
        self.panel2.add(errorButtonsPanel, BorderLayout.PAGE_END)

        #Layout
        self.tabbedPane = JTabbedPane()
        self.tabbedPane.addTab(self.app.strings.getString("Download"),
                               None,
                               panel1,
                               self.app.strings.getString("download_tab"))
        mainPnl.add(self.tabbedPane, BorderLayout.CENTER)
        self.createLayout(mainPnl, False, None)

    def add_data_to_models(self, tool):
        """Add data of a tool to the models of the dialog components
        """
        #tools combobox model
        self.toolsComboModel.addElement(tool.title)

        #views combobox
        tool.viewsComboModel = DefaultComboBoxModel()
        for view in tool.views:
            tool.viewsComboModel.addElement(view.title)

        #checks table, one TableModel for each view, of each tool
        columns = ["",
                   self.app.strings.getString("Check"),
                   self.app.strings.getString("Errors")]
        for view in tool.views:
            tableRows = []
            for check in view.checks:
                if check.icon is not None:
                    icon = check.icon
                else:
                    icon = ""
                errorsNumber = ""
                tableRows.append([icon, check.title, errorsNumber])
            view.tableModel = MyTableModel(tableRows, columns)

    def update_favourite_zone_indicator(self):
        #icon
        if self.app.favZone is not None:
            self.favAreaIndicator.setIcon(self.app.favZone.icon)
            #tooltip
            messageArguments = array([self.app.favZone.name], String)
            formatter = MessageFormat("")
            formatter.applyPattern(self.app.strings.getString("favAreaIndicator_tooltip"))
            msg = formatter.format(messageArguments)
            self.favAreaIndicator.setToolTipText(msg)
            #status
            self.favAreaIndicator.setVisible(self.app.favouriteZoneStatus)

    def set_checksTextFld_color(self, color):
        """Change color of textField under checksTable
        """
        colors = {"white": (255, 255, 255),
                  "black": (0, 0, 0),
                  "green": (100, 200, 0),
                  "red": (200, 0, 0)}
        if color == "default":
            self.statsPanel.background = self.statsPanel_def_color
            self.checksTextFld.foreground = colors["black"]
        else:
            self.statsPanel.background = colors[color]
            self.checksTextFld.foreground = colors["white"]

    def change_selection(self, source):
        """Change comboboxes and checks table selections after a
           selection has been made by the user
        """
        if source in ("menu", "layer", "add favourite"):
            self.app.selectionChangedFromMenuOrLayer = True
            self.toolsCombo.setSelectedItem(self.app.selectedTool.title)
            self.viewsCombo.setModel(self.app.selectedTool.viewsComboModel)
            self.viewsCombo.setSelectedItem(self.app.selectedView.name)

            self.checksTable.setModel(self.app.selectedTableModel)
            self.refresh_checksTable_columns_geometries()
            for i, c in enumerate(self.app.selectedView.checks):
                if c == self.app.selectedChecks[0]:
                    break
            self.checksTable.setRowSelectionInterval(i, i)
            self.app.selectionChangedFromMenuOrLayer = False
        else:
            self.app.selectionChangedFromMenuOrLayer = False
            if source == "toolsCombo":
                self.viewsCombo.setModel(self.app.selectedTool.viewsComboModel)
                self.viewsCombo.setSelectedIndex(0)
            elif source == "viewsCombo":
                self.checksTable.setModel(self.app.selectedTableModel)
                self.refresh_checksTable_columns_geometries()
                if self.app.selectedView.checks != []:  # favourite checks may be none
                    self.checksTable.setRowSelectionInterval(0, 0)

    def refresh_checksTable_columns_geometries(self):
        self.checksTable.getColumnModel().getColumn(0).setCellRenderer(self.iconrenderer)
        self.checksTable.getColumnModel().getColumn(0).setMaxWidth(25)
        self.checksTable.getColumnModel().getColumn(2).setMaxWidth(60)

    def activate_error_tab(self, status):
        if status:
            if self.tabbedPane.getTabCount() == 1:
                self.tabbedPane.addTab(self.app.strings.getString("Fix"),
                                       None,
                                       self.panel2,
                                       self.app.strings.getString("fix_tab"))
        else:
            if self.tabbedPane.getTabCount() == 2:
                self.tabbedPane.remove(1)

    def update_checks_buttons(self):
        """This method sets the status of downloadBtn and startBtn
        """
        #none check selected
        if len(self.app.selectedChecks) == 0:
            self.downloadBtn.setEnabled(False)
            self.startBtn.setEnabled(False)
        else:
            #some check selected
            self.downloadBtn.setEnabled(True)
            if len(self.app.selectedChecks) > 1:
                self.startBtn.setEnabled(False)
            else:
                #only one check is selected
                self.app.errors = self.app.selectedChecks[0].errors
                if self.app.errors is None or len(self.app.errors) == 0:
                    #errors file has not been downloaded and parsed yet
                    self.startBtn.setEnabled(False)
                else:
                    #errors file has been downloaded and parsed
                    if self.app.selectedChecks[0].toDo == 0:
                        #all errors have been corrected
                        self.startBtn.setEnabled(False)
                    else:
                        self.startBtn.setEnabled(True)
                        #self.nextBtn.setEnabled(True)

    def update_error_buttons(self, mode):
        """This method sets the status of:
           ignoreBtn, falsePositiveBtn, correctedBtn, nextBtn
        """
        if mode == "new error":
            status = True
        else:
            status = False
        if self.app.selectedChecks[0].tool.fixedFeedbackMode is None:
            self.correctedBtn.setEnabled(False)
        else:
            self.correctedBtn.setEnabled(status)
        if self.app.selectedChecks[0].tool.falseFeedbackMode is None:
            self.notErrorBtn.setEnabled(False)
        else:
            self.notErrorBtn.setEnabled(status)
        self.errorInfoBtn.setEnabled(status)
        self.ignoreBtn.setEnabled(status)

        if mode in ("reset", "review end"):
            self.nextBtn.setEnabled(False)
        elif mode in ("errors downloaded", "show stats", "new error"):
            self.nextBtn.setEnabled(True)

    def update_text_fields(self, mode, errorInfo=""):
        """This method updates the text in:
           checksTextFld, errorDesc, errorTextFld
        """
        self.errorDesc.text = ""
        if mode == "review end":
            cheksTextColor = "green"
            checksText = self.app.strings.getString("All_errors_reviewed.")
            errorText = self.app.strings.getString("All_errors_reviewed.")
        elif mode == "reset":
            cheksTextColor = "default"
            checksText = ""
            errorText = ""
        elif mode == "show stats":
            cheksTextColor = "default"
            checksText = "%s %d / %s" % (
                         self.app.strings.getString("to_do"),
                         self.app.selectedChecks[0].toDo,
                         len(self.app.selectedChecks[0].errors))
            #print "checks text", checksText
            errorText = "%s%s %d / %s" % (
                        errorInfo,
                        self.app.strings.getString("to_do"),
                        self.app.selectedChecks[0].toDo,
                        len(self.app.selectedChecks[0].errors))
            #print "error text", errorText
            if self.app.selectedError is not None and self.app.selectedError.desc != "":
                self.errorDesc.text = "<html>%s</html>" % self.app.selectedError.desc

        self.set_checksTextFld_color(cheksTextColor)
        self.checksTextFld.text = checksText
        self.errorTextFld.text = errorText
        self.update_statsPanel_status()

    def update_statsPanel_status(self):
        if self.checksTextFld.text == "" and not self.app.favouriteZoneStatus:
            self.statsPanel.setVisible(False)
        else:
            self.statsPanel.setVisible(True)

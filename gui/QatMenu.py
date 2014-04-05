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
from javax.swing import JMenu, JMenuItem, JCheckBoxMenuItem, ImageIcon,\
                        JFileChooser
from javax.swing.filechooser import FileNameExtensionFilter
from java.awt.event import ActionListener
from java.io import File

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.tools import OpenBrowser, ImageProvider
from org.openstreetmap.josm.actions import DiskAccessAction

#local import
from gui.AboutDialog import AboutDialog
from tools.data.LocalFile.LocalFile import LocalFileTool


#### QatMenu ###########################################################
class QatMenuActionListener(ActionListener):
    def __init__(self, app, itemType, tool=None, view=None, check=None):
        self.app = app
        self.itemType = itemType
        self.tool = tool
        self.view = view
        self.check = check
        self.strings = self.app.strings

    def actionPerformed(self, event):
        command = event.getActionCommand()
        if self.itemType == "dialog":

            #False positives dialog
            if command == self.strings.getString("False_positives..."):
                self.app.falsePositiveDlg.show()

            #Preferences dialog
            elif command == self.strings.getString("Preferences..."):
                self.app.open_preferences("from menu")

            #About dialog
            elif command == self.strings.getString("About..."):
                try:
                    self.app.aboutDlg
                except AttributeError:
                    #build about dialog
                    self.app.aboutDlg = AboutDialog(
                        Main.parent,
                        self.strings.getString("about_title"),
                        True,
                        self.app)
                self.app.aboutDlg.show()

        #Web link of the tool
        elif self.itemType == "link":
            OpenBrowser.displayUrl(self.tool.uri)

        elif self.itemType in ("check", "local file"):
            #Open local GPX file with errors
            if self.itemType == "local file":
                fileNameExtensionFilter = FileNameExtensionFilter("files GPX (*.gpx)",
                                                                  ["gpx"])
                chooser = DiskAccessAction.createAndOpenFileChooser(True,
                    False,
                    self.strings.getString("Open_a_GPX_file"),
                    fileNameExtensionFilter,
                    JFileChooser.FILES_ONLY,
                    None)
                if chooser is None:
                    return
                filePath = chooser.getSelectedFile()

                #remove former loaded local file
                for i, tool in enumerate(self.app.tools):
                    if filePath.getName() == tool.name:
                        self.app.dlg.toolsCombo.removeItemAt(i)
                        del self.app.tools[i]
                #create a new local file tool
                self.tool = LocalFileTool(self.app, filePath)
                self.view = self.tool.views[0]
                self.check = self.view.checks[0]
                self.app.tools.append(self.tool)
                #add tool to toggle dialog
                self.app.dlg.add_data_to_models(self.tool)

            selection = (self.tool, self.view, self.check)
            self.app.on_selection_changed("menu", selection)


class QatMenu(JMenu):
    """A menu from which the user can select an error type, toggle the
       qat dialog or about dialog.
    """
    def __init__(self, app, menuTitle):
        JMenu.__init__(self, menuTitle)
        self.app = app
        #quat dialog item
        dialogItem = JCheckBoxMenuItem(self.app.dlg.toggleAction)
        self.add(dialogItem)
        self.addSeparator()

        #tool submenu
        for tool in self.app.tools:
            if tool.name == "favourites":
                self.addSeparator()
            toolMenu = JMenu(tool.title)
            toolMenu.setIcon(tool.bigIcon)
            if tool.uri != "":
                #Website link
                iconFile = File.separator.join([self.app.SCRIPTDIR,
                                                "images",
                                                "icons",
                                                "browser.png"])
                urlItem = JMenuItem(tool.title)
                urlItem.setIcon(ImageIcon(iconFile))
                urlItem.addActionListener(QatMenuActionListener(self.app,
                                                                "link",
                                                                tool))
                toolMenu.add(urlItem)
                toolMenu.addSeparator()
            #View submenu
            for view in tool.views:
                viewMenu = JMenu(view.title)
                if tool.name == "favourites":
                    self.app.favouritesMenu = viewMenu
                #Check item
                for check in view.checks:
                    self.add_check_item(tool, view, check, viewMenu)
                toolMenu.add(viewMenu)
            self.add(toolMenu)
        #Local file with errors
        localFileItem = JMenuItem(self.app.strings.getString("Open_GPX"))
        localFileItem.setIcon(ImageProvider.get("open"))
        localFileItem.addActionListener(QatMenuActionListener(self.app, "local file"))
        self.add(localFileItem)
        self.addSeparator()
        #False positive dialog
        falsepositiveItem = JMenuItem(self.app.strings.getString("False_positives..."))
        falsepositiveItem.addActionListener(QatMenuActionListener(self.app, "dialog"))
        self.add(falsepositiveItem)
        #Preferences dialog
        preferencesItem = JMenuItem(self.app.strings.getString("Preferences..."))
        preferencesItem.addActionListener(QatMenuActionListener(self.app, "dialog"))
        self.add(preferencesItem)
        #About dialog item
        aboutItem = JMenuItem(self.app.strings.getString("About..."))
        aboutItem.addActionListener(QatMenuActionListener(self.app, "dialog"))
        self.add(aboutItem)

    def add_check_item(self, tool, view, check, viewMenu):
        checkItem = JMenuItem(check.title)
        if check.icon is not None:
            checkItem.setIcon(check.icon)
        checkItem.addActionListener(QatMenuActionListener(self.app,
                                                          "check",
                                                          tool,
                                                          view,
                                                          check))
        viewMenu.add(checkItem)

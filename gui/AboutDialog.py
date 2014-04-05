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
from javax.swing import JDialog, ImageIcon, JButton, JLabel, JPanel,\
                        JScrollPane, BorderFactory, Box, BoxLayout,\
                        WindowConstants
from java.awt import Dimension, FlowLayout, GridLayout, Component
from java.io import File

#josm import
from org.openstreetmap.josm.tools import ImageProvider
from org.openstreetmap.josm.gui.widgets import UrlLabel


#### AboutDialog #######################################################
class AboutDialog(JDialog):
    """Dialog with script info
    """
    def __init__(self, parent, title, modal, app):
        from javax.swing import JTextArea

        border = BorderFactory.createEmptyBorder(5, 7, 7, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))

        #Icon
        icon = ImageIcon(File.separator.join([app.SCRIPTDIR,
                                              "images",
                                              "icons",
                                              "logo.png"]))
        iconLbl = JLabel(icon)
        iconLbl.setAlignmentX(JLabel.CENTER_ALIGNMENT)

        #Name
        titleLbl = JLabel("Quality Assurance Tools script")
        titleLbl.setAlignmentX(JLabel.CENTER_ALIGNMENT)

        #Version
        p = JPanel()
        versionPanel = JPanel(GridLayout(2, 2))
        versionPanel.add(JLabel("script: "))
        versionPanel.add(JLabel(app.SCRIPTVERSION))
        versionPanel.add(JLabel("tools: "))
        self.toolsVersionLbl = JLabel(app.TOOLSVERSION)
        versionPanel.add(self.toolsVersionLbl)
        versionPanel.setAlignmentX(Component.CENTER_ALIGNMENT)
        p.add(versionPanel)

        #Wiki
        wikiLblPanel = JPanel(FlowLayout(FlowLayout.CENTER))
        wikiLbl = UrlLabel(app.SCRIPTWEBSITE, "Wiki", 2)
        wikiLblPanel.add(wikiLbl)
        wikiLblPanel.setAlignmentX(JLabel.CENTER_ALIGNMENT)

        #Author, contributors and credits
        creditsTextArea = JTextArea(15, 35, editable=False)
        creditsTextArea.setBackground(None)
        contribFile = open(File.separator.join([app.SCRIPTDIR, "CONTRIBUTORS"]), "r")
        contribText = contribFile.read()
        contribFile.close()
        creditsTextArea.append(contribText)
        creditsTextArea.setCaretPosition(0)
        creditScrollPane = JScrollPane(creditsTextArea)

        #OK button
        okBtn = JButton("OK",
                        ImageProvider.get("ok"),
                        actionPerformed=self.on_okBtn_clicked)
        okBtn.setAlignmentX(JButton.CENTER_ALIGNMENT)

        #Layout
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(iconLbl)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(titleLbl)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(p)
        self.add(wikiLblPanel)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(creditScrollPane)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(okBtn)

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
        self.pack()

    def on_okBtn_clicked(self, event):
        """Dispose About Dialog when ok button is clicked
        """
        self.dispose()

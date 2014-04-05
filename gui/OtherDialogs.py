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
from javax.swing import JDialog, JPanel, ImageIcon, JButton, JLabel,\
                        JTable, JScrollPane, BorderFactory, Box,\
                        JProgressBar, BoxLayout, WindowConstants
from java.awt import Dimension, FlowLayout
from java.io import File

#josm import
from org.openstreetmap.josm.tools import ImageProvider
from org.openstreetmap.josm.gui.widgets import JMultilineLabel

#local import
from QatDialog import MyTableModel


#### DownloadAndReadDialog #############################################
class DownloadAndReadDialog(JDialog):
    """Dialog showing the progress of errors downloading and parsing
    """
    def __init__(self, parent, title, modal, app):
        JDialog.__init__(self, parent, title, modal)

        #Download and Read Dialog
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))

        panel = JPanel()
        panel.setAlignmentX(0.5)
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.add(Box.createRigidArea(Dimension(0, 10)))

        self.progressLbl = JLabel(app.strings.getString("downloading_and_reading_errors"))
        panel.add(self.progressLbl)

        panel.add(Box.createRigidArea(Dimension(0, 10)))

        self.progressBar = JProgressBar(0, 100, value=0)
        panel.add(self.progressBar)
        self.add(panel)

        self.add(Box.createRigidArea(Dimension(0, 20)))

        cancelBtn = JButton(app.strings.getString("cancel"),
                            ImageProvider.get("cancel"),
                            actionPerformed=app.on_cancelBtn_clicked)
        cancelBtn.setAlignmentX(0.5)
        self.add(cancelBtn)

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
        self.pack()


#### FalsePositiveDialog ###############################################
class FalsePositiveDialog(JDialog):
    """Dialog which shows info regarding errors that the user believe are false positive,
       so that the user can copy their info and send a message to the tool mainteiner
       (if tool.falseFeedback == "ms").
    """
    def __init__(self, parent, title, modal, app):
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))

        #Intro
        falsePositivePng = File.separator.join([app.SCRIPTDIR,
                                                "images",
                                                "icons",
                                                "not_error36.png"])
        introLbl = JMultilineLabel(app.strings.getString("manual_false_positives_info"))
        introLbl.setMaxWidth(600)

        #Table
        table = JTable()
        columns = [app.strings.getString("Tool"),
                   app.strings.getString("Check"),
                   app.strings.getString("Error_id"),
                   app.strings.getString("OSM_id")]
        self.tableModel = MyTableModel([], columns)
        table.setModel(self.tableModel)
        scrollPane = JScrollPane(table)
        scrollPane.setAlignmentX(0.0)

        #OK button
        btnPanel = JPanel(FlowLayout(FlowLayout.CENTER))
        okBtn = JButton("OK",
                        ImageProvider.get("ok"),
                        actionPerformed=self.on_okBtn_clicked)
        btnPanel.add(okBtn)
        btnPanel.setAlignmentX(0.0)

        #Layout
        headerPnl = JPanel()
        headerPnl.setLayout(BoxLayout(headerPnl, BoxLayout.X_AXIS))
        headerPnl.add(JLabel(ImageIcon(falsePositivePng)))
        headerPnl.add(Box.createRigidArea(Dimension(10, 0)))
        headerPnl.add(introLbl)
        headerPnl.setAlignmentX(0.0)
        self.add(headerPnl)
        self.add(Box.createRigidArea(Dimension(0, 10)))
        self.add(scrollPane)
        self.add(Box.createRigidArea(Dimension(0, 10)))
        self.add(btnPanel)

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
        self.pack()

    def on_okBtn_clicked(self, event):
        """Dispose False Positive Dialog when ok button is clicked
        """
        self.dispose()

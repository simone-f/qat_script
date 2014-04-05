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
from javax.swing import JDialog, JPanel, JButton, JLabel,\
                        JScrollPane, BorderFactory, WindowConstants
from java.awt import FlowLayout, BorderLayout
from javax.swing.event import HyperlinkListener, HyperlinkEvent
from java.net import URLEncoder

#josm import
from org.openstreetmap.josm.tools import ImageProvider, OpenBrowser
from org.openstreetmap.josm.gui.widgets import HtmlPanel


#### ErrorInfoDialog ###################################################
class ErrorInfoDialog(JDialog, HyperlinkListener):
    """Dialog which shows info regarding the currently selcted error,
       so that the user can copy its info and send a message to the user
       who possibly made the error.
    """
    def __init__(self, parent, title, modal, app):
        self.app = app
        self.setSize(400, 450)
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BorderLayout(5, 5))

        #Intro
        introLbl = JLabel("<html>%s</html>" % self.app.strings.getString("error_info_intro"))

        #Panel for displaying error info
        self.infoPanel = HtmlPanel()
        self.infoPanel.getEditorPane().addHyperlinkListener(self)
        self.scrollPane = JScrollPane(self.infoPanel)

        #OK button
        btnPanel = JPanel(FlowLayout(FlowLayout.CENTER))
        okBtn = JButton(self.app.strings.getString("OK"),
                        ImageProvider.get("ok"),
                        actionPerformed=self.on_okBtn_clicked)
        btnPanel.add(okBtn)

        #Layout
        self.add(introLbl, BorderLayout.PAGE_START)
        self.add(self.scrollPane, BorderLayout.CENTER)
        self.add(btnPanel, BorderLayout.PAGE_END)

        self.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)

    def update(self):
        """Update information shown by the dialog with those of
           currently selected error
        """
        error = self.app.selectedError
        check = error.check
        view = check.view
        tool = view.tool
        text = "<html>"

        #user
        if error.user is not None:
            errorUserName = error.user.getName()
            text += "%s:" % self.app.strings.getString("Last_user")
            userUrl = "http://www.openstreetmap.org/user/%s/" % URLEncoder.encode(errorUserName, "UTF-8")
            userLink = "<a href='%s'>%s</a>" % (userUrl, errorUserName)
            msgUrl = "http://www.openstreetmap.org/message/new/%s" % URLEncoder.encode(errorUserName, "UTF-8")
            messageLink = "<a href='%s'>%s</a>" % (msgUrl, self.app.strings.getString("Send_a_message"))
            text += "<br>%s (%s)<br><br>" % (userLink, messageLink)

        #tool
        text += "%s:<br>%s" % (self.app.strings.getString("Error_reported_by_the_tool"), tool.title)
        if tool.uri != "":
            text += "<br>%s" % self.link(tool.uri)

        #error type
        if not tool.isLocal:
            text += "<br><br>%s:" % self.app.strings.getString("Type_of_error")
            text += "<br>%s --> %s" % (view.title,
                                       check.title)

        #error help, usually a link to a Wiki page describing this errror type
        #error link, e.g. a link to the error on the tool web page
        for propName, prop in ((self.app.strings.getString("Error_help"), check.helpUrl),
                               (self.app.strings.getString("Error_link"), tool.error_url(error))):
            if prop != "":
                text += "<br><br>%s:" % propName
                text += "<br>%s" % self.link(prop)

        #error description, usually some info contained in the error file
        if error.desc != "":
            text += "<br><br>%s:" % self.app.strings.getString("Description")
            text += "<br>%s" % error.desc

        text += "</html>"
        self.infoPanel.setText(text)
        self.show()

    def link(self, url):
        link = "<a href='%s'>%s</a>" % (url, url)
        return link

    def hyperlinkUpdate(self, e):
        if e.getEventType() == HyperlinkEvent.EventType.ACTIVATED:
            OpenBrowser.displayUrl(e.getURL().toString())

    def on_okBtn_clicked(self, event):
        """Dispose Error Info Dialog when ok button is clicked
        """
        self.hide()

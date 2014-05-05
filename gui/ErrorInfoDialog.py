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
from javax.swing import JDialog
from javax.swing.event import HyperlinkListener, HyperlinkEvent
from org.openstreetmap.josm.tools import OpenBrowser


#### ErrorInfoDialog ###################################################
class ErrorInfoDialog(JDialog, HyperlinkListener):
    """Dialog which shows info regarding the currently selcted error,
       so that the user can copy its info and send a message to the user
       who possibly made the error.
    """
    def __init__(self, parent, title, modal, app):
        #java import
        from javax.swing import JPanel, JButton, JLabel, ImageIcon,\
                                JScrollPane, BorderFactory, WindowConstants,\
                                BoxLayout, Box
        from java.awt import FlowLayout, Dimension, Component
        from java.io import File
        #josm import
        from org.openstreetmap.josm.tools import ImageProvider
        from org.openstreetmap.josm.gui.widgets import HtmlPanel, UrlLabel
        self.app = app
        self.setSize(400, 480)
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        self.getContentPane().setBorder(border)
        self.setLayout(BoxLayout(self.getContentPane(), BoxLayout.Y_AXIS))

        #Intro
        intro = HtmlPanel("<html><i>%s</i></html>" % self.app.strings.getString("error_info_intro"))
        intro.setAlignmentX(Component.LEFT_ALIGNMENT)

        #User info
        userLbl = JLabel(self.app.strings.getString("Last_user"))
        userLbl.setAlignmentX(JLabel.LEFT_ALIGNMENT)

        self.userInfoPanel = HtmlPanel()
        self.userInfoPanel.getEditorPane().addHyperlinkListener(self)
        self.userInfoPanel.setAlignmentX(Component.LEFT_ALIGNMENT)

        #Panel with current error's info
        errorLbl = JLabel(self.app.strings.getString("Error_info"))
        errorLbl.setAlignmentX(JLabel.LEFT_ALIGNMENT)
        self.errorInfoPanel = HtmlPanel()
        self.errorInfoPanel.getEditorPane().addHyperlinkListener(self)
        self.scrollPane = JScrollPane(self.errorInfoPanel)
        self.scrollPane.setAlignmentX(Component.LEFT_ALIGNMENT)

        #OK button
        btnPanel = JPanel(FlowLayout(FlowLayout.CENTER))
        okBtn = JButton(self.app.strings.getString("OK"),
                        ImageProvider.get("ok"),
                        actionPerformed=self.on_okBtn_clicked)
        btnPanel.add(okBtn)
        btnPanel.setAlignmentX(Component.LEFT_ALIGNMENT)

        #Layout
        self.add(intro)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(userLbl)
        self.add(Box.createRigidArea(Dimension(0, 5)))
        self.add(self.userInfoPanel)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(errorLbl)
        self.add(Box.createRigidArea(Dimension(0, 5)))
        self.add(self.scrollPane)
        self.add(Box.createRigidArea(Dimension(0, 7)))
        self.add(btnPanel)

        self.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)

    def update(self):
        """Update information shown by the dialog with those of
           currently selected error
        """
        from java.net import URL, URLEncoder
        from javax.xml.parsers import DocumentBuilderFactory
        error = self.app.selectedError
        check = error.check
        view = check.view
        tool = view.tool

        #user info
        if error.user is not None:
            errorUserName = error.user.getName()
            errorUserId = str(error.user.getId())

            #download user info from OSM API
            accountDate = None
            changesetsNumber = None

            if errorUserId in self.app.users:
                userInfo = self.app.users[errorUserId]
                accountDate = userInfo["account date"]
                changesetsNumber = userInfo["changesets number"]
            else:
                docFactory = DocumentBuilderFactory.newInstance()
                docBuilder = docFactory.newDocumentBuilder()
                url = URL("http://api.openstreetmap.org/api/0.6/user/" + errorUserId)
                try:
                    stream = url.openStream()
                    doc = docBuilder.parse(stream)
                    rootElement = doc.getDocumentElement()
                    userNode = rootElement.getElementsByTagName("user").item(0)
                    accountDate = userNode.getAttributes().getNamedItem("account_created").getNodeValue()
                    changesetsNode = rootElement.getElementsByTagName("changesets").item(0)
                    changesetsNumber = changesetsNode.getAttributes().getNamedItem("count").getNodeValue()
                except:
                    print "I could not download user info from:\n", url
                    pass
                if accountDate is not None:
                    self.app.users[errorUserId] = {"account date": accountDate,
                                                   "changesets number": changesetsNumber}

            #user links
            encodedErrorUserName = URLEncoder.encode(errorUserName, "UTF-8").replace("+", "%20")
            userUrl = "http://www.openstreetmap.org/user/%s/" % encodedErrorUserName
            msgUrl = "http://www.openstreetmap.org/message/new/%s" % encodedErrorUserName

            #update user info
            text = "<html><table>"
            text += "<tr><td>%s</td>" % self.app.strings.getString("User_name")
            text += "<td><a href='%s'>%s</a></td></tr>" % (userUrl, errorUserName)
            if accountDate is not None:
                text += "<tr>"
                text += "<td>%s</td>" % self.app.strings.getString("Changesets")
                text += "<td>%s</td>" % changesetsNumber
                text += "</tr><tr>"
                text += "<td>%s</td>" % self.app.strings.getString("Mapper_since")
                text += "<td>%s</td>"  % accountDate[:10]
                text += "</tr>"
            text += "</table>"
            text += "<a href='%s'>%s</a>" % (msgUrl, self.app.strings.getString("Send_a_message"))
            text += "</html>"
            self.userInfoPanel.setText(text)

        #error info
        text = "<html>"
        #tool
        text += "%s:<br>%s" % (self.app.strings.getString("Error_reported_by_the_tool"),
                               tool.title)
        if tool.uri != "":
            text += "<br>%s" % self.link(tool.uri)

        #error type
        if not tool.isLocal:
            text += "<br><br>%s:" % self.app.strings.getString("Type_of_error")
            text += "<br>%s --> %s" % (view.title,
                                       check.title)

        #error help, usually a link to a Wiki page describing this errror type
        #error link, e.g. a link to the error on the tool web page
        for propName, prop in ((self.app.strings.getString("Error_help"),\
            check.helpUrl), (self.app.strings.getString("Error_link"), tool.error_url(error))):
            if prop != "":
                text += "<br><br>%s:" % propName
                text += "<br>%s" % self.link(prop)

        #error description, usually some info contained in the error file
        if error.desc != "":
            text += "<br><br>%s:" % self.app.strings.getString("Description")
            text += "<br>%s" % error.desc

        #OSM object
        if error.osmId != "":
            osmType = {"n": "node", "w": "way", "r": "relation"}
            osmLinks = ""
            osmIds = error.osmId.split("_")
            for i, osmId in enumerate(osmIds):
                osmIdUrl = "http://www.openstreetmap.org/%s/%s" % (osmType[osmId[0]],
                                                                   osmId[1:])
                osmLinks += self.link(osmIdUrl)
                if i != len(osmIds) - 1:
                    osmLinks += "<br>"
            text += "<br><br>%s:" % self.app.strings.getString("OSM_objects")
            text += "<br>%s" % osmLinks

        #OSM changeset
        if error.changeset is not None:
            changesetUrl = "http://www.openstreetmap.org/changeset/%s" % error.changeset
            text += "<br><br>%s:" % self.app.strings.getString("OSM_changeset")
            text += "<br>%s" % self.link(changesetUrl)

        text += "</html>"

        #Update error info
        self.errorInfoPanel.setText(text)
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

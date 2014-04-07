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
from javax.swing import JOptionPane, SwingWorker, JPanel
from java.beans import PropertyChangeListener
from java.io import FileOutputStream, File
from java.net import URL, UnknownHostException, SocketException
from java.lang import String
from java.text import MessageFormat

from javax.swing import JDialog, BorderFactory
from java.io import FileInputStream
from java.net import URI
from java.nio.file import Files, Paths
from java.util import Properties
from java.util.jar import JarFile
from java.awt import BorderLayout, Dimension
from javax.swing import JButton, JProgressBar

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.gui.widgets import JMultilineLabel
from org.openstreetmap.josm.tools import OpenBrowser

#python import
from jarray import array


##### Updater thread ###################################################
class Updater:
    def __init__(self, app, mode):

        self.app = app
        self.mode = mode
        UpdaterTask(self).execute()
        print "- Checking for updates..."


class UpdaterTask(SwingWorker):
    """SwingWorker task used to look for any update of the script
    """
    def __init__(self, updater):
        self.app = updater.app
        self.mode = updater.mode
        SwingWorker.__init__(self)

    def doInBackground(self):
        #print "\n- Checking for the latest version..."
        try:
            url = URL(self.app.scriptVersionUrl)
            uc = url.openConnection()
            ins = uc.getInputStream()
            p = Properties()
            p.load(ins)
            latestScriptVersion = p.getProperty("script")
            self.app.latestToolsVersion = p.getProperty("tools")
        except (UnknownHostException, SocketException):
            print "I can't connect to:\n%s" % url
            ins.close()
            return

        if latestScriptVersion == self.app.SCRIPTVERSION:
            #using latest script
            print "  already using the latest script version:", self.app.SCRIPTVERSION
            if self.app.latestToolsVersion == self.app.TOOLSVERSION:
                #using latest tools
                print "  already using the latest tools version:", self.app.TOOLSVERSION
                if self.mode != "auto":
                    JOptionPane.showMessageDialog(self.app.preferencesFrame,
                                                  self.app.strings.getString("using_latest"))
                    return
            else:
                #not using latest tools
                print "  tools can be updated: %s -> %s" % (self.app.TOOLSVERSION,
                                                            self.app.latestToolsVersion)
                if app.mode == "stable":
                    infoString = self.app.strings.getString("update_tools_question")
                else:
                    infoString = self.app.strings.getString("dev_update_tools_question")
                answer = JOptionPane.showConfirmDialog(Main.parent,
                    self.app.strings.getString("update_tools_question"),
                    self.app.strings.getString("updates_available"),
                    JOptionPane.YES_NO_OPTION)
                if answer == 0:
                    #Download the updated tools data
                    print "\n- Update tools data"
                    try:
                        self.app.toolsProgressDialog
                    except AttributeError:
                        from java.awt import Dialog
                        self.app.toolsProgressDialog = ToolsProgressDialog(Main.parent,
                                                           self.app.strings.getString("download_tools_updates"),
                                                           Dialog.ModalityType.APPLICATION_MODAL,
                                                           self.app)
                    self.app.toolsProgressDialog.show()
        else:
            #not using latest script
            print "a new script version is available:\n%s -> %s" % (self.app.SCRIPTVERSION,
                                                                    latestScriptVersion)
            messageArguments = array([self.app.SCRIPTVERSION, latestScriptVersion], String)
            formatter = MessageFormat("")
            if self.app.mode == "stable":
                formatter.applyPattern(self.app.strings.getString("updates_warning"))
                infoBtnString = self.app.strings.getString("Visit_Wiki")
            else:
                formatter.applyPattern(self.app.strings.getString("dev_updates_warning"))
                infoBtnString = self.app.strings.getString("Visit_git")
            msg = formatter.format(messageArguments)
            options = [
                self.app.strings.getString("Do_not_check_for_updates"),
                infoBtnString,
                self.app.strings.getString("cancel")]
            answer = JOptionPane.showOptionDialog(Main.parent,
                msg,
                self.app.strings.getString("updates_available"),
                JOptionPane.YES_NO_CANCEL_OPTION,
                JOptionPane.QUESTION_MESSAGE,
                None,
                options,
                options[1])
            if answer == 0:
                self.app.properties.setProperty("check_for_update", "off")
                self.app.save_config(self)
            elif answer == 1:
                if self.app.mode == "stable":
                    url = self.app.SCRIPTWEBSITE
                else:
                    url = self.app.GITWEBSITE
                OpenBrowser.displayUrl(url)


##### Tools updater ####################################################
class ToolsProgressDialog(JDialog, PropertyChangeListener):
    def __init__(self, parent, title, modal, app):
        """Restore the tools data by:
           - downloading the tools list
           - downloading the tools jar files
           - extracting the tools data from jar files
        """
        self.app = app
        border = BorderFactory.createEmptyBorder(5, 7, 5, 7)
        mainPane = self.getContentPane()
        mainPane.setLayout(BorderLayout(5, 5))
        mainPane.setBorder(border)
        self.setPreferredSize(Dimension(400, 200))
        self.taskOutput = JMultilineLabel(self.app.strings.getString("checking_for_updates"))
        self.taskOutput.setMaxWidth(350)
        self.progressBar = JProgressBar(0, 100, value=0, stringPainted=True)
        self.progressBar.setIndeterminate(True)
        self.cancelBtn = JButton("Cancel",
                                 actionPerformed=self.on_cancelBtn_clicked,
                                 enabled=True)
        self.okBtn = JButton("Ok",
                             actionPerformed=self.on_okBtn_clicked,
                             enabled=False)

        mainPane.add(self.taskOutput, BorderLayout.CENTER)
        bottomPanel = JPanel(BorderLayout(5, 5))
        bottomPanel.add(self.progressBar, BorderLayout.PAGE_START)
        buttonsPanel = JPanel()
        buttonsPanel.add(self.okBtn)
        buttonsPanel.add(self.cancelBtn)
        bottomPanel.add(buttonsPanel, BorderLayout.PAGE_END)
        mainPane.add(bottomPanel, BorderLayout.PAGE_END)
        self.pack()

        self.task = DownloaderTask(self)
        self.task.addPropertyChangeListener(self)
        self.task.execute()

    def propertyChange(self, e):
        # Invoked when task's progress property changes.
        if e.propertyName == "progress":
            if e.newValue == 2:
                text = self.app.strings.getString("downloading_tools_list")
            elif e.newValue == 3:
                text = self.app.strings.getString("tools_not_downloaded_warning")
            elif e.newValue == 5:
                text = self.app.strings.getString("downloading_tools_data")
            elif e.newValue == 6:
                text = self.app.strings.getString("i_cannot_download_the_tool_files")
            elif e.newValue == 7:
                text = self.app.strings.getString("extracting_jar_files")
            elif e.newValue == 8:
                text = self.app.strings.getString("tools_updated")
            self.taskOutput.setText("<html>" + text + "</html>")

    def on_cancelBtn_clicked(self, e):
        self.dispose()
        self.task.cancel(True)

    def on_okBtn_clicked(self, e):
        self.dispose()


class DownloaderTask(SwingWorker):
    def __init__(self, gui):
        self.gui = gui
        self.app = self.gui.app
        self.toolsListFile = File.separator.join([self.app.SCRIPTDIR,
                                        "tools",
                                        "tools_list.properties"])
        self.tmpToolsListFile = File.separator.join([self.app.SCRIPTDIR,
                                        "tools",
                                        "tmp_tools_list.properties"])

        SwingWorker.__init__(self)

    def doInBackground(self):
        #Initialize progress property.
        progress = 0
        self.super__setProgress(progress)

        # "\n download tools list"
        progress = 2
        self.super__setProgress(progress)
        self.delete_file(self.tmpToolsListFile)

        if not self.download_file(self.app.toolsListUrl, self.tmpToolsListFile):
            # " I cannot download the tools list."
            progress = 3
            self.super__setProgress(progress)
            return

        toolsRefs = read_tools_list(self.tmpToolsListFile)

        #Download tools data as jar files
        progress = 5
        self.super__setProgress(progress)
        self.jarDir = File.separator.join([self.app.SCRIPTDIR, "tools", "jar"])
        if not File(self.jarDir).exists():
            File(self.jarDir).mkdir()
        else:
            #delete old files
            for jarFileName in File(self.jarDir).list():
                File(File.separator.join([self.jarDir, jarFileName])).delete()
        #download new files
        for toolRef in toolsRefs:
            jarFileName = "%s.jar" % toolRef
            jarUrl = "%s/%s" % (self.app.toolsListUrl, jarFileName)
            jarFilePath = File.separator.join([self.jarDir, jarFileName])
            answer = self.download_file(jarUrl, jarFilePath)
            if not answer:
                # " I cannot download the tools file"
                progress = 6
                self.super__setProgress(progress)
                return

        #Extract tools data from jar files
        self.toolsDir = File.separator.join([self.app.SCRIPTDIR, "tools", "data"])
        progress = 7
        self.super__setProgress(progress)
        self.extract_tools_data_from_jar_files()

        #Remove temporary file
        self.delete_file(self.toolsListFile)
        Files.copy(Paths.get(self.tmpToolsListFile), Paths.get(self.toolsListFile))
        self.delete_file(self.tmpToolsListFile)

        progress = 8
        self.super__setProgress(progress)

    def done(self):
        try:
            self.get()  # raise exception if abnormal completion
            self.gui.progressBar.setValue(100)
            self.gui.okBtn.setEnabled(True)
            self.gui.cancelBtn.setEnabled(False)
            self.app.TOOLSVERSION = self.app.latestToolsVersion
            try:
                self.app.aboutDlg
                self.app.aboutDlg.toolsVersionLbl.setText(self.app.TOOLSVERSION)
            except AttributeError:
                pass
            self.app.config.save_versions()
            print "  done."
        except:
            self.gui.taskOutput.setText(self.app.strings.getString("tools_not_correctly_updated"))
        self.gui.progressBar.setIndeterminate(False)

    def download_file(self, url, filePath):
        """Downloads a file form url and save it as filePath
        """
        try:
            print "\ndownloading"
            print url
            print filePath
            inputStream = URI.create(url).toURL().openStream()
            Files.copy(inputStream, Paths.get(filePath))
            return True
        except (UnknownHostException, SocketException), e:
            print e
            print "I cannot download:\n%s" % url
            return False

    def extract_tools_data_from_jar_files(self):
        """Create tools directories from JAR files with tools data
           Read directories from tools/data and create jar files in tools/jar
        """
        jarDir = File(self.jarDir)
        for jarFileName in jarDir.list():
            toolDir = File.separator.join([self.toolsDir, jarFileName[:-4]])
            self.delete_old_tool_directory(File(toolDir))
            jar = JarFile(File(self.jarDir, jarFileName))
            for entry in jar.entries():
                f = File(File.separator.join([self.toolsDir, entry.getName()]))
                if entry.isDirectory():
                    f.mkdir()
                    continue
                inputStream = jar.getInputStream(entry)
                fos = FileOutputStream(f)
                while inputStream.available() > 0:
                    fos.write(inputStream.read())
                fos.close()
                inputStream.close()

    def delete_old_tool_directory(self, file):
        if not file.isDirectory():
            file.delete()
        else:
            if len(file.list()) == 0:
                file.delete()
            else:
                #recursive delete
                for temp in file.list():
                    fileDelete = File(file, temp)
                    self.delete_old_tool_directory(fileDelete)
                if len(file.list()) == 0:
                    file.delete()

    def delete_file(self, fileName):
        if File(fileName).exists:
            File(fileName).delete()


def read_tools_list(tmpToolsListFile):
    """Read the tools names and tools data urls
       from the downlaoded tools list
    """
    properties = Properties()
    fin = FileInputStream(tmpToolsListFile)
    properties.load(fin)
    toolsRefs = properties.getProperty("tools.list").split("|")
    fin.close()
    return toolsRefs

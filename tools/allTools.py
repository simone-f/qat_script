#! /usr/bin/env jython

""" Defines the quality assurcance tools properties.
    Tools: OSM Inspector, KeepRight, Errori OSM Italia Grp.
"""

#java import
from javax.swing import JOptionPane, JPanel, JScrollPane, JTextArea, \
                    SwingWorker, JDialog, JLabel, BorderFactory
from java.net import UnknownHostException, SocketException
from java.io import FileInputStream, FileOutputStream, File
from java.net import URI
from java.nio.file import Files, Paths
from java.util import Properties
from java.util.jar import JarFile
from java.beans import PropertyChangeListener
from java.awt import BorderLayout, Dimension
from javax.swing import JButton, JFrame, JPanel, JProgressBar

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.gui.widgets import JMultilineLabel


##### Build all tools ##################################################
class AllTools():
    def __init__(self, app):
        """Initialize quality assurance tools
        """
        #Read tools names
        toolsListFile = File.separator.join([app.SCRIPTDIR,
                                             "tools",
                                             "tools_list.properties"])
        toolsInfo = read_tools_list(toolsListFile)

        #Create tools instances
        self.tools = []
        for toolRef, toolUrl in toolsInfo:
            if toolRef != "LocalFile":
                toolDir = File.separator.join([app.SCRIPTDIR,
                                               "tools",
                                               "data",
                                               toolRef])
                toolClass = self.import_class(toolDir, toolRef)
                if toolClass is not None:
                    self.tools.append(toolClass(app))

    def import_class(self, toolDir, toolRef):
        if File(toolDir).exists():
            modulename = "data.%s.%s" % (toolRef, toolRef)
            classname = "%sTool" % toolRef
            m = __import__(modulename, globals(), locals(), [classname])
            return getattr(m, classname)
        else:
            print "\n Tool directory is missing:", toolDir
            return None

def read_tools_list(tmpToolsListFile):
    #Read the tools names and tools data urls
       #from the downlaoded tools list

    toolsInfo = []
    properties = Properties()
    fin = FileInputStream(tmpToolsListFile)
    properties.load(fin)
    toolsRefs = properties.getProperty("tools.list").split("|")
    for toolRef in toolsRefs:
        jarUrl = properties.getProperty(toolRef)
        toolsInfo.append([toolRef, jarUrl.replace("\n", "")])
    fin.close()
    return toolsInfo"""

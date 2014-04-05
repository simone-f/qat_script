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

"""Create JAR files from local existing tools data (tools/data/*)
"""

import os


class ToolsJarCreator():
    def __init__(self):
        """
           Read directories from tools/data and create jar files in tools/jar
        """
        print "\n- Create JAR files from local existing tools data"
        from subprocess import call

        toolsDir = "data"
        jarDir = "jar"
        if os.path.isdir(jarDir):
            call("rm -r %s/*" % jarDir, shell=True)
        else:
            call("mkdir %s" % jarDir, shell=True)
        for name in os.listdir(toolsDir):
            if os.path.isdir(os.path.join(toolsDir, name)):
                jarFile = os.path.join(jarDir, "%s.jar" % name)
                cmd = "jar -cfM %s -C data %s" % (jarFile, name)
                print cmd
                call(cmd, shell=True)
        print "\n * Copy JAR files and tools_list.properties to Dropbox."


if __name__ == '__main__':
    print "Create tools jar files from tools data directories"
    ToolsJarCreator()

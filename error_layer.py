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

"""Create a layer with marker to show errors position on map.
"""

#java import
from javax.swing import ImageIcon, JOptionPane
from java.awt.image import BufferedImage

#josm import
from org.openstreetmap.josm import Main
from org.openstreetmap.josm.gui.layer import GpxLayer
from java.awt import Color
from java.awt.event import MouseListener, MouseEvent
from org.openstreetmap.josm.data.coor import LatLon


class ErrorLayer(GpxLayer, MouseListener):
    """A layer showing downloaded errors
    """
    def __init__(self, data, app, check):
        self.app = app
        self.check = check
        self.view = self.check.view
        self.tool = self.check.tool
        self.mv = self.app.mv
        self.d = data
        self.iconf = self.check.icon
        self.marker = self.check.marker

        GpxLayer.__init__(self, data, self.check.title)

    def paint(self, g, mv, bounds):
        """Paint the error layer with the correct marker.
        """
        g.setColor(Color.red)
        for wp in self.data.waypoints:
            pnt = mv.getPoint(wp.getCoor())
            if self.marker is None:
                g.fillOval(pnt.x - 5,
                           pnt.y - 11,
                           10,
                           10)
            else:
                width = self.marker.getIconWidth()
                height = self.marker.getIconHeight()
                g.drawImage(self.marker.getImage(),
                            pnt.x - (width / 2),
                            pnt.y - height - 1,
                            mv)

    def getIcon(self):
        """Set the layer icon.
        """
        if self.iconf is not None:
            return self.iconf
        else:
            img = BufferedImage(16, 16, BufferedImage.TYPE_INT_ARGB)
            g = img.getGraphics()
            g.setColor(Color.RED)
            g.fillOval(2, 2, 10, 10)
            return ImageIcon(img)

    def getNearestNode(self, p):
        #Credit: code from Openstreetbugs Plugin
        snapDistance = 10.0
        minDistanceSq = 100.0
        minError = None
        if self.check.errors is None:
            msg = "Please, download again this kind of errors."
            JOptionPane.showMessageDialog(Main.parent, msg)
            return None
        else:
            for error in self.check.errors:
                (lat, lon) = error.coords
                errorPoint = self.mv.getPoint(LatLon(lat, lon))
                dist = p.distanceSq(errorPoint)

                if p.distance(errorPoint) < snapDistance and dist < minDistanceSq:
                    minDistanceSq = p.distanceSq(errorPoint)
                    minError = error
        #if minError == None:
        #    print "No erros found nearby"
        #else:
        #    print "Dist min", minError.osmId
        return minError

    def mouseClicked(self, e):
        if(e.getButton() == MouseEvent.BUTTON1):
            if self.mv.getActiveLayer() == self:
                error = self.getNearestNode(e.getPoint())
                if error is not None:
                    selection = (self.tool, self.view, self.check)
                    self.app.on_selection_changed("layer", selection, error)
                else:
                    #no error found where the user clicked
                    self.app.reset_selected_error()

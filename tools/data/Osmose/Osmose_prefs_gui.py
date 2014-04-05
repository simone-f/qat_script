#! /usr/bin/env jython
# -*- coding: utf-8 -*-

"""Preferences for Osmose tool
"""

from javax.swing import JPanel, JLabel, JTextField, JComboBox
from java.awt import GridLayout
from java.lang import Integer, NumberFormatException


class PrefsPanel(JPanel):
    """JPanle with gui for tool preferences
    """
    def __init__(self, app):
        strings = app.strings

        self.setLayout(GridLayout(3, 2, 5, 5))
        userLbl = JLabel(strings.getString("osmose_pref_username"))
        self.userTextField = JTextField(20)
        self.userTextField.setToolTipText(strings.getString("osmose_pref_username_tooltip"))

        levelLbl = JLabel(strings.getString("osmose_pref_level"))
        self.levels = ["1", "1,2", "1,2,3", "2", "3"]
        self.levelsCombo = JComboBox(self.levels)
        self.levelsCombo.setToolTipText(strings.getString("osmose_pref_level_tooltip"))

        limitLbl = JLabel(strings.getString("osmose_pref_limit"))
        self.limitTextField = JTextField(20)
        self.limitTextField.setToolTipText(strings.getString("osmose_pref_limit_tooltip"))

        self.add(userLbl)
        self.add(self.userTextField)
        self.add(levelLbl)
        self.add(self.levelsCombo)
        self.add(limitLbl)
        self.add(self.limitTextField)

    def update_gui(self, preferences):
        """Update preferences gui
        """
        self.userTextField.setText(preferences["username"])
        self.levelsCombo.setSelectedIndex(self.levels.index(preferences["level"]))
        self.limitTextField.setText(str(preferences["limit"]))

    def read_gui(self):
        """Read preferences from gui
        """
        username = self.userTextField.getText()
        level = self.levelsCombo.getSelectedItem()
        limit = self.limitTextField.getText()
        try:
            limit = Integer.parseInt(limit)
            if limit > 500:
                limit = 500
            limit = str(limit)
        except NumberFormatException:
            limit = ""

        preferences = {"username": username.strip(),
                       "level": level,
                       "limit": limit}
        return preferences

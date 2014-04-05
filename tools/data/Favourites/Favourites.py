#! /usr/bin/env jython

# tool  : local file

from ...tool import Tool


class FavouritesTool(Tool):
    def __init__(self, app):
        self.app = app

        #Tool title
        self.title = "Favourites"

        #Tool url
        self.uri = ""

        #Translations
        self.isTranslated = True

        #Corrected errors
        self.fixedFeedbackMode = None

        #False positives
        self.falseFeedbackMode = None

        self.isLocal = True

        #Additional preferences for this tool
        self.prefsGui = None

        #Tool checks
        #{view: [title, name, url, icon, marker], ...}
        self.toolInfo = {"View": []}

        Tool.__init__(self, app)

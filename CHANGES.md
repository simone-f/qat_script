development
===========
* Russian translation, thanks to [Edward17](http://wiki.openstreetmap.org/wiki/User:Edward17) and [Xmypblu](http://wiki.openstreetmap.org/wiki/User:Xmypblu).

Supported tools v0.2beta1
-------------------------

* New tool: [**Opening Hours Validator**](http://openingh.openstreetmap.de/), by Robin Schneider

v0.6
====
New features:

* **Favourite checks** can be picked from the checks of all the supported QA Tools (right-click on a check name). <br>They will be collected in the new "Favourites" tool, to easily find them again.
* **Multiple favourite zones** can be created and previewed on a map inside JOSM (credit to imagery preferences).<br>They can be built from Preferences dialog or by adding text files (with WKT geometry or bbox for rectangular area) into `qat_script/configuration/favourite_zones` directory.
* An **help link** is provided for each check (right click on a check name) pointing to the OSM Wiki page describing that error kind, if this does exist.
* An **information dialog** can be opened while fixing an error (request from Poppei82).<br>Current error information can be copied and sent to the last user who touched the OSM object affected by the error and possibly made it.
* A **local GPX file with errors** can be opened from QA Tools menu. Anyone finding erros while processing OSM data can create GPX files with a waypoint for each error and give it to local mappers to check them in sequence, like with the regular  tools. `desc` tag content is shown in QATs dialog while `osmid` is used to select an object. Example:


```xml
<desc>Here there is a self intersecting geometry</desc>
<extensions>
    <ogr:osmid>w12345567</ogr:osmid>
</extensions>
```

* **Tools can be updated**. If new tools, checks or tools translations are supported they can be donwloaded whithout having to download all the script again.
* Now multiple error kinds can always be selected and downloaded. If a tool does not return more than one error type per request, requests are queued.
* The panel with stats hides if no information are present regarding the selected check (the number of fixed/downloaded errors).
* Favourites zones Preferences can be opened also by clicking on the favourite zone status icon.

Tools:

* New tool: [**housenumbervalidator**](http://gulp21.bplaced.net/osm/housenumbervalidator/), by User:Gulp21 (request from Poppei82)
* False positives errors can now be reported for "OSM Italia Grp" QA tool.

Fixes and cleanup:

* GUIs for downloading errors and fixing them in sequence are separated in two tabs, to give more space to checks table and error description.
* (Reported by Poppei82) "The configuration dialogue isn't visible in the window panel". Preferences are now displayed on a JFrame.
* (Reported by Xmypblu) Some boundaries with spaces in names cannot be downoloaded from overpass to use them as favourite zone.
* (Reported by Xmypblu, fixed by Akks) Encoding problems on errors descriptions.
* Default JOSM icons are used for buttons where it's possible (OK,  Cancel, Refresh...) and Java File.separator is used instead of Python os.path.join.
* FalsePositiveDialog width is fixed.
* New logo.
* A lot of code has been refactorized by separating classes to different files.
* German and French translations updated by Poppei82 and operon.

v0.5.1
======
- Max number of errors that can be downlaoded from KeepRight changed from 100 to 10000 (thanks to Harald Klainer for accepting this feature request). Changed the text of the warning regarding errors limit and disabled the popup by default.
- (Request from Poppei82) Disable favourite area editing when favourite area is not active.
- When the favourite area is active an icon appears, as a warning, with the name of area as tooltip.
- Small changes to the gui of max number of downloadable errors.
- Increased the number of errors downloaded from Osmose by default to 500.
- Fixed max number of errors limiting when favourite area is active.
- Fixed some strings and added some translations. Thanks to mappers Poppei82 for German and operon for French.

v0.5
====
Thanks to: Poppei82, operon and Marco Braida for translations, hints and testing for this version.

- (Request by Operon) Translations: Italian (Groppo), French (operon), German (Poppei82)
- The script can now be launched from any directory. If the script can't understand where it is, it will ask to the user to move qat_script directory to the default directory ('plugins/scripting directory' into JOSM settings).
- (Request by Leonardo) Multiple error kinds from the same view can now be selected and downloaded (this has been enabled for KeepRight thanks to a change by its author, Harald Kleiner).
- (Request by Poppei82) A favourite area can now be set from the Preferences dialog. When activated, only errors within it will be downloaded. This area can be e ractangle (bbox), a polygon drawn by hand or can corrispond to an administrative boundary with specific tags.
- (Request by Poppei82) A maximum number of errors to show can be set from Preferences.
- Some settings can be made for Osmose tool from Preferences (number or severity of errors, username of the mapper).
- (Request by Marco Braida) New check: OSM Inspector--> Geometry --> Way with single node
- Fix bug (reported by Operon): the toggle dialog can't be minimized.
- Fix bug (reported by sabas88): error when using OSM Inspector and clicking on "Not an error"
- Fix bug (reported by Marco Braida): it shows only the first of multiple errors, of the same kind, on the same object.
- Fix bug: sometimes changes in views combobox do not update views items.

v0.4
====
- Added new errors detecting tool: Osmose (http://osmose.openstreetmap.fr/).
- (Request by Operon) Show a warning message the first time the button "Not an error" is pressed.
- If the script is launched from JOSM front page, automatically zoom to the latest downloaded zone, instead of (0.0, 0.0).
- Reduced a bit the startup time (from 8s to 4s), by substituting Pyhton modules with Java (urllib2 -> URLConnection, Configparser -> Properties, random -> Collections.shuffle).
- New, more visible markers for errors form "OSM Inspector" and "Errori OSM Italia Grp" tools.
- Move the error layer to the top after creation, for more visibility.
- Added a Preferences dialog.
- The user can now choose from the Preferences dialog how to manage errors layers when a new one is downloaded: hide or remove them all, hide or remove only the layers with the same kind of errors.
- After the last error has been corrected zoom out to see all the edited zone.
- Fixes: use pack() for dialogs.

v0.3
====
- Download errors in current zone when the user double clicks a check in the list
- (Request by Poppei82) Select the way/node affected by error after the error is downloaded from KeepRight. Thanks to Harald Kleiner for adding OSM id and object type in KeepRight GPX files.
- (Request and contribution by Marco Braida) Color the text that shows the number of errors downloaded: red if > 0, green if 0 (substituting the dialog "No errors found...")
- (Request by Marco Braida) Check for updates when the script is launched (this can be disabled from 'config.cfg' file). If there is an update a dialog shows up asking the user if he/she wants to visit Wiki page. If he/she answer "No", the script won't check for updates anymore
- There is now a configuration file ('config.cfg') from which the user can disable a specific tool or the automatic check for updates
- If an error from KeepRight has a comment, show it in error description
- Fix bug (reported by Marco Braida): if after all errors are corrected the user downloads some error of the same check, only errors[:-1] can be corrected
- Fix bug: missing import Color in gui.py
- Fix bug: missing decode("utf-8") of text with selected error description.
- Fix bug (reported by Marco Braida): it doesn't write error description of errors regarding relations.
- (Marco Braida) Fix bug: cannot look for updates when behind a proxy.
- Other minor changes and fixes

v0.2
====
- Fix bug (reported by Poppei82): wrong url for reporting corrected errors or false positive in central Europe to KeepRight

v0.1.2
======
- Added three new checks. Tool: OSM Inspector --> View: Addresses --> Checks: No addr:street, Street not found, Interpolation errors.
- Moved IconRenderer class to gui.py
- Fixed bug: exception when a markers layer is active and the user clicks far from a marker (AttributeError 'resetCurrentError')
- Fixed bug (reported by Aury88): downloaded area for "OSM Inspector", "duplicate ways" error is too little. Added a check that enlarges bbox when necessary.
- Fixed bug: exception when parsing canceled by user.

v0.1.1
======
- Centered the first column of checks table in qat dialog
- Disabled a tool by commenting its line in 'tools/allTools.py'
- Change README to README.md
- Minor changes to 'tools/README' file
- Changed menu title from "Errors" to "QA Tools"
- Fixed bug (reported by Leonardo "Darkswan"): "se scaricate un Check che ha 0 errori, vi spostate su quello successivo e ritornate sopra al primo, JOSM genera una "Eccezione inattesa""
- Fixed bug: it tries to parse an errors file even if this was not downloaded because connection wasn't working or the file was not found on the server

Quality Assurance Tools script
==============================
Quality Assurance Tools script (qat_script) is a script for JOSM (Java OpenStreetMap Editor) that lets the user download OSM errors from some error detecting tool and review them one after another.

![qat_script menu in JOSM](http://dl.dropboxusercontent.com/u/41550819/OSM/qat_script/wiki_img/qat_script_menu_small.png "qat_script menu in JOSM")

![qat_script dialog in JOSM, errors downloading](http://dl.dropboxusercontent.com/u/41550819/OSM/qat_script/wiki_img/qat_script_dialog_download_small.png "qat_script dialog in JOSM, errors downloading")

![qat_script dialog in JOSM, errors fixing](http://dl.dropboxusercontent.com/u/41550819/OSM/qat_script/wiki_img/qat_script_dialog_fixing_small.png "qat_script dialog in JOSM, errors fixing")

[Video on how to use it](http://bit.ly/ZTwj0Z) (webm, 35.3MB)

## Features:

* **Errors download** of currently observed area in JOSM, from different error detectors. The type of error can be selected from a menu or a toggle dialog, in the second case, multiple kinds of error can be downloaded at once.
* **Progressive correction** of downloaded errors by clicking on a button (next, next, next...).
* Automatic flag to server (''KeepRight'', ''Osmose'', ''Errori in OSM Italia Grp'', ''housenumbervalidator'') of **false positive** errors or information gathering for manual report (''OSM Inspector'') to the tool admin.
* Flag errors to be **ignored**. They will be stored on a local black-list file and not shown to the mapper again.
* **Clickable markers** for zooming/downloading a specific error. The level of the clicked marker must be activated.
* Multiple **favourite zones** can be set so that only errors within it will be downloaded. It can be a ractangle, a polygon drawn by hand or an administrative boundary with specific tags.
* A list of **favourites checks** can be created by selecting different checks belonging to different tools and find them again quickly.
* A **local GPX file** can be opened. Its waypoints will be used as positions that the user can visits in sequence to check for errors (more info on the [Wiki](http://wiki.openstreetmap.org/wiki/Quality_Assurance_Tools_script)).

## Supported QA Tools:

* [OSM Inspector](http://tools.geofabrik.de/osmi/) by GEOFABRIK (only some types of errors)
* [KeepRight](http://keepright.ipax.at/) by Harald Kleiner
* [Osmose](http://osmose.openstreetmap.fr/)
* [Errori in OSM Italia Grp](https://dl.dropboxusercontent.com/u/41550819/OSM/Errori_in_Italia_Grp)
* [housenumbervalidator](http://gulp21.bplaced.net/osm/housenumbervalidator/) by Gulp21
* [Opening Hours Validator](http://openingh.openstreetmap.de/) by Robin Schneider

Installation and how to
-----------------------
For installation and usage see [Quality Assurance Tools script page](http://wiki.openstreetmap.org/wiki/Quality_Assurance_Tools_script) on OpenStreetMap Wiki.

Development
-----------
Author: Simone F. <groppo8@gmail.com>

License: GPLv2

To add a new QA tool read the file [tools/README.md](tools/README.md).

Note: I wrote a Python script, that can be run in JOSM thanks to [JOSM Scripting plugin](http://gubaer.github.io/josm-scripting-plugin/), rathar than a regular JOSM plugin because I just know Python. I would be happy if someone could create a Java plugin with these features.

### Credits and contributors
Thanks to QA tools' authors and to the mappers who contributed by translations, testing, reporting bugs or suggesting new features (mcheck, Poppei82, operon, Xmypblu, Edward17 ...)<br>Their names are in CONTRIBUTORS and CHANGES files.

### Attributions
* KeepRight, Geofabrik and Osmose logos have been drawn in Inkscape and are based on the official logos.
* KeepRight checks icons are from [KeepRight website](http://keepright.ipax.at/).
* Osmose checks icons are from [Osmose website](http://osmose.openstreetmap.fr/).
* housenumebrvalidator icons are from [housenumbervalidator](http://gulp21.bplaced.net/osm/housenumbervalidator/)
* qat_script logo.png build upon [Openstreetmap_logo.svg](http://commons.wikimedia.org/wiki/File:Openstreetmap_logo.svg) (CC BY-SA 2.0) and [Red_bug.svg](http://commons.wikimedia.org/wiki/File:Red_bug.svg) by Mushii, Anomie (CC BY-SA 3.0)
* icons of buttons build upon [Green_bug.svg](http://commons.wikimedia.org/wiki/File:Green_bug.svg) by Mushii (CC BY-SA 3.0) and [Red_bug.svg](http://commons.wikimedia.org/wiki/File:Red_bug.svg) by Mushii, Anomie (CC BY-SA 3.0)
* favourites tool icon from [candyadams](http://openclipart.org/detail/93169/star-by-candyadams) (Public Domain)
* browser.png from [Internet-web-browser.svg](http://commons.wikimedia.org/wiki/File:Internet-web-browser.svg) by The Tango! Desktop Project (PD)

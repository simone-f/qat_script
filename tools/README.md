Adding a new quality assurance tool to the script
=================================================
New Quality Assurance Tools can be added to the script:

1. Create a new directory 'qat_script/tools/data/NameOfTheTool'.
2. Create a new file 'qat_script/tools/data/NameOfTheTool/NameOfTheTool.py', with a class 'NameOfTheToolTool' in it. Use tools/FakeTool.py as a template.
3. Add 'NameOfTheTool' to the list of tools in 'qat_script/tools/tools_list.properties' (not beyond 'Favourites').

The script regularly checks for tools updates from git repository. If you choose to download the updates you must then manually add your tool's name to 'qat_script/tools/tools_list.properties' again.

Using a local file with errors
==============================
If you have found some errors in OSM and you want to review them in sequence with qat_script in JOSM, instead of creating a new tool you may create a GPX file with the errors as way points.

See the [Wiki](http://wiki.openstreetmap.org/wiki/Quality_Assurance_Tools_script#Local_file) for more information.




== How to add a new tool to the script ==
New Quality Assurance Tools can be added to the script, here is how to do it.

1. Create a new file tools/NameOfTheTool.py, with a class NameOfTheToolTool in it.
   See tools/FakeTool.py for an example.
2. Append a new tool instance creation to the list AllTools.tools, in tools/allTools.py. 
3. Describe how to parse an errors file in the method ParseTask.doInBackground, in tools/tool.py 
4. Add the new tool to the preferences file, "config.properties", and turn it on:
tool.osmose=on




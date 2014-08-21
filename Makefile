
.PHONY: build
build: pyopening_hours

# jython can not read symbolic links?
pyopening_hours:
	git submodule update --init --recursive
	mv git_submodules_of_libs/pyopening_hours/pyopening_hours pyopening_hours

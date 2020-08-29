#!/usr/bin/env sh

rm -rf build dist
pyinstaller --noconfirm \
	--onefile \
	--hidden-import='pyvisa-py' \
	--hidden-import='pkg_resources.py2_warn' \
	--add-data=template.ini:. \
	--add-data=README.html:. \
	e4990a.py

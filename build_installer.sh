#!/usr/bin/env sh

pyinstaller --clean \
	--noconfirm \
	--onefile \
	--hidden-import='pyvisa_py' \
	--add-data=template.ini:. \
	e4990a.py

@echo off

rmdir /s /q build dist
%~dp0venv\Scripts\pyinstaller.exe --noconfirm ^
	--onefile ^
	--hidden-import="pyvisa-py" ^
	--hidden-import="pkg_resources.py2_warn" ^
	--add-data="template.ini;." ^
	--add-data="README.html;." ^
	e4990a.py

@echo off

WHERE /Q pyinstaller.exe
IF %ERRORLEVEL% NEQ 0 (
  set pyinstaller=%~dp0venv\Scripts\pyinstaller.exe
) ELSE (
  set pyinstaller=pyinstaller.exe
)
echo %pyinstaller%
%pyinstaller% --clean ^
	--noconfirm ^
	--onefile ^
	--hidden-import="pyvisa-py" ^
	--hidden-import="pkg_resources.py2_warn" ^
	--add-data="template.ini;." ^
	--add-data="README.html;." ^
	e4990a.py

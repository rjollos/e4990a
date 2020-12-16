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
	--hidden-import="pyvisa_py" ^
	--add-data="template.ini;." ^
	e4990a.py

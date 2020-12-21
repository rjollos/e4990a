@echo off

WHERE /Q pyinstaller.exe
IF %ERRORLEVEL% NEQ 0 (
  set pyinstaller=%~dp0venv\Scripts\pyinstaller.exe
) ELSE (
  set pyinstaller=pyinstaller.exe
)
echo %pyinstaller%
set distname=win
%pyinstaller% --clean ^
	--distpath .\dist\%distname% ^
	--noconfirm ^
	--onedir ^
	--hidden-import="pyvisa_py" ^
	--add-data="template.ini;." ^
	e4990a.py

set scriptname=dist\e4990a.bat
(
@echo @echo off
@echo .\%distname%\e4990a\e4990a %%*
)>%scriptname%

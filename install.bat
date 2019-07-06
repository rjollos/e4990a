@echo off

set venv=%~dp0venv
C:\Python37\python.exe -m venv "%venv%"
set python=%venv%\Scripts\python.exe
"%python%" -m pip install -U pip
"%python%" -m pip install -r requirements.txt
"%python%" -m markdown -x gfm README.md > README.html


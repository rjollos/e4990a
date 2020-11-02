@echo off

set venv=%~dp0venv
C:\Python39\python.exe -m venv "%venv%"
set python=%venv%\Scripts\python.exe
"%python%" -m pip install -U pip
"%python%" -m pip install -r requirements.txt
"%python%" -m pip install -r requirements-dev.txt
"%python%" -m markdown -x extra README.md > README.html


# E4990A Change Log

## 2.2 (2019-05-07)
* Added option -a/--append-datetime for appending an ISO 8601 timestamp
  to the filename.

## 2.3 (2019-05-22)
* Only prompt to exit if plotting enabled
* Added marker at peak of channel 1 trace

## 2.4 (2019-05-23)
* Added batch file to simplify execution.
* Added batch file to simplify installation.
* Fixed parsing of segments from ini file.
* Segmented sweep display window has linear frequency scale.

## 2.5 (2019-06-20)
* Fixed incorrect reporting of acquisition time.
* Report acquisition time in ms rather than s.

## 2.6 (2020-12-16)
* Install creates README.html from README.md.
* Added MATLAB function for plotting impedance data.
* Added install and execution scripts for OSX.
* Fixed poor performance and timeout over TCP/IP.
* Added build of executable using PyInstaller.
* Upgraded dependencies and pinned install requirements.
* Upgrade to Python 3.9
* Added build of executables using GitHub Actions.
* Added script for creating a release.

## 2.7 (To be released)
* Change to single-dir rather than single-file
  package to avoid slow extraction time from file.
* Implictly clear quarantine attribute on macOS.
* Upgrade to Python 3.9.5

# Description

This is a python script for acquiring from the Keysight E4990A impedance analyzer. The script repeatedly captures a frequency sweep from the E4990 at a specified time interval and saves the data in a MAT file. The capture parameters are configured in the `e4990a.ini` file.

The [PyVISA](https://pyvisa.readthedocs.io) library is used to communicate with the device over a USB link. The device driver and visa backend are provided by the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).

## Installation

1. Install the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).
1. Install [Python](https://www.python.org/downloads/windows/) to `C:\Python37`.
1. Open Command Prompt and create a Python environment.
    ```
    > C:\Python37\python.exe -m venv venv
    > venv\Scripts\activate.bat
    > python -m pip install -U pip
    > python -m pip install -r requirements.txt
    ```

## Execution

1. Open Command Prompt and activate the virtual environment.
    ```
    > venv\Scripts\activate.bat
    ```
1. Set the capture parameters in `e4990a.ini`.
1. Execute the fixture compensation procedure.
    ```
    > python -m e4990a -c
    Visa Library at C:\Windows\system32\visa64.dll
    Starting fixture compensation procedure
    Put the test fixture's device contacts in the OPEN state and press [ENTER]
    Put the test fixture's device contacts in the SHORT state and press [ENTER]
    ```

1. Execute the script and accept the default filename for storing the data, or specify the filename. The `.mat` extension will be appended if not provided.
    ```
    > python -m e4990a
    Enter a filepath or press [ENTER] to accept the default (20181020T182322.mat):
    ```

The configuration file can be specified using the `--config` parameter:
```
> python -m e4990a --config=e4990a-2.ini
```

View the script documentation:
```
> python -m e4990a -h
```

## Tested With

* Windows 10
* Python 3.7.1 x86-64
* Keysight IO Libraries Suite 18.1

## TODO

1. Can the script be run from Linux and/or OSX? The Keysight IO libraries are Windows-only and a device driver seems to be needed to communicate with the instrument over the USB interface. The device driver might not be needed if the E4990A ethernet interface is used.

## References

* [Keysight E4990A impedance analyzer](https://www.keysight.com/en/pd-2405177-pn-E4990A/impedance-analyzer-20-hz-to-10-20-30-50-120-mhz)
* [Keysight E4990A help](http://ena.support.keysight.com/e4990a/manuals/webhelp/eng/index.htm)

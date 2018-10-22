# Description

This is a python script for acquiring from the Keysight E4990A impedance analyzer. The script repeatedly captures a frequency sweep from the E4990 at a specified time interval and saves the data in a MAT file. The capture parameters are configured in the `e4990.ini` file.

The [PyVISA](https://pyvisa.readthedocs.io) library is used to communicate with the device over a USB link. The [PyVISA-py](https://pyvisa-py.readthedocs.io/en/latest/) is used as the backend for PyVISA. The device driver is provided by the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).

## Installation

1. Install the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).
1. Install [Python](https://www.python.org/downloads/windows/) to `C:\Python37`.
1. Create a Python environment.
    ```
    PS> C:\Python37\python.exe -m venv venv
    PS> venv\Scripts\activate.ps1
    PS> python -m pip install -U pip
    PS> python -m pip install -r requirements.txt
    ```

## Execution

1. Activate the virtual environment
    ```
    PS> venv\Scripts\activate.ps1
    ```
1. Set the capture parameters in `e4990.ini`
1. Execute the script and accept the default filename for storing the data, or specify the filename. The `.mat` extension will be appended if not provided.
    ```
    PS> python -m e4990
    Enter a filepath or press [ENTER] to accept the default (20181020T182322.mat):
    ```

## Tested With

* Windows 10
* Python 3.7.1 x86-64
* Keysight IO Libraries Suite 18.1

## TODO

1. Pass the INI filename as a script option.
1. Can the script be run from Linux and/or OSX? The Keysight IO libraries are Windows-only and a device driver seems to be needed to communicate with the instrument over the USB interface. The device driver might not be needed if the E4990A ethernet interface is used.

## References

* [Keysight E4990A impedance analyzer](https://www.keysight.com/en/pd-2405177-pn-E4990A/impedance-analyzer-20-hz-to-10-20-30-50-120-mhz)
* [Keysight E4990A help](http://ena.support.keysight.com/e4990a/manuals/webhelp/eng/index.htm)

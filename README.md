# Description

This is a python script for acquiring from the Keysight E4990A impedance analyzer. The script repeatedly captures a frequency sweep from the E4990 at a specified time interval and saves the data in a MAT file. The capture parameters are configured in the `e4990a.ini` file.

The [PyVISA](https://pyvisa.readthedocs.io) library is used to communicate with the device over a USB link. The device driver and visa backend are provided by the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).

## Installation

1. Install the [Keysight IO Libraries Suite](https://www.keysight.com/en/pd-1985909/io-libraries-suite).
1. Install [Python](https://www.python.org/downloads/windows/) to `C:\Python37`.
1. Clone this repository.
1. Run the `install` script.


## Execution

1. Set the capture parameters in `e4990a.ini`.
1. Execute the fixture compensation procedure.
    ```
    > e4990a -c
    Visa Library at C:\Windows\system32\visa64.dll
    Starting fixture compensation procedure
    Put the test fixture's device contacts in the OPEN state and press [ENTER]
    Put the test fixture's device contacts in the SHORT state and press [ENTER]
    ```

1. Execute the script and accept the default filename for storing the data, or specify the filename. The `.mat` extension will be appended if not provided.
    ```
    > e4990a
    Enter a filepath or press [ENTER] to accept the default (20181020T182322.mat):
    ```

## Options

The configuration file can be specified using the `--config` parameter:
```
> e4990a --config=e4990a-2.ini
```

Data files can be output to a directory:
```
> e4990a 20190705/DeviceA7
```
* The directory will be created if it does not exist.
* The forward slash must be used as the path separator.
* The extension `.mat` is appended if not specified.

A timestamp can be appended to the given filename using the `-a` parameter:
```
> e4990a -a 20190705/DeviceA7
...
Data saved to "20190705\DeviceA7-20190705T213856.mat"
```

View the script documentation:
```
> e4990a -h
```

## Reading Data

The MATLAB function `read_e4990a_data.m` reads the MAT file and returns
a structure. The numeric fields of the structure, which are stored in the
MAT file using their intrinsic types, are cast to type `double` for
convenience of working with the data in MATLAB.

## Tested With

* Windows 10
* Python 3.7.1 x86-64
* Keysight IO Libraries Suite 18.1

## TODO

1. Can the script be run from Linux and/or OSX? The Keysight IO libraries are Windows-only and a device driver seems to be needed to communicate with the instrument over the USB interface. The device driver might not be needed if the E4990A ethernet interface is used.

## References

* [Keysight E4990A impedance analyzer](https://www.keysight.com/en/pd-2405177-pn-E4990A/impedance-analyzer-20-hz-to-10-20-30-50-120-mhz)
* [Keysight E4990A help](http://ena.support.keysight.com/e4990a/manuals/webhelp/eng/index.htm)

# Description

This is a python application for acquiring from the Keysight E4990A
impedance analyzer. The script captures a frequency sweep from the
E4990A and saves the data in a MAT file. The capture parameters are
configured in the `e4990a.ini` file. The USB or ethernet interface of
the E4990A can be used.

The [PyVISA](https://pyvisa.readthedocs.io) library is used to communicate with the device.

## Execution

The application entry point is named `e4990a.bat` on Windows and `e4990a`
on macOS / Linux. On macOS / Linux the permissions of the script need to
be changed after extracting the zip archive:
```
$ chmod 755 e4990a
```

On macOS, the quarantine flag
([Gatekeeper](https://en.wikipedia.org/wiki/Gatekeeper_(macOS)))
will need to be cleared if the archive was downloaded through the
web browser:
```
$ sudo xattr -r -d com.apple.quarantine .
```

Run the application once to generate the default `e4990a.ini`.
The INI file can then be edited or copied. Replace `./e4990a` with
`e4990a.bat` when running on Windows.

1. Set the capture parameters in `e4990a.ini`.
1. Execute the fixture compensation procedure.

        $ ./e4990a -c
        Opening resource: TCPIP::192.168.11.227::INSTR
        Starting fixture compensation procedure
        Put the test fixture's device contacts in the OPEN state and press [ENTER]
        Put the test fixture's device contacts in the SHORT state and press [ENTER]

1. Execute the script and accept the default filename for storing the data, or specify the filename. The `.mat` extension will be appended if not provided.

        $ ./e4990a
        Enter a filepath or press [ENTER] to accept the default (20181020T182322.mat):
The filename can be a relative or absolute path.

## Instrument communication

USB and TCP/IP instrument communication is supported. The communication
is configured in the `[resource]` section. Remove or comment-out the
section for USB communication. For TCP/IP, set the `ip_address`.

The E4990A IP address can be discovered through the instrument panel
System > Misc Setup > Network Setup > LAN Dialog. Manually assign a fixed
IP address through the router to persist the configuration.

## Options

View the configuration parameters:
```
$ ./e4990a -h
```

The configuration file can be specified using the `--config` parameter:
```
$ ./e4990a --config=e4990a-2.ini
```

Data files can be output to a specified directory using a specified prefix:
```
$ ./e4990a 20190705/DeviceA7
```
* The directory will be created if it does not exist.
* The forward slash must be used as the path separator, even on Windows.
* The extension `.mat` is appended if not specified.

A timestamp can be appended to the given filename using the `-a` parameter:
```
$ ./e4990a -a 20190705/DeviceA7
...
Data saved to "20190705\DeviceA7-20190705T213856.mat"
```

The default filename can be specified to avoid being prompted:
```
$ ./e4990a -d
```
The default filename is an ISO9601 datetime stamp.

## INI File

Uniform sampling is supported with the following options:
```
start_frequency = 500e3
stop_frequency = 5e6
number_of_points = 401
```
Start and stop frequency are specified in Hz.

Segmented sampling is supported by specifying a single option:
```
segments = 500e3,1400e3,19,1410e3,2400e3,100,2500e3,5000e3,26
```
Each triplet specifies a single segment: start frequency, stop
frequency, number of points (e.g. 500e3,1400e3,19). Any number
of segments can be specified.

An error will occur if the options for both uniform and segmented
sampling are specified in the INI file.

## Reading Data

The MATLAB function `read_e4990a_data.m` reads the MAT file and returns
a structure. The numeric fields of the structure, which are stored in the
MAT file using their intrinsic types, are cast to type `double` for
convenience of working with the data in MATLAB.

The MATLAB function `plot_impedance.m` plots the impedance data.

## Development

1. (Windows only) Install [Python](https://www.python.org/downloads/windows/) to `C:\Python38`.
1. Clone this repository.
1. Run the `install` script (`install.bat` on Windows, `install.sh` on Unix).
1. Run the `build_installer` script (`build_installer.bat` on Windows,
   `build_installer.sh` on Unix).

After making code changes, run `pylint` and fix errors/warnings before commit:
```
$ pylint e4990a.py
```
The configuration of `pylint` is in `.pylintrc`.

## Tested With

* Windows 10 and macOS 10.15
* Python 3.9.1 x86-64

## Dependencies
* [PyVISA-py](https://pypi.org/project/PyVISA-py)
* [PyVISA](https://pypi.org/project/PyVISA)
* [matplotlib](https://pypi.org/project/matplotlib)
* [scipy](https://pypi.org/project/scipy)
* [Markdown](https://pypi.org/project/Markdown)
* [pyinstaller](https://pypi.org/project/pyinstaller)

## References

* [Keysight E4990A impedance analyzer](https://www.keysight.com/en/pd-2405177-pn-E4990A/impedance-analyzer-20-hz-to-10-20-30-50-120-mhz)
* [Keysight E4990A help](http://ena.support.keysight.com/e4990a/manuals/webhelp/eng/index.htm)

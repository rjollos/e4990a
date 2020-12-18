#!/usr/bin/env python
"""Acquisition script for Keysight E4990A."""

import argparse
import collections
import configparser
import datetime
import functools
import numbers
import pathlib
import shutil
import subprocess
import sys
import time
import traceback

import matplotlib.pyplot as pyplot
import numpy
import pyvisa
import scipy.io as scio

FILE_EXT = '.mat'
CONFIG_FILENAME_DEFAULT = 'e4990a.ini'
program_version = None
time_now = None
__version__ = '2.6'


class E4990AError(Exception):
    """Exception class for all errors raised in this module.

    The `main` function has an exception handler for this class.
    """


def to_number(f, s):
    """Convert string to a number with format specified by `f`."""
    if s is None:
        return s
    if isinstance(s, numbers.Number):
        return f(float(s))
    if ',' in s:  # comma-separated values
        return [f(float(i.strip())) for i in s.strip().split(',')]
    return f(float(s.strip()))


def to_int(s):
    """Convert string to an integer."""
    return to_number(int, s)


def to_float(s, precision=None):
    """Convert string to a float."""
    if precision is not None:
        f = functools.partial(round, ndigits=precision)
    else:
        f = lambda x: x
    return to_number(f, s)


def resource_path(file_name):
    """Resolve filename within the PyInstaller executable."""
    try:
        base_path = pathlib.Path(sys._MEIPASS)
    except AttributeError:
        base_path = pathlib.Path('.').resolve()
    return base_path.joinpath(file_name)


def acquire(filename, config_filename, fixture_compensation):
    """Read the configuration file, initiate communication with the
    instrument and execute the sweep or fixture compensation.
    """
    cfg = read_config(config_filename)
    rm = pyvisa.ResourceManager()
    print(rm.visalib)
    if cfg.ip_address:
        resource_name = f'TCPIP::{cfg.ip_address}::INSTR'
    else:
        resources = rm.list_resources('USB?*INSTR')
        if not resources:
            raise E4990AError("No USB instruments found")
        if len(resources) > 1:
            msg = "Multiple USB instruments found:\n"
            for r in resources:
                msg += ('\t' + r)
            raise E4990AError(msg)
        resource_name = resources[0]

    print(f"Opening resource: {resource_name}")
    try:
        inst = rm.open_resource(resource_name)
    except pyvisa.errors.VisaIOError as e:
        raise E4990AError(f"{e}") from e
    # Timeout must be longer than sweep interval.
    inst.timeout = 15000
    try:
        if fixture_compensation:
            run_fixture_compensation(inst, cfg)
        else:
            try:
                run_sweep(inst, filename, cfg)
            finally:
                inst.write(':SOUR:BIAS:STAT OFF')
            if cfg.plotting_enabled:
                input("Press [ENTER] to exit\n")
    finally:
        inst.close()
        rm.close()


def read_config(config_filename):
    """Parse the configuration file and return a named tuple of
    configuration data.
    """
    parser = configparser.ConfigParser()

    ConfigBase = collections.namedtuple('ConfigBase', [
        'ip_address',
        'start_frequency',
        'stop_frequency',
        'number_of_points',
        'segments',
        'measurement_speed',
        'number_of_sweep_averages',
        'number_of_point_averages',
        'oscillator_voltage',
        'bias_voltage',
        'number_of_intervals',
        'interval_period',
        'plotting_enabled'
    ])

    class Configuration(ConfigBase):
        """Named tuple of configuration parameters."""

        def print(self):
            """Print the configuration parameters."""
            print("Acquisition parameters:")
            if self.ip_address is not None:
                print(f"\tIP address: {self.ip_address}")
            if self.start_frequency is not None:
                print(f"\tStart frequency: {self.start_frequency / 1e3:.3e} kHz")
            if self.stop_frequency is not None:
                print(f"\tStop frequency: {self.stop_frequency / 1e3:.3e} kHz")
            if self.number_of_points is not None:
                print(f"\tNumber of points: {self.number_of_points}")
            if self.segments is not None:
                print(f"\tSegments: {self.segments}")
            print(f"\tMeasurement speed: {self.measurement_speed}")
            print(f"\tNumber of sweep averages: {self.number_of_sweep_averages}")
            print(f"\tNumber of point averages: {self.number_of_point_averages}")
            print(f"\tOscillator voltage: {self.oscillator_voltage} Volts")
            print(f"\tBias voltage: {self.bias_voltage} Volts")
            print(f"\tNumber of intervals: {self.number_of_intervals}")
            print(f"\tInterval period: {self.interval_period} seconds")
            print(f"\tPlotting enabled: {self.plotting_enabled}")

    parser.read(config_filename)
    sweep_section = parser['sweep']
    cfg = Configuration(
        parser.get('resource', 'ip_address', fallback=None),
        to_int(sweep_section.getfloat('start_frequency')),
        to_int(sweep_section.getfloat('stop_frequency')),
        sweep_section.getint('number_of_points'),
        sweep_section.get('segments'),
        sweep_section.getint('measurement_speed', fallback=1),
        sweep_section.getint('number_of_sweep_averages', fallback=1),
        sweep_section.getint('number_of_point_averages', fallback=1),
        to_float(sweep_section.getfloat('oscillator_voltage'), 3),
        to_float(sweep_section.getfloat('bias_voltage'), 3),
        sweep_section.getint('number_of_intervals'),
        sweep_section.getfloat('interval_period'),
        parser.getboolean('plotting', 'enabled', fallback=True)
    )
    linear_sweep_params = \
        (cfg.start_frequency, cfg.stop_frequency, cfg.number_of_points)
    if cfg.segments and any(linear_sweep_params):
        raise E4990AError(
            "Configuration contains segmented and linear sweep parameters.\n"
            "Define only segments or "
            "start_frequency/stop_frequency/number_of_points.")
    return cfg


def run_sweep(inst, filename, cfg):
    """Execute the sweep acquisition and save data to a MAT file."""
    print(f"Acquisition program version: {program_version}")
    idn = inst.query('*IDN?').strip()
    print(idn)
    opt = inst.query('*OPT?').strip()
    print('Options installed:', opt)
    cfg.print()

    inst.write('*CLS')
    def print_status(st):
        return "ON" if st else "OFF"

    fixture = inst.query(':SENS:FIXT:SEL?').strip()
    print(f"Fixture: {fixture}")
    print("Fixture compensation status:")
    open_cmp_status = to_int(inst.query(':SENS1:CORR2:OPEN?'))
    print(f"\tOpen fixture compensation: {print_status(open_cmp_status)}")
    short_cmp_status = to_int(inst.query(':SENS1:CORR2:SHOR?'))
    print(f"\tShort fixture compensation: {print_status(short_cmp_status)}")

    query = functools.partial(inst.query_ascii_values, separator=',',
                              container=numpy.array)

    number_of_points = configure_sweep_parameters(inst, cfg)

    x = query(':SENS1:FREQ:DATA?')

    # Check that compensation is valid for the sweep frequency range.
    # Check the frequencies for the open compensation and assume that
    # frequencies for the short compensation are the same.
    fix_cmp_frequencies = query(':SENS1:CORR2:ZME:OPEN:FREQ?')
    fix_cmp_number_of_points = to_int(inst.query(':SENS1:CORR2:ZME:OPEN:POIN?'))
    if number_of_points != fix_cmp_number_of_points or \
            not numpy.array_equal(x, fix_cmp_frequencies):
        raise E4990AError(
            "Fixture compensation data is not valid for the sweep "
            "frequency range")

    def to_complex(a):
        av = a.view().reshape(a.size//2, 2)
        return av.view(dtype=numpy.complex64)

    fixture_cmp_open_impedance = \
        to_complex(query(':SENS1:CORR2:ZME:OPEN:DATA?'))
    fixture_cmp_short_impedance = \
        to_complex(query(':SENS1:CORR2:ZME:SHOR:DATA?'))

    # Set oscillator voltage and bias voltage
    configure_osc_voltage(inst, cfg.oscillator_voltage)
    if cfg.bias_voltage != 0:
        inst.write(':SOUR1:BIAS:MODE VOLT')
        inst.write(f':SOUR1:BIAS:VOLT {cfg.bias_voltage}')
        inst.write(':SOUR:BIAS:STAT ON')

    # Configure DC Bias current and voltage measurement
    if cfg.bias_voltage != 0:
        inst.write(':SENS1:DC:MEAS:ENAB ON')
        bias_current_measurement = numpy.zeros((1, cfg.number_of_intervals),
                                               dtype=numpy.float32)
        bias_voltage_measurement = numpy.zeros((1, cfg.number_of_intervals),
                                               dtype=numpy.float32)
    else:
        inst.write(':SENS1:DC:MEAS:ENAB OFF')
        bias_current_measurement = numpy.empty(0, dtype=numpy.float32)
        bias_voltage_measurement = numpy.empty(0, dtype=numpy.float32)

    # Show marker at peak of trace
    inst.write(':CALC1:MARK1 ON')
    inst.write(':CALC1:MARK1:FUNC:TYPE PEAK')

    ydims = number_of_points, cfg.number_of_intervals
    yx = numpy.zeros(ydims, dtype=numpy.float32)
    yr = numpy.zeros(ydims, dtype=numpy.float32)
    if cfg.plotting_enabled:
        pyy = PlotYY(x)
    start_time = time.time()
    for i in range(0, cfg.number_of_intervals):
        # Clear DC Bias measurement data
        if cfg.bias_voltage != 0:
            inst.write(':SENS1:DC:MEAS:CLE')

        acq_start_time = time.perf_counter()
        inst.write(':TRIG:SING')
        inst.query('*OPC?')
        acq_end_time = (time.perf_counter() - acq_start_time) * 1e3
        print(f"Acquisition time is {acq_end_time:.0f} ms")

        inst.write(':DISP:WIND1:TRAC1:Y:AUTO')
        inst.write(':DISP:WIND1:TRAC2:Y:AUTO')

        # Execute marker search
        inst.write(':CALC1:MARK1:FUNC:EXEC')

        y = query(':CALC1:DATA:RDAT?')
        yx[:,i] = y[::2]
        yr[:,i] = y[1::2]

        # Get DC Bias current and voltage measurement
        if cfg.bias_voltage != 0:
            bias_current_measurement[0,i] = \
                inst.query(':SENS1:DC:MEAS:DATA:DCI?')
            bias_voltage_measurement[0,i] = \
                inst.query(':SENS1:DC:MEAS:DATA:DCV?')

        if cfg.plotting_enabled:
            rlev1 = to_int(inst.query(':DISP:WIND1:TRAC1:Y:RLEV?'))
            rlev2 = to_int(inst.query(':DISP:WIND1:TRAC2:Y:RLEV?'))
            ndiv = to_int(inst.query(':DISP:WIND1:Y:DIV?'))
            pdiv1 = to_int(inst.query(':DISP:WIND1:TRAC1:Y:PDIV?'))
            pdiv2 = to_int(inst.query(':DISP:WIND1:TRAC2:Y:PDIV?'))
            yxlim = rlev1 - ndiv / 2 * pdiv1, rlev1 + ndiv / 2 * pdiv1
            yrlim = rlev2 - ndiv / 2 * pdiv2, rlev2 + ndiv / 2 * pdiv2
            pyy.update(yx[:,i], yr[:,i], yxlim, yrlim)

        if cfg.interval_period != 0:
            sleep_time = \
                cfg.interval_period * (i + 1) - (time.time() - start_time)
            if sleep_time < 0:
                raise E4990AError("The interval_period is too short")
            print(f"Sleeping for {sleep_time:.2f} s")
            time.sleep(sleep_time)

    x.shape = x.shape[0], 1  # Force shape to be N x 1
    if not filename.parent.exists():
        filename.parent.mkdir()
    scio.savemat(filename, {
        'time': time_now,
        'idn': idn,
        'acqProgramVersion': program_version,
        'biasVoltage': cfg.bias_voltage,
        'biasCurrentMeasurement': bias_current_measurement,
        'biasVoltageMeasurement': bias_voltage_measurement,
        'oscillatorVoltage': cfg.oscillator_voltage,
        'measurementSpeed': cfg.measurement_speed,
        'numberOfSweepAverages': cfg.number_of_sweep_averages,
        'numberOfPointAverages': cfg.number_of_point_averages,
        'openCmpStatus': open_cmp_status,
        'shortCmpStatus': short_cmp_status,
        'fixture': fixture,
        'FixtureCmpOpenImpedance': fixture_cmp_open_impedance,
        'FixtureCmpShortImpedance': fixture_cmp_short_impedance,
        'Frequency': x,
        'X': yr,
        'R': yx,
    })
    print(f"Data saved to \"{filename}\"")


def default_filename(now=None):
    """Create ISO8601 timestamp as default filename

    The format is: YYYYMMDDTHHMMSS
    """
    if now is None:
        now = datetime.datetime.now().isoformat()
    return now.replace('-', '').replace(':', '').split('.')[0]


class PlotYY:
    """Plot two time series with separate y-axis."""

    def __init__(self, t):
        self._t = t / 1e3  # Hz -> kHz
        self._fig, self._ax1 = pyplot.subplots()
        self._color1 = 'tab:orange'
        self._ax1.set_xlabel('Frequency [kHz]')
        self._ax1.set_ylabel('R', color=self._color1)
        self._ax1.set_xlim(self._t[0], self._t[-1])
        self._ax1.tick_params(axis='y', labelcolor=self._color1)

        self._ax2 = self._ax1.twinx()  # instantiate a second axes that shares the same x-axis

        self._color2 = 'tab:blue'
        self._ax2.set_ylabel('X', color=self._color2)
        self._ax2.set_xlim(self._t[0], self._t[-1])
        self._ax2.tick_params(axis='y', labelcolor=self._color2)
        self._lines1 = self._lines2 = None

        self._fig.tight_layout()  # otherwise the right y-label is slightly clipped
        pyplot.ion()
        pyplot.show()

    def update(self, y1, y2, y1lim=None, y2lim=None):
        """Refresh the axes with new time series data."""
        if not self._lines1:
            self._lines1 = self._ax1.plot(self._t, y1, color=self._color1)
        else:
            self._lines1[0].set_ydata(y1)
        if not self._lines2:
            self._lines2 = self._ax2.plot(self._t, y2, color=self._color2)
        else:
            self._lines2[0].set_ydata(y2)
        if y1lim:
            self._ax1.set_ylim(y1lim)
        if y2lim:
            self._ax2.set_ylim(y2lim)
        pyplot.draw()
        pyplot.pause(0.001)

def configure_sweep_parameters(inst, cfg):
    """Configure instrument with specified sweep parameters."""
    inst.write(':INIT1:CONT ON')
    inst.write(':TRIG:SOUR BUS')
    inst.write(':CALC1:PAR1:DEF R')
    inst.write(':CALC1:PAR2:DEF X')
    if cfg.segments is not None:
        inst.write(':SENS1:SWE:TYPE SEGM')
        segments = numpy.array(to_int(cfg.segments))
        number_of_segments = segments.size // 3
        segments.shape = number_of_segments, 3
        inst.write(f':SENS1:SEGM:DATA 7,0,0,0,0,0,0,0,'
                   f'{number_of_segments},{cfg.segments}')
        number_of_points = sum(segments[:,2])
        if number_of_points != to_int(inst.query(':SENS1:SEGM:SWE:POIN?')):
            raise E4990AError("Number of points in segments definition does "
                              "not match the number of points to be acquired "
                              "in the segment sweep.")
        inst.write(':DISP:WIND1:X:SPAC LIN')
    else:
        inst.write(':SENS1:SWE:TYPE LIN')
        inst.write(f':SENS1:FREQ:START {cfg.start_frequency}')
        inst.write(f':SENS1:FREQ:STOP {cfg.stop_frequency}')
        inst.write(f':SENS1:SWE:POIN {cfg.number_of_points}')
        number_of_points = cfg.number_of_points

    inst.write(f':SENS1:AVER:COUN {cfg.number_of_point_averages}')
    inst.write(':SENS1:AVER:STAT ON')
    # Measurement speed: [1 5] (1: fastest, 5: most accurate)
    inst.write(f':SENS1:APER:TIME {cfg.measurement_speed}')

    if cfg.number_of_sweep_averages > 1:
        inst.write(':TRIG:SEQ:AVER ON')
        inst.write(':CALC1:AVER ON')
        inst.write(f':CALC1:AVER:COUN {cfg.number_of_sweep_averages}')
    else:
        inst.write(':CALC1:AVER OFF')
    return number_of_points


def configure_osc_voltage(inst, volt):
    """Configure voltage of oscillator."""
    inst.write(':SOUR1:MODE VOLT')
    inst.write(f':SOUR1:VOLT {volt}')


def run_fixture_compensation(inst, cfg):
    """Execute the fixture compensation procedure."""
    inst.write(':SYST:PRES')
    configure_sweep_parameters(inst, cfg)
    inst.write(':SENS1:CORR:COLL:FPO USER')
    # Per manual (https://bit.ly/2Llu3lW), oscillator voltage should be
    # 500 mV during short correction.
    configure_osc_voltage(inst, 0.5)
    print("Starting fixture compensation procedure")
    input("Put the test fixture's device contacts in the OPEN state "
          "and press [ENTER]")
    inst.write(':SENS1:CORR2:COLL:ACQ:OPEN')
    inst.query('*OPC?')
    input("Put the test fixture's device contacts in the SHORT state "
          "and press [ENTER]")
    inst.write(':SENS1:CORR2:COLL:ACQ:SHOR')
    inst.query('*OPC?')


def get_program_version():
    """Get the program version metadata from Git."""
    if pathlib.Path('.git').is_dir():
        r = subprocess.run('git describe --tags --always',
                           stdout=subprocess.PIPE, check=True, shell=True)
        tag_or_hash = r.stdout.strip().decode()
        r = subprocess.run('git diff --stat',
                           stdout=subprocess.PIPE, check=True, shell=True)
        is_dirty = r.stdout.strip().decode() != ''
        return tag_or_hash + ' (dirty)' if is_dirty else ''
    return __version__


class _ConfigFilenameAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        config_filename = values
        if not pathlib.Path(config_filename).exists():
            raise argparse.ArgumentError(
                self, f"Config file '{config_filename}' not found")
        setattr(namespace, self.dest, config_filename)


def parse_args():
    """Parse command line arguments."""
    default = default_filename(time_now)
    parser = argparse.ArgumentParser(
        description="Keysight E4990A acquisition script")
    parser.add_argument('filename', nargs='?')
    parser.add_argument('--config', default=CONFIG_FILENAME_DEFAULT,
                        dest='config_filename',
                        action=_ConfigFilenameAction,
                        help="INI config filename "
                             f"(default: {CONFIG_FILENAME_DEFAULT})")
    parser.add_argument('-a', '--append-datetime', action='store_true',
                        dest='append_datetime',
                        help="Append ISO 8601 datetime to filename")
    parser.add_argument('-d', '--default-filename', action='store_true',
                        dest='use_default_filename',
                        help="Use default filename (ISO 8601 datetime)")
    parser.add_argument('--debug', action='store_true',
                        help="Print tracebacks for debugging")
    parser.add_argument('-c', '--fixture-compensation', action='store_true',
                        help="Execute fixture compensation procedure")
    args = parser.parse_args()
    # Create default INI file if it doesn't exist
    if args.config_filename == CONFIG_FILENAME_DEFAULT and \
            not pathlib.Path(args.config_filename).exists():
        print(f"Default config file \"{CONFIG_FILENAME_DEFAULT}\" doesn't "
              "exist. Creating it from template and exiting.")
        template_ini = resource_path('template.ini')
        shutil.copyfile(template_ini, 'e4990a.ini')
        sys.exit(0)
    filename = None
    if not args.fixture_compensation:
        if args.filename:
            filename = args.filename
        elif args.use_default_filename:
            filename = default
        else:
            filename = input(f"Enter a filepath or press [ENTER] to accept "
                             f"the default ({default}.mat):") or default
        if args.append_datetime and not args.use_default_filename:
            # Remove extension, it will get added back.
            if filename.endswith(FILE_EXT):
                filename = filename.rsplit(FILE_EXT)[0]
            filename += ('-' + default)
        if not filename.endswith(FILE_EXT):
            filename += FILE_EXT
        filename = pathlib.Path(filename)
        if filename.exists():
            resp = input(f"File {filename} exists. Are you sure you want "
                         f"to overwrite it (y/n)?")
            if resp.lower() != 'y':
                sys.exit(0)
    return filename, args


def main():
    """Parse command line arguments, execute the acquisition and
    handle errors.
    """
    filename, args = parse_args()
    try:
        acquire(filename, args.config_filename, args.fixture_compensation)
    except Exception as e:  #pylint: disable=W0703
        if args.debug:
            traceback.print_exc()
        else:
            print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Initialize variables that have global scope.
    time_now = datetime.datetime.now().isoformat()
    program_version = get_program_version()
    main()

#!/usr/bin/env python3
"""Acquisition script for Keysight E4990A."""

import argparse
import collections
import configparser
import datetime
import functools
import numbers
import os
import subprocess
import sys
import time

import matplotlib.pyplot as pyplot
import numpy
import pyvisa
import scipy.io as scio
import visa

fileext = '.mat'
program_version = None
time_now = None


class E4990AError(Exception):
    pass


def to_int(s):
    if s is None:
        return s
    elif isinstance(s, numbers.Number):
        return int(float(s))
    elif ',' in s:  # comma-separated values
        return [int(float(f)) for f in s.strip().split(',')]
    else:
        return int(float(s.strip()))


def main(filename, config_filename):
    cfg = read_config(config_filename)
    rm = visa.ResourceManager()
    print(rm.visalib)
    resources = rm.list_resources('USB?*INSTR')
    if not resources:
        raise E4990AError("No USB instruments found")
    if len(resources) > 1:
        msg = "Multiple USB instruments found:\n"
        for r in resources:
            msg += ('\t' + r)
        raise E4990AError(msg)

    try:
        inst = rm.open_resource(resources[0])
    except pyvisa.errors.VisaIOError as e:
        raise E4990AError(f"{e}")
    try:
        acquire(inst, filename, cfg)
    finally:
        inst.write(':SOUR:BIAS:STAT OFF')
        inst.close()
        rm.close()

    input("Press [ENTER] to exit\n")


def read_config(config_filename):
    parser = configparser.ConfigParser()

    Config = collections.namedtuple('Configuration', [
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

    parser.read(config_filename)
    sweep_section = parser['sweep']
    cfg = Config(
        to_int(sweep_section.getfloat('start_frequency')),
        to_int(sweep_section.getfloat('stop_frequency')),
        sweep_section.getint('number_of_points'),
        sweep_section.get('segments'),
        sweep_section.getint('measurement_speed', fallback=1),
        sweep_section.getint('number_of_sweep_averages', fallback=1),
        sweep_section.getint('number_of_point_averages', fallback=1),
        sweep_section.getfloat('oscillator_voltage'),
        sweep_section.getint('bias_voltage'),
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


def acquire(inst, filename, cfg):
    print(f"Acquisition program version: {program_version}")
    idn = inst.query('*IDN?').strip()
    print(idn)

    print("Acquisition parameters:")
    if cfg.start_frequency is not None:
        print(f"\tStart frequency: {cfg.start_frequency / 1e3:.3e} kHz")
    if cfg.stop_frequency is not None:
        print(f"\tStop frequency: {cfg.stop_frequency / 1e3:.3e} kHz")
    if cfg.number_of_points is not None:
        print(f"\tNumber of points: {cfg.number_of_points}")
    if cfg.segments is not None:
        print(f"\tSegments: {cfg.segments}")
    print(f"\tMeasurement speed: {cfg.measurement_speed}")
    print(f"\tNumber of sweep averages: {cfg.number_of_sweep_averages}")
    print(f"\tNumber of point averages: {cfg.number_of_point_averages}")
    print(f"\tOscillator voltage: {cfg.oscillator_voltage} Volts")
    print(f"\tBias voltage: {cfg.bias_voltage} Volts")
    print(f"\tNumber of intervals: {cfg.number_of_intervals}")
    print(f"\tInterval period: {cfg.interval_period} seconds")

    #inst.write('*RST')
    inst.write('*CLS')
    #inst.write(':SENS1:CORR1:STAT ON')
    #inst.write(':SENS1:CORR2:OPEN ON')
    #inst.write(':SENS1:CORR2:SHOR ON')
    #inst.write(':SENS1:CORR2:LOAD ON')
    def print_status(st):
        return "ON" if st else "OFF"

    fixture = inst.query(':SENS:FIXT:SEL?').strip()
    print(f"Fixture: {fixture}")
    print("Calibration status:")
    user_cal_status = to_int(inst.query(':SENS1:CORR1:STAT?'))
    print(f"\tUser calibration: {print_status(user_cal_status)}")
    open_cmp_status = to_int(inst.query(':SENS1:CORR2:OPEN?'))
    print(f"\tOpen fixture compensation: {print_status(open_cmp_status)}")
    short_cmp_status = to_int(inst.query(':SENS1:CORR2:SHOR?'))
    print(f"\tShort fixture compensation: {print_status(short_cmp_status)}")
    load_cmp_status = to_int(inst.query(':SENS1:CORR2:LOAD?'))
    print(f"\tLoad fixture compensation: {print_status(load_cmp_status)}")

    inst.write(':CALC1:PAR1:DEF R')
    inst.write(':CALC1:PAR2:DEF X')
    inst.timeout = 15000
    if cfg.segments is not None:
        inst.write(':SENS1:SWE:TYPE SEGM')
        segments = numpy.array(to_int(cfg.segments))
        number_of_segments = segments.size // 3
        segments.shape = number_of_segments, 3
        inst.write(f':SENS1:SEGM:DATA 7,0,0,0,0,0,0,0,'
                   f'{number_of_segments},{cfg.segments}')
        number_of_points = sum(segments[:,2])
        if number_of_points != to_int(inst.query(':SENS1:SEGM:SWE:POIN?')):
                raise E4990AError(
                        "Number of points in segments definition does "
                        "not match the number of points to be acquired in the "
                        "segment sweep.")
    else:
        inst.write(':SENS1:SWE:TYPE LIN')
        inst.write(f':SENS1:FREQ:START {cfg.start_frequency}')
        inst.write(f':SENS1:FREQ:STOP {cfg.stop_frequency}')
        inst.write(f':SENS1:SWE:POIN {cfg.number_of_points}')
        number_of_points = cfg.number_of_points

    inst.write(f':SENS1:AVER:COUN {cfg.number_of_point_averages}')
    inst.write(f':SENS1:AVER:STAT ON')
    # Measurement speed: [1 5] (1: fastest, 5: most accurate)
    inst.write(f':SENS1:APER:TIME {cfg.measurement_speed}')

    if cfg.number_of_sweep_averages > 1:
        inst.write(':TRIG:SEQ:AVER ON')
        inst.write(':CALC1:AVER ON')
        inst.write(f':CALC1:AVER:COUN {cfg.number_of_sweep_averages}')
    else:
        inst.write(':CALC1:AVER OFF')

    inst.write(':SOUR1:MODE VOLT')
    inst.write(f':SOUR1:VOLT {cfg.oscillator_voltage}')
    inst.write(':SOUR1:BIAS:MODE VOLT')
    inst.write(f':SOUR1:BIAS:VOLT {cfg.bias_voltage}')
    inst.write(':SOUR:BIAS:STAT ON')

    inst.write(':INIT1:CONT ON')
    inst.write(':TRIG:SOUR BUS')

    ydims = number_of_points, cfg.number_of_intervals
    yx = numpy.zeros(ydims, dtype=numpy.float32)
    yr = numpy.zeros(ydims, dtype=numpy.float32)
    query = functools.partial(inst.query_ascii_values, separator=',',
                              container=numpy.array)
    x = query(':SENS1:FREQ:DATA?')
    if cfg.plotting_enabled:
        pyy = PlotYY(x)
    start_time = time.time()
    for i in range(0, cfg.number_of_intervals):
#        inst.write(':DISP:WIND1:TRAC1:STAT OFF')
#        inst.write(':DISP:WIND1:TRAC2:STAT OFF')
        acq_start_time = time.time()
        inst.write(':TRIG:SING')
        inst.query('*OPC?')
        acq_end_time = time.time() - acq_start_time
        print(f"Acquisition time is {acq_end_time:.2f} s")

#        inst.write(':DISP:WIND1:TRAC1:STAT ON')
#        inst.write(':DISP:WIND1:TRAC2:STAT ON')
        inst.write(':DISP:WIND1:TRAC1:Y:AUTO')
        inst.write(':DISP:WIND1:TRAC2:Y:AUTO')

        y = query(':CALC1:DATA:RDAT?')
        yx[:,i] = y[::2]
        yr[:,i] = y[1::2]

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
    scio.savemat(filename, {
        'time': time_now,
        'idn': idn,
        'acqProgramVersion': program_version,
        'biasVoltage': cfg.bias_voltage,
        'oscillatorVoltage': cfg.oscillator_voltage,
        'measurementSpeed': cfg.measurement_speed,
        'numberOfSweepAverages': cfg.number_of_sweep_averages,
        'numberOfPointAverages': cfg.number_of_point_averages,
        'userCalStatus': user_cal_status,
        'openCmpStatus': open_cmp_status,
        'shortCmpStatus': short_cmp_status,
        'loadCmpStatus': load_cmp_status,
        'fixture': fixture,
        'Frequency': x,
        'X': yr,
        'R': yx,
    })
    print(f"Data saved to {filename}")


def default_filename(now=None):
    """Create ISO8601 timestamp as default filename

    The format is: YYYYMMDDTHHMMSS
    """
    if now is None:
        now = datetime.datetime.now().isoformat()
    return now.replace('-', '').replace(':', '').split('.')[0]


class PlotYY:

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


def get_program_version():
    r = subprocess.run('git describe --tags --always',
                       stdout=subprocess.PIPE, shell=True)
    return r.stdout.strip().decode()


class _ConfigFilenameAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        config_filename = values
        if not os.path.exists(config_filename):
            raise argparse.ArgumentError(self,
                f"Config file '{config_filename}' not found")
        setattr(namespace, self.dest, config_filename)


def parse_args():
    default = default_filename(time_now)
    parser = argparse.ArgumentParser(
        description="Keysight E4990A acquisition script")
    parser.add_argument('filename', nargs='?')
    parser.add_argument('--config', default='e4990a.ini',
                        dest='config_filename',
                        action=_ConfigFilenameAction,
                        help="INI config filename (default: e4990.ini)")
    parser.add_argument('-d', '--default-filename', action='store_true',
                        dest='use_default_filename',
                        help="Use default filename for saving data")
    args = parser.parse_args()
    if args.filename:
        filename = args.filename
    elif args.use_default_filename:
        filename = default
    else:
        filename = input(f"Enter a filepath or press [ENTER] to accept the "
                         f"default ({default}.mat):") or default
    if not filename.endswith(fileext):
        filename += fileext
    if os.path.exists(filename):
        resp = input(f"File {filename} exists. Are you sure you want "
                     f"to overwrite it (y/n)?")
        if resp.lower() != 'y':
            sys.exit(0)
    return filename, args.config_filename


if __name__ == '__main__':
    time_now = datetime.datetime.now().isoformat()
    program_version = get_program_version()
    try:
        sys.exit(main(*parse_args()))
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

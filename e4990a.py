#!/usr/bin/env python3

import argparse
import configparser
import datetime
import functools
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


def to_int(s):
    return int(float(s.strip()))


def main(filename, config_filename):
    rm = visa.ResourceManager()
    resources = rm.list_resources('USB?*INSTR')
    if not resources:
        print("No USB instruments found")
        return 1
    elif len(resources) > 1:
        print("Multiple USB instruments found:")
        for r in resources:
            print('\t' + r)
        return 1

    try:
        inst = rm.open_resource(resources[0])
    except pyvisa.errors.VisaIOError as e:
        print(f"\n{e}")
        return 1
    inst.timeout = 15000
    try:
        rc = acquire(inst, config_filename)
    finally:
        inst.write(':SOUR:BIAS:STAT OFF')
        inst.close()
        rm.close()

    if rc == 0:
        input("Press [ENTER] to exit\n")
    return rc


def acquire(inst, config_filename):
    print(f"Acquisition program version: {program_version}")
    idn = inst.query(r'*IDN?').strip()
    print(idn)

    parser = configparser.ConfigParser()
    if not os.path.exists(config_filename):
        print(f"Config file '{config_filename}' not found")
        return 1
    parser.read(config_filename)
    sweep_section = parser['sweep']
    start_frequency = int(sweep_section.getfloat('start_frequency'))
    stop_frequency = int(sweep_section.getfloat('stop_frequency'))
    number_of_points = sweep_section.getint('number_of_points')
    measurement_speed = sweep_section.getint('measurement_speed', fallback=1)
    number_of_sweep_averages = \
        sweep_section.getint('number_of_sweep_averages', fallback=1)
    number_of_point_averages = \
        sweep_section.getint('number_of_point_averages', fallback=1)
    oscillator_voltage = sweep_section.getfloat('oscillator_voltage')
    bias_voltage = sweep_section.getint('bias_voltage')
    number_of_intervals = sweep_section.getint('number_of_intervals')
    interval_period = sweep_section.getfloat('interval_period')
    plotting_enabled = parser.getboolean('plotting', 'enabled', fallback=True)

    print("Acquisition parameters:")
    print(f"\tStart frequency: {start_frequency / 1e3:.3e} kHz")
    print(f"\tStop frequency: {stop_frequency / 1e3:.3e} kHz")
    print(f"\tNumber of points: {number_of_points}")
    print(f"\tMeasurement speed: {measurement_speed}")
    print(f"\tNumber of sweep averages: {number_of_sweep_averages}")
    print(f"\tNumber of point averages: {number_of_point_averages}")
    print(f"\tOscillator voltage: {oscillator_voltage} Volts")
    print(f"\tBias voltage: {bias_voltage} Volts")
    print(f"\tNumber of intervals: {number_of_intervals}")
    print(f"\tInterval period: {interval_period} seconds")

    #inst.write('*RST')
    inst.write('*CLS')
    #inst.write(':SENS1:CORR1:STAT ON')
    #inst.write(':SENS1:CORR2:OPEN ON')
    #inst.write(':SENS1:CORR2:SHOR ON')
    #inst.write(':SENS1:CORR2:LOAD ON')
    def print_status(st):
        return "ON" if st else "OFF" 

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
    inst.write(':SENS1:SWE:TYPE LIN')
    inst.write(f':SENS1:SWE:POIN {number_of_points}')
    inst.write(f':SENS1:FREQ:START {start_frequency}')
    inst.write(f':SENS1:FREQ:STOP {stop_frequency}')
    inst.write(f':SENS1:AVER:COUN {number_of_point_averages}')
    inst.write(f':SENS1:AVER:STAT ON')
    # Measurement speed: [1 5] (1: fastest, 5: most accurate)
    inst.write(f':SENS1:APER:TIME {measurement_speed}')

    if number_of_sweep_averages > 1:
        inst.write(':TRIG:SEQ:AVER ON')
        inst.write(':CALC1:AVER ON')
        inst.write(f':CALC1:AVER:COUN {number_of_sweep_averages}')
    else:
        inst.write(':CALC1:AVER OFF')

    inst.write(':SOUR1:MODE VOLT')
    inst.write(f':SOUR1:VOLT {oscillator_voltage}')
    inst.write(':SOUR1:BIAS:MODE VOLT')
    inst.write(f':SOUR1:BIAS:VOLT {bias_voltage}')
    inst.write(':SOUR:BIAS:STAT ON')

    inst.write(':INIT1:CONT ON')
    inst.write(':TRIG:SOUR BUS')

    ydims = number_of_points, number_of_intervals
    yx = numpy.zeros(ydims, dtype=numpy.float32)
    yr = numpy.zeros(ydims, dtype=numpy.float32)
    if plotting_enabled:
        query = functools.partial(inst.query_ascii_values, separator=',',
                                container=numpy.ndarray)
        x = query(':SENS1:FREQ:DATA?')
        pyy = PlotYY(x)
    start_time = time.time()
    for i in range(0, number_of_intervals):
        inst.write('*CLS')
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

        if plotting_enabled:
            rlev1 = to_int(inst.query(':DISP:WIND1:TRAC1:Y:RLEV?'))
            rlev2 = to_int(inst.query(':DISP:WIND1:TRAC2:Y:RLEV?'))
            ndiv = to_int(inst.query(':DISP:WIND1:Y:DIV?'))
            pdiv1 = to_int(inst.query(':DISP:WIND1:TRAC1:Y:PDIV?'))
            pdiv2 = to_int(inst.query(':DISP:WIND1:TRAC2:Y:PDIV?'))
            yxlim = rlev1 - ndiv / 2 * pdiv1, rlev1 + ndiv / 2 * pdiv1
            yrlim = rlev2 - ndiv / 2 * pdiv2, rlev2 + ndiv / 2 * pdiv2
            y = query(':CALC1:DATA:RDAT?')
            yx[:,i] = y[::2]
            yr[:,i] = y[1::2]
            pyy.update(yx[:,i], yr[:,i], yxlim, yrlim)

        if interval_period != 0:
            sleep_time = interval_period * (i + 1) - (time.time() - start_time)
            if sleep_time < 0:
                print("The interval_period is too short")
                return 1
            print(f"Sleeping for {sleep_time:.2f} s")
            time.sleep(sleep_time)

    scio.savemat(filename, {
        'time': datetime.datetime.now().isoformat(),
        'idn': idn,
        'acqProgramVersion': program_version,
        'biasVoltage': bias_voltage,
        'oscillatorVoltage': oscillator_voltage,
        'measurementSpeed': measurement_speed,
        'numberOfSweepAverages': number_of_sweep_averages,
        'numberOfPointAverages': number_of_point_averages,
        'userCalStatus': user_cal_status,
        'openCmpStatus': open_cmp_status,
        'shortCmpStatus': short_cmp_status,
        'loadCmpStatus': load_cmp_status,
        'Frequency': (start_frequency, stop_frequency),
        'X': yr,
        'R': yx,
    })
    print(f"Data saved to {filename}")


def default_filename():
    """Create ISO8601 timestamp as default filename

    The format is: YYYYMMDDTHHMMSS
    """
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


if __name__ == '__main__':
    r = subprocess.run('git describe --tags --always',
                       stdout=subprocess.PIPE)
    program_version = r.stdout.strip().decode()
    default = default_filename()
    parser = argparse.ArgumentParser(
        description="Keysight E4990A acquisition script")
    parser.add_argument('filename', nargs='?')
    parser.add_argument('--config', default='e4990a.ini',
                        dest='config_filename',
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
    main(filename, args.config_filename)

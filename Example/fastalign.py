#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This example shows how to define and run area and gradient scan routines."""

from time import sleep

from pipython import GCSDevice

CONTROLLERNAME = 'E-712'

AREASCAN = 1  # name of area scan routine
GRADIENTSCAN = 3  # name of gradient scan routine

RESULTIDS = {
    1: 'successful bit',
    2: 'signal level at maximum',
    3: 'position of maximum signal'
}


def main():
    """Connect controller and start scans."""
    with GCSDevice(CONTROLLERNAME) as pidevice:
#         pidevice.ConnectRS232(comport=1, baudrate=115200)
        pidevice.ConnectUSB(serialnum='107024343')
        # pidevice.ConnectTCPIP(ipaddress='192.168.178.42')
        print('connected: {}'.format(pidevice.qIDN().strip()))
        runscan(pidevice)


def runscan(pidevice):
    """Define gradient and area scan routines and start them.
    @type pidevice : pipython.gcscommands.GCSCommands
    """
    # warning: given values of this sample can damage your system
    # adjust all values accordingly and remove the following line
    raise UserWarning('adjust FDG values to match your configuration')
    print('define gradient scan routine...')
    pidevice.FDG(routinename=GRADIENTSCAN,
                 scanaxis=1,
                 stepaxis=2,
                 minlevel=0.01,
                 aligninputchannel=1,
                 minampl=1.0,
                 maxampl=4.0,
                 frequency=23.0,
                 speedfactor=20.0,
                 maxvelocity=20.0,
                 maxdirectionchanges=100,
                 speedoffset=0.05)
    # warning: given values of this sample can damage your system
    # adjust all values accordingly and remove the following line
    raise UserWarning('adjust FDR values to match your configuration')
    print('define area scan routine...')
    pidevice.FDR(routinename=AREASCAN,
                 scanaxis=1,
                 scanrange=100.0,
                 stepaxis=2,
                 steprange=100.0,
                 threshold=0,
                 aligninputchannel=1,
                 frequency=20.0,
                 velocity=50.0,
                 scanmiddlepos=50.0,
                 stepmiddlepos=50.0,
                 targettype=1,
                 estimationmethod=0,
                 mininput=80.0,
                 maxinput=20.0,
                 stopoption=0)
    start_and_wait_for_scan(pidevice, routinename=AREASCAN)
    start_and_wait_for_scan(pidevice, routinename=GRADIENTSCAN)
    print('done')


def start_and_wait_for_scan(pidevice, routinename):
    """Start scan 'routinename', wait for finish and show its results.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param routinename : Name of the fast alignment routine.
    """
    print('start scan routine {}...'.format(routinename))
    pidevice.FRS(routinename)
    print('wait for scan routine {} to finish...'.format(routinename))
    while pidevice.qFRP(routinename)[routinename]:
        sleep(0.1)
    print('results for scan routine {}:'.format(routinename))
    result = pidevice.qFRR(name=[routinename] * len(RESULTIDS), resultid=RESULTIDS.keys())[routinename]
    for resultid in RESULTIDS:
        print('{} (ID {}): {}'.format(RESULTIDS[resultid], resultid, result[resultid]))


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    main()

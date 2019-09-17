# -*- coding: utf-8 -*-
'''
Created on 17.09.2019

@author: yu03
'''
from pipython import GCSDevice, datarectools, pitools, gcscommands
import numpy as np
import matplotlib.pyplot as plt
import time

CONTROLLERNAME = 'E-712'
STAGES = None  # connect stages to axes
REFMODE = None  # reference the connected stages

NUMPOINTS = 30000  # number of points for one sine period as integer
STARTPOS = 0.0  # start position of the circular motion as float for both axes
AMPLITUDE = 10  # amplitude of the circular motion as float for both axes
NUMCYLES = 5  # number of cycles for wave generator output
TABLERATE = 1  # duration of a wave table point in multiples of servo cycle times as integer

wavegens = (1, 2)
wavetables = (1, 2)

with GCSDevice(CONTROLLERNAME) as pidevice:
    
    '''
        Initialization
    '''
    pidevice.InterfaceSetupDlg()
#     print('connected: {}'.format(pidevice.qIDN().strip()))
#     print('initialize connected stages...')
    pitools.startup(pidevice, STAGES, REFMODE)
    IDN = pidevice.qIDN()
    print('IDN: ', IDN)
#     pidevice.WGO(wavegens, mode=[0]*len(wavegens))

    '''
        Auto-Zero (not use)
    '''
#     pidevice.ATZ({1:0, 2:0, 4:0})
#     time.sleep(5)
    
    '''
        Turn on control loop
    '''
    pidevice.SVO({'1':1,'2':1,'3':1,'4':1,'5':1,'6':1})
    print('Servo Status: ', pidevice.qSVO())
    
    '''
        Set Target Relative To Current Position
    '''
#     for i in range(3):
#         pidevice.MVR('2', 0.1) ### y = 2
#         time.sleep(1)
    
    '''
        Wave Generator & Trigger Configuration
    '''
    pidevice.WAV_SIN_P(table=wavetables[1], firstpoint=1, numpoints=NUMPOINTS, append='X',
                       center=NUMPOINTS/2, amplitude=AMPLITUDE, offset=STARTPOS, seglength=NUMPOINTS)    
#     pidevice.WAV_LIN(table=wavetables[1], firstpoint=1, numpoints=NUMPOINTS, append='X',
#                     speedupdown=NUMPOINTS//10, amplitude=AMPLITUDE, offset=0, seglength=NUMPOINTS)
     
    pidevice.WSL(wavegens, wavetables)
    pidevice.WGC(wavegens, [NUMCYLES]*len(wavegens))
    pidevice.WTR(0, tablerates=TABLERATE, interpol=0)
    pitools.waitonready(pidevice)
    pitools.waitontarget(pidevice, '2')
    pidevice.WGO(wavegens[1], mode=[1])
    while any(list(pidevice.IsGeneratorRunning(wavegens[1]).values())):
        print ('.')
        time.sleep(1.0)
    print('done')
    pidevice.WGO(wavegens, mode=[0]*len(wavegens))
    
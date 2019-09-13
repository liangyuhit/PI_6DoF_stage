# -*- coding: utf-8 -*-
'''
Created on 13.09.2019

@author: yu03
'''
from pipython import GCSDevice, datarectools, pitools, gcscommands
import numpy as np
import matplotlib.pyplot as plt
import time
from time import sleep


cpu_time = []
cpu_time.append(time.time())
# CONTROLLERNAME = 'E-712'
STAGES = None  # connect stages to axes
REFMODE = None  # reference the connected stages
NUMVALUES = 1000  # number of data sets to record as integer
RECRATE = 2000  # number of recordings per second, i.e. in Hz


NUMPOINTS = 1000  # number of points for one sine period as integer
STARTPOS = 0.0  # start position of the circular motion as float for both axes
AMPLITUDE = 15  # amplitude of the circular motion as float for both axes
NUMCYLES = 1  # number of cycles for wave generator output
TABLERATE = 1  # duration of a wave table point in multiples of servo cycle times as integer


with GCSDevice('E-712') as pidevice:
    pidevice.InterfaceSetupDlg()
    print('connected: {}'.format(pidevice.qIDN().strip()))
    print('initialize connected stages...')
    pitools.startup(pidevice, STAGES, REFMODE)

    drec = datarectools.Datarecorder(pidevice)
    drec.numvalues = NUMVALUES
    drec.samplefreq = RECRATE
    print('data recorder rate: {:.2f} Hz'.format(drec.samplefreq))
    drec.options = (datarectools.RecordOptions.ACTUAL_POSITION_2)
    drec.sources = ('2', '3', '5') ### 2=y=lenth 3=rot_z=hor_angle, 5=rot_x=ver_angle
#     drec.trigsources = datarectools.TriggerSources.POSITION_CHANGING_COMMAND_1
    drec.trigsources = datarectools.TriggerSources.TRIGGER_IMMEDIATELY_4
    drec.arm()
    
    print(pidevice.qDRT())
    
    
    
    
    wavegens = (1, 2)
    wavetables = (1, 2)
 
    pidevice.WAV_LIN(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
                     speedupdown=100, amplitude=AMPLITUDE, offset=STARTPOS, seglength=NUMPOINTS)
#     pidevice.WAV_SIN_P(table=wavetables[1], firstpoint=NUMPOINTS, numpoints=NUMPOINTS, append='X',
#                        center=NUMPOINTS / 2, amplitude=AMPLITUDE[1], offset=STARTPOS[1], seglength=NUMPOINTS)
    pitools.waitonready(pidevice)
    if pidevice.HasWSL():  # you can remove this code block if your controller does not support WSL()
        print('connect wave generators {} to wave tables {}'.format(wavegens, wavetables))
        pidevice.WSL(wavegens, wavetables)
    if pidevice.HasWGC():  # you can remove this code block if your controller does not support WGC()
        print('set wave generators {} to run for {} cycles'.format(wavegens, NUMCYLES))
        pidevice.WGC(wavegens, [NUMCYLES] * len(wavegens))
#     if pidevice.HasWTR():  # you can remove this code block if your controller does not support WTR()
#         print('set wave table rate to {} for wave generators {}'.format(TABLERATE, wavegens))
#         pidevice.WTR(wavegens, [TABLERATE] * len(wavegens), interpol=[0] * len(wavegens))
#     startpos = (STARTPOS[0], STARTPOS[1] + AMPLITUDE[1] / 2.0)
#     print('move axes {} to their start positions {}'.format(pidevice.axes[:2], startpos))
#     pidevice.MOV(pidevice.axes[:2], startpos)
    pitools.waitontarget(pidevice, '2')
    print('start wave generators {}'.format(wavegens))
    pidevice.WGO(wavegens, mode=[1] * len(wavegens))
    while any(list(pidevice.IsGeneratorRunning(wavegens).values())):
        print ('.')
        sleep(1.0)
    print('done')
     
     
#     pidevice.MVR('2', 0.01) ### y = 2
#     
    header, data = drec.getdata()
  
    y_pos, z_rot, x_rot = data[0], data[1], data[2]
      
    samp_time = int(header['NDATA'])/RECRATE
    n_data = int(header['NDATA'])
    print('Sampling Rate = ', RECRATE)
    print('Data length = ', n_data)
    print('Time = ', samp_time)
      
plt.figure(1)
t = np.linspace(0, samp_time, num=n_data)
plt.subplot(2,1,1)
plt.plot(t, y_pos, color='blue')
plt.subplot(2,1,2)
plt.plot(t, z_rot, color='blue')
plt.plot(t, x_rot, color='red')
plt.show()

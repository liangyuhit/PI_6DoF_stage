# -*- coding: utf-8 -*-
'''
Created on 16.09.2019

@author: yu03
'''
from pipython import GCSDevice, datarectools, pitools, gcscommands
import numpy as np
import matplotlib.pyplot as plt
import time

CONTROLLERNAME = 'E-712'
STAGES = None  # connect stages to axes
REFMODE = None  # reference the connected stages

Wave_length = 30000
NUMVALUES = 3000  # number of data sets to record as integer
RECRATE = 500  # number of recordings per second, i.e. in Hz


with GCSDevice(CONTROLLERNAME) as pidevice:
    
    '''
        Initialization
    '''
    pidevice.InterfaceSetupDlg()
    print('connected: {}'.format(pidevice.qIDN().strip()))
    print('initialize connected stages...')
    pitools.startup(pidevice, STAGES, REFMODE)
    IDN = pidevice.qIDN()
    print('IDN: ', IDN)
    print('Servo Status: ', pidevice.qSVO())
    
    
    '''
        Auto-Zero
    '''
#     pidevice.ATZ({1:0, 2:0, 4:0})
#     time.sleep(5)

    '''
        Data Recording Configuration
    '''
    drec = datarectools.Datarecorder(pidevice)
    drec.numvalues = NUMVALUES
    drec.samplefreq = RECRATE
    print('data recorder rate: {:.2f} Hz'.format(drec.samplefreq))
    drec.options = (datarectools.RecordOptions.ACTUAL_POSITION_2)
    drec.sources = ('2', '3', '5') ### 2=y=lenth 3=rot_z=hor_angle, 5=rot_x=ver_angle
    drec.trigsources = datarectools.TriggerSources.POSITION_CHANGING_COMMAND_1
#     drec.trigsources = 0
    drec.arm()
    
#     print('Data recorder options: ', pidevice.qHDR())
    print('Num. of recorded points: ', pidevice.qDRL())
    
#     pidevice.DRC(tables=1, sources='2', options=2)
#     pidevice.DRC(tables=2, sources='3', options=2)
#     pidevice.DRC(tables=3, sources='5', options=2)
#     print('Data recorder configuration: ', pidevice.qDRC())
# 
# #     pidevice.DRT(tables=1, sources='1', values=1)
#     print('Data recorder TriggerSource: ', pidevice.qDRT())

    '''
        Wave Generator & Trigger Configuration
    '''
    print('Wave Generator Num. ', pidevice.qTWG())
    Servo_update_time = pidevice.qSPA(items=1, params=0x0E000200)[1][234881536]### 0x0E000200
    print('Servo update time: /s', Servo_update_time)
     
    pidevice.WAV_LIN(table=1, firstpoint=1, numpoints=Wave_length, append='X', speedupdown=3, amplitude=10, offset=0, seglength=Wave_length)
#     pidevice.WAV_SIN_P(table=1, firstpoint=1, numpoints=10000, append='X', center=5000, amplitude=10, offset=0, seglength=10000)
    pidevice.TWC()
    for i in range(Wave_length//300+1): ### 1kHz~15; 48Hz~300
        pidevice.TWS(lines=2, points=1+300*i, switches=1)
 
    pidevice.CTO(lines=2, params=1, values=0.1)
#     pidevice.CTO(lines=2, params=2, values=2)
    pidevice.CTO(lines=2, params=3, values=9)
    Trig_conf = pidevice.qCTO()[2] ### Y_axis=2
    Trig_step = Trig_conf[1]
    Trig_line = Trig_conf[2]
    Trig_mode = Trig_conf[3]
#     print(Trig_conf)
    print('Trigger step = ', float(Trig_step))
    print('Trigger line = ', Trig_line)
    print('Trigger mode = ', Trig_mode)
             
    pidevice.WSL(wavegens=1, tables=1)
    pidevice.WGC(wavegens=1, numcycles=2)
    pidevice.MVR('2', 0.1) ### y = 2
    pidevice.WGO(wavegens=1, mode=1)
 
#     time.sleep(10.0)
#     pidevice.WGO(wavegens=1, mode=0)
    
    '''
        Set Target Relative To Current Position
    '''
#     pidevice.MVR('2', 0.1) ### y = 2
    
    '''
        Get Target Position
    '''
#     target_position = pidevice.qMOV() 
#     target_x, target_y, target_z_r, target_z, target_x_r, target_y_r = pidevice.qMOV()['1'],pidevice.qMOV()['2'],pidevice.qMOV()['3'],pidevice.qMOV()['4'],pidevice.qMOV()['5'],pidevice.qMOV()['6']
#     print(target_x, target_y, target_z_r, target_z, target_x_r, target_y_r)
    
    '''
        Get Real Position
    '''
#     pos = pidevice.qPOS()
#     pos_x, pos_y, pos_z_r, pos_z, pos_x_r, pos_y_r = pidevice.qMOV()['1'],pidevice.qMOV()['2'],pidevice.qMOV()['3'],pidevice.qMOV()['4'],pidevice.qMOV()['5'],pidevice.qMOV()['6']
#     print(pos_x, pos_y, pos_z_r, pos_z, pos_x_r, pos_y_r)
    
    
    

    '''
        Data Recording
    '''
    
    header, data = drec.getdata()   
    y_pos, z_rot, x_rot = data[0], data[1], data[2]
        
    samp_time = NUMVALUES/RECRATE
    n_data = NUMVALUES
    print('Sampling Rate = ', RECRATE)
    print('Data length = ', n_data)
    print('Time = ', samp_time)

#     header, data = pidevice.qDRR(tables=[1,2,3], offset=1, numvalues=NUMVALUES)
#     samp_time = int(header['NDATA'])/RECRATE
#     n_data = int(header['NDATA'])
#     y_pos, z_rot, x_rot = data[0], data[1], data[2]
#     print('Sampling Rate = ', RECRATE)
#     print('Data length = ', n_data)
#     print('Time = ', samp_time)
#     print(len(y_pos))
#     print(header)
#     print(data)
    
plt.figure(1)
t = np.linspace(0, samp_time, num=n_data)
plt.subplot(2,1,1)
plt.plot(t, y_pos, color='blue')
plt.subplot(2,1,2)
plt.plot(t, z_rot, color='blue')
plt.plot(t, x_rot, color='red')
plt.show()
     
     
     
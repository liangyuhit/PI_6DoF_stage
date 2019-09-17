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

# Wave_length = 500
NUMVALUES = 700  # number of data sets to record as integer
RECRATE = 50  # number of recordings per second, i.e. in Hz

NUMPOINTS = 3000  # number of points for one sine period as integer
STARTPOS = 0.0  # start position of the circular motion as float for both axes
AMPLITUDE = 10  # amplitude of the circular motion as float for both axes
NUMCYLES = 2  # number of cycles for wave generator output
TABLERATE = 1  # duration of a wave table point in multiples of servo cycle times as integer

wavegens = (1, 2)
wavetables = (1, 2)

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
    pidevice.WGO(wavegens, mode=[0]*len(wavegens))
    '''
        Auto-Zero
    '''
#     pidevice.ATZ({1:0, 2:0, 4:0})
#     time.sleep(5)
    '''
        Turn on control loop
    '''
    pidevice.SVO({'1':1,'2':1,'3':1,'4':1,'5':1,'6':1})
#     print('Servo Status: ', pidevice.qSVO())
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
#     drec.trigsources = datarectools.TriggerSources.TRIGGER_IMMEDIATELY_4
    drec.arm()
    print(pidevice.qDRT())
    print('Sampling Freq. = ', drec.samplefreq)

    '''
        Wave Generator & Trigger Configuration
    '''
#     print('Wave Generator Num. ', pidevice.qTWG())
#     Servo_update_time = pidevice.qSPA(items=1, params=0x0E000200)[1][234881536]### 0x0E000200
#     print('Servo update time: /s', Servo_update_time)
      
#     pidevice.WAV_LIN(table=1, firstpoint=1, numpoints=NUMPOINTS, append='X', speedupdown=NUMPOINTS//10, amplitude=10, offset=0, seglength=NUMPOINTS)
    pidevice.WAV_LIN(table=wavetables[1], firstpoint=0, numpoints=NUMPOINTS, append='X',
                    speedupdown=NUMPOINTS//10, amplitude=AMPLITUDE, offset=0, seglength=NUMPOINTS)
#     pidevice.WAV_SIN_P(table=wavetables[1], firstpoint=1, numpoints=NUMPOINTS, append='X',
#                        center=NUMPOINTS/2, amplitude=AMPLITUDE, offset=STARTPOS, seglength=NUMPOINTS)
    pidevice.WSL(wavegens, wavetables)
    pidevice.WGC(wavegens, [NUMCYLES]*len(wavegens))
    pidevice.WTR(0, tablerates=TABLERATE, interpol=1)
    
    pidevice.TWC()
    for i in range(NUMPOINTS//3+1): ### 1kHz~15; 48Hz~300
        pidevice.TWS(lines=2, points=1+3*i, switches=1)
    
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
     
#     print('Data recorder options: ', pidevice.qHDR())
     
    pidevice.DRC(tables=1, sources='2', options=2)
    pidevice.DRC(tables=2, sources='3', options=2)
    pidevice.DRC(tables=3, sources='5', options=2)
    print('Data recorder configuration: ', pidevice.qDRC())
  
#     pidevice.DRT(tables=1, sources='1', values=1)
#     print('Data recorder TriggerSource: ', pidevice.qDRT())
    pitools.waitonready(pidevice)
    
#     Table_rate = pidevice.qSPA(items=1, params=0x13000109)[1][318767369] ###0x13000109
#     print(Table_rate)
#     print(pidevice.qWTR(wavegens=1))
    pitools.waitontarget(pidevice, '2')
    print('Servo Status: ', pidevice.qSVO())
    pidevice.WGO(wavegens, mode=[1]*len(wavegens))
    while any(list(pidevice.IsGeneratorRunning(1).values())):
        print ('.')
        time.sleep(1.0)
    print('done')
    pidevice.WGO(wavegens, mode=[0]*len(wavegens))

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
    
#     header, data = datarectools.Datarecorder(pidevice).read(offset=1, numvalues=NUMVALUES)
#     print('Num. of recorded points: ', pidevice.qDRL())
#     samp_time = NUMVALUES/RECRATE
#     n_data = NUMVALUES
    
#     print(header)
#     print((data))
# #     y_pos, z_rot, x_rot = data[0], data[1], data[2]
#     y_pos = data[0]
    
#     print('Sampling Rate = ', RECRATE)
#     print('Data length = ', n_data)
#     print('Time = ', samp_time)
#     print(len(y_pos))
    
plt.figure(1)
t = np.linspace(0, samp_time, num=n_data)
plt.subplot(2,1,1)
plt.plot(t, y_pos, color='blue')
plt.subplot(2,1,2)
plt.plot(t, z_rot, color='blue')
plt.plot(t, x_rot, color='red')
plt.show()
     
     
     
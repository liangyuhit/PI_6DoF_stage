# -*- coding: utf-8 -*-
'''
Created on 19.09.2019

@author: yu03
'''

from pipython import GCSDevice, datarectools, pitools, gcscommands
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
from File_name_define import PI_name, name

now = datetime.datetime.now()

def Export_Data(file_name, header, out_str):
    print('Writing Data')
    with open(file_name,'w') as fid: ######################################################################################
        fid.writelines(header)
        fid.writelines(out_str)
    print('Finish Writing')
    return

CONTROLLERNAME = 'E-712'
STAGES = None  # connect stages to axes
REFMODE = None  # reference the connected stages

'''
    Parameters for data recorder
'''
NUMVALUES = 600  # number of data sets to record as integer
# NUMVALUES = 600
RECRATE = 50  # number of recordings per second, i.e. in Hz

'''
    !!!! Moving Axis define
'''
### 1=x,2=y,3=z_rot,4=z,5=x_rot,6=y_rot

moving_axis = 5

wavegens = (1, 2, 3, 4, 5, 6)
wavetables = (1, 2, 3, 4, 5, 6)

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
        Turn on control loop
    '''
    pidevice.SVO({'1':1,'2':1,'3':1,'4':1,'5':1,'6':1})
    
    '''
        Data Recording Configuration
    '''
    drec = datarectools.Datarecorder(pidevice)
    drec.numvalues = NUMVALUES
    drec.samplefreq = RECRATE
    print('data recorder rate: {:.2f} Hz'.format(drec.samplefreq))
    drec.options = (datarectools.RecordOptions.ACTUAL_POSITION_2)
    drec.sources = ('2', '3', '5') ### 2=y=lenth 3=rot_z=hor_angle, 5=rot_x=ver_angle
#     drec.trigsources = datarectools.TriggerSources.POSITION_CHANGING_COMMAND_1
    drec.trigsources = datarectools.TriggerSources.TRIGGER_IMMEDIATELY_4
    drec.arm()
#     time.sleep(0.5)

    if 0:    
        '''        
            Square test
        '''
    #     pidevice.MVR('2', 0.1) ### y = 2
        for num in range(5):
            pidevice.MVR('%s'%moving_axis, 0.1) ### y = 2
            time.sleep(1)
            pidevice.MVR('%s'%moving_axis, -0.1) ### y = 2
            time.sleep(1)
        
        print('finish moving')

    if 1:    
        '''
            Step test
        '''
    #     pidevice.MVR('2', 0.1) ### y = 2
        for num in range(5):
            pidevice.MVR('%s'%moving_axis, 0.1) ### y = 2
            time.sleep(1)
        for num in range(5):
            pidevice.MVR('%s'%moving_axis, -0.1) ### y = 2
            time.sleep(1)
        
            print('finish moving')

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
    
''' 
    保存文件 Exporting TXT
'''
header = ['%s\n' %(name+'_PI'),
      'Local current time : %s\n' %now.strftime("%Y-%m-%d %H:%M:%S"),
      'Fs = %e (Hz)\n' %RECRATE,##########################################################################################################
      'Record time: %e (s)\n' %samp_time,############################################################################################
      'Frame Number = %i\n' %NUMVALUES,############################################################################################
      'Channel_1: Position /um \n',############################################################################################
      'Channel_2: Hor_Angle /urad \n',############################################################################################
      'Channel_3: ver_Angle /urad \n',############################################################################################
      'Channel_4: xxx \n',############################################################################################
      '-------------------------------------------------\n',
      ]
out_str = ['%f, %f, %f\n' %(y_pos[i], z_rot[i], x_rot[i]) for i in range(NUMVALUES)]
    
'''
    Output
'''
Export_Data(PI_name, header, out_str)
print('TXT file saved')

t = np.linspace(0, samp_time, num=n_data)

plt.figure(1)
plt.gcf().set_size_inches(18,9)

plt.subplot(3,1,1)
plt.plot(t, y_pos, color='blue', label='length')
plt.title('Length')
plt.xlabel('Time /s')
plt.ylabel('Position /um')
plt.grid(which='both', axis='both')

plt.subplot(3,1,2)
plt.plot(t, z_rot, color='red', label='Hor_Angle')
plt.grid(which='both', axis='both')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.title('Hor_Angle')

plt.subplot(3,1,3)
plt.plot(t, x_rot, color='black', label='Ver_Angle')
plt.grid(which='both', axis='both')
plt.title('Ver_Angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()

plt.show()
    
    
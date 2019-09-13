# -*- coding: utf-8 -*-
'''
Created on 13.09.2019

@author: yu03
'''
from pipython import GCSDevice

with GCSDevice('E-712') as gcs:
    gcs.InterfaceSetupDlg()
    print('connected: {}'.format(gcs.qIDN().strip()))
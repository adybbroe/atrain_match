#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c14526.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Read all matched data and make some plotting of thresholds
"""

from glob import glob
import os.path
import os
import numpy as np
from scipy import histogram
import re
OFFSET_DIR=os.environ.get('SM_CFG_DIR')
OFFSET_FILE=os.environ.get('SM_THROFFSETS_NAME')         
OFFESET_FILE = os.path.join(OFFSET_DIR,OFFSET_FILE)
isNPP = True
isGAC_v2012 = False
RunWithOutMargins=True
RunEdited= True

if isNPP:
    isACPGv2012=False
    isGAC=False
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20130908_TEST1B_2/Reshaped_Files/npp/1km/"

    SATELLITE='npp'
    if RunEdited:
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_3_removeall_negativtest_correct_some_bugs/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_4_keep_low_quality_snow_abit_more_remove_bad_test_from_night_inv_sheme/Reshaped_Files/npp/1km/"
        
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_2/Reshaped_Files/npp/1km/"
        #ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_and_night_ice_2/Reshaped_Files/npp/1km/"
        ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_and_night_ice_2/Reshaped_Files/npp/1km/"

    
        SATELLITE='npp_cm_edited'

    files = glob(ROOT_DIR + "/????/??/*/*h5")

elif isGAC_v2012:
    isGAC=True
    isACPGv2012=True
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_GAC_2012_el2010/Reshaped_Files/noaa18/5km/"
    files = glob(ROOT_DIR + "/????/??/cea*/*noaa18*h5")
    SATELLITE='avhrr18'
else:
    isGAC=True
    isACPGv2012=False
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_GAC_2014/Reshaped_Files/noaa18/5km/"
    files = glob(ROOT_DIR + "/????/??/cea*/*noaa18*h5")
    SATELLITE='avhrr18_v2014'

print OFFESET_FILE 


  #print "hi", filename
offset_file = open(OFFESET_FILE, 'r')  
re_offset  = re.compile(r"^SM_ACMG_(\w+)[:=]\s*(-*\d+\.*\d*)\D")
OFFSETS={}
for line in offset_file:
    match_offset = re_offset.match(line)
    if match_offset:
        print "read_offset %s=%s"%(match_offset.group(1),match_offset.group(2))
        OFFSETS[match_offset.group(1)] = 1.0*float(match_offset.group(2))



from matchobject_io import (readCaliopAvhrrMatchObj,
                            CalipsoAvhrrTrackObject)
from cloudsat_calipso_avhrr_statistics import (
    get_day_night_twilight_info_pps2014,
    get_land_coast_sea_info_pps2014,
    get_ice_info_pps2014,
    get_day_night_twilight_info_pps2012,    
    get_land_coast_sea_info_pps2012,
    get_ice_info_pps2012,
    get_inversion_info_pps2014,
    get_sunglint_info_pps2014,
    get_mountin_info_pps2014)
caObj = CalipsoAvhrrTrackObject()
for filename in files:
    print os.path.basename(filename)
    caObj = caObj + readCaliopAvhrrMatchObj(filename)

isClear = caObj.calipso.all_arrays['number_of_layers_found'] == 0
isCloudy = caObj.calipso.all_arrays['number_of_layers_found'] >0
isSingleLayerCloud = caObj.calipso.all_arrays['number_of_layers_found'] == 1
SeesThrough = caObj.calipso.all_arrays['lidar_surface_elevation'][0] >-999
isHigh = caObj.calipso.all_arrays['cloud_top_profile'][0] >5.0
if isGAC:
    isOpticallyThin = caObj.calipso.all_arrays['optical_depth'][0]<1.0
    notVeryThinTop = caObj.calipso.all_arrays['optical_depth'][0]>0.2
else:
    isOpticallyThin = caObj.calipso.all_arrays['optical_depth_top_layer5km']<5.0
    notVeryThinTop = caObj.calipso.all_arrays['optical_depth_top_layer5km']>0.2

isCloudyPPS = np.logical_and(caObj.avhrr.all_arrays['cloudtype']>4,
                             caObj.avhrr.all_arrays['cloudtype']<21)
isClearPPS = np.logical_and(caObj.avhrr.all_arrays['cloudtype']>0,
                            caObj.avhrr.all_arrays['cloudtype']<5)
isPPSCloudyOrClear = np.logical_and(caObj.avhrr.all_arrays['cloudtype']>0,
                                    caObj.avhrr.all_arrays['cloudtype']<21)


thr_t11t12 = caObj.avhrr.all_arrays['thr_t11t12']
thr_t11t37 = caObj.avhrr.all_arrays['thr_t11t37']
thr_t37t12 = caObj.avhrr.all_arrays['thr_t37t12']
thr_t11ts = caObj.avhrr.all_arrays['thr_t11ts']
thr_t11ts_inv = caObj.avhrr.all_arrays['thr_t11ts_inv']
thr_t11t12_inv = caObj.avhrr.all_arrays['thr_t11t12_inv']
thr_t37t12_inv = caObj.avhrr.all_arrays['thr_t37t12_inv']
thr_r06 = caObj.avhrr.all_arrays['thr_r06']
surftemp = caObj.avhrr.all_arrays['surftemp']
latitude = caObj.avhrr.all_arrays['latitude']
ciwv = caObj.avhrr.all_arrays['ciwv']
t11 = caObj.avhrr.all_arrays['bt11micron']
t12 = caObj.avhrr.all_arrays['bt12micron']
t37 = caObj.avhrr.all_arrays['bt37micron']
r06 = caObj.avhrr.all_arrays['r06micron']
r09 = caObj.avhrr.all_arrays['r09micron']
r16 = caObj.avhrr.all_arrays['r16micron']
t11text = caObj.avhrr.all_arrays['text_t11']
r06text = caObj.avhrr.all_arrays['text_r06']
sunz = caObj.avhrr.all_arrays['sunz']
t37t12text = caObj.avhrr.all_arrays['text_t37t12']
t37text = caObj.avhrr.all_arrays['text_t37']

cloudtype_conditions = caObj.avhrr.all_arrays['cloudtype_conditions']
cloudtype_status = caObj.avhrr.all_arrays['cloudtype_status']
cloudtype = caObj.avhrr.all_arrays['cloudtype']
cloudtype_qflag = caObj.avhrr.all_arrays['cloudtype_qflag']
if isACPGv2012:
    i_flags = get_day_night_twilight_info_pps2012(cloudtype_qflag)
    (no_qflag, isPPSNight, twilight_flag, isPPSDay, all_dnt_flag) =  i_flags
    lt_flag = get_land_coast_sea_info_pps2012(cloudtype_qflag)
    (no_qflag, land_flag, isPPSSea, coast_flag, all_lsc_flag) = lt_flag
    isPPSIce = get_ice_info_pps2012(cloudtype_qflag)
else:
    i_flags = get_day_night_twilight_info_pps2014(cloudtype_conditions)
    (no_qflag, isPPSNight, isPPSTwilight, isPPSDay, all_dnt_flag) = i_flags
    lt_flag =get_land_coast_sea_info_pps2014(cloudtype_conditions)
    (no_qflag, isPPSLand, isPPSSea, isPPSCoast, all_lsc_flag) = lt_flag 
    isPPSIce = get_ice_info_pps2014(cloudtype_status)
    isPPSInversion = get_inversion_info_pps2014(cloudtype_status)
    isPPSSunglint = get_sunglint_info_pps2014(cloudtype_conditions)
    isPPSMountain = get_mountin_info_pps2014(cloudtype_conditions)


isClear = np.logical_and(isClear,isPPSCloudyOrClear)
isCloudy = np.logical_and(isCloudy,isPPSCloudyOrClear)
isThinCirrus = np.logical_and(isCloudy, np.logical_and(
        np.logical_and(SeesThrough,isHigh),
        np.logical_and(isOpticallyThin, isSingleLayerCloud)))
isThinCirrus = np.logical_and(isThinCirrus, notVeryThinTop)
# nsidc 
# 255 = Coast
# 1-100 = Sea ice concentration %
# 101 = Permamnent ice
# 0 = Ice free
isCalipsoIce = np.logical_and(caObj.calipso.all_arrays['nsidc'] >= 1,
                       caObj.calipso.all_arrays['nsidc'] <= 101)

isPPSSeaNotIce = np.logical_and(isPPSSea,np.equal(isPPSIce,False))
isSea = np.equal(caObj.calipso.all_arrays['igbp'], 17)
isSea = isSea#np.logical_and(isSea,isPPSSea)
isWater = np.logical_and(isPPSSea, isPPSSeaNotIce)
#isIce = np.logical_and(isCalipsoIce, isPPSIce)
isIce = np.logical_and(isPPSSea, isPPSIce)
isSunglintDay = np.logical_and(np.logical_and(isPPSDay, isPPSSunglint), isPPSSea)
isSunglintTwilight = np.logical_and(np.logical_and(isPPSTwilight, isPPSSunglint), isPPSSea)
isWaterNight = np.logical_and(isWater,isPPSNight)
isWaterDay = np.logical_and(np.logical_and(isWater,isPPSDay),np.equal(isSunglintDay,False))
isWaterTwilight = np.logical_and(np.logical_and(isWater,isPPSTwilight),np.equal(isSunglintTwilight,False))
isIceNight = np.logical_and(isIce,isPPSNight)
isIceDay = np.logical_and(isIce,isPPSDay)
isIceTwilight = np.logical_and(isIce,isPPSTwilight)
isLandNight = np.logical_and(np.logical_and(isPPSLand,isPPSNight),
                             np.logical_and(np.equal(isPPSInversion,False),
                                            np.equal(isPPSMountain,False)))
isLandNightMount = np.logical_and(np.logical_or(isPPSLand,isPPSCoast),
                                  np.logical_and(isPPSNight, isPPSMountain))
isLandNightInv = np.logical_and(np.logical_and(isPPSLand,isPPSNight),
                                  np.logical_and(isPPSInversion, np.equal(isPPSMountain,False)))
isCoastNightInv = np.logical_and(np.logical_and(isPPSCoast,isPPSNight),
                                  np.logical_and(isPPSInversion, np.equal(isPPSMountain,False)))
isCoastNight = np.logical_and(np.logical_and(isPPSCoast,isPPSNight),
                                  np.logical_and(np.equal(isPPSInversion,False), 
                                                 np.equal(isPPSMountain,False)))

isLandDayMount = np.logical_and(np.logical_and(isPPSLand,isPPSDay),
                                isPPSMountain)
isLandDay = np.logical_and(np.logical_and(isPPSLand,isPPSDay),
                                np.equal(isPPSMountain,False))
isCoastDayMount = np.logical_and(np.logical_and(isPPSCoast,isPPSDay),
                                isPPSMountain)
isCoastDay = np.logical_and(np.logical_and(isPPSCoast,isPPSDay),
                                np.equal(isPPSMountain,False))

isLandTwilight = np.logical_and(np.logical_and(isPPSLand,isPPSTwilight),
                             np.logical_and(np.equal(isPPSInversion,False),
                                            np.equal(isPPSMountain,False)))
isLandTwilightMount = np.logical_and(np.logical_or(isPPSLand,isPPSCoast),
                                  np.logical_and(isPPSTwilight, isPPSMountain))
isLandTwilightInv = np.logical_and(np.logical_and(isPPSLand,isPPSTwilight),
                                  np.logical_and(isPPSInversion, np.equal(isPPSMountain,False)))
isCoastTwilightInv = np.logical_and(np.logical_and(isPPSCoast,isPPSTwilight),
                                  np.logical_and(isPPSInversion, np.equal(isPPSMountain,False)))
isCoastTwilight = np.logical_and(np.logical_and(isPPSCoast,isPPSTwilight),
                                  np.logical_and(np.equal(isPPSInversion,False), 
                                                 np.equal(isPPSMountain,False)))
#isWater =  isPPSSeaNotIce
#isIce =  np.logical_and(isPPSSea,isPPSIce)

isClearIce = np.logical_and(isIce, isClear)

isClearIceNight = np.logical_and(isClear, isIceNight)
isCloudyIceNight = np.logical_and(isCloudy, isIceNight)
isCloudyCirrusIceNight = np.logical_and(isThinCirrus, isIceNight)
isClearWaterNight = np.logical_and(isClear, isWaterNight)
isCloudyWaterNight = np.logical_and(isCloudy, isWaterNight)
isCloudyCirrusWaterNight = np.logical_and(isThinCirrus, isWaterNight)
isClearLandNight =   np.logical_and(isClear, isLandNight)
isCloudyLandNight =  np.logical_and(isCloudy, isLandNight)
isClearLandNightMount =  np.logical_and(isClear, isLandNightMount)
isCloudyLandNightMount =  np.logical_and(isCloudy, isLandNightMount)
isClearLandNightInv =  np.logical_and(isClear,isLandNightInv) 
isCloudyLandNightInv = np.logical_and(isCloudy, isLandNightInv)
isClearCoastNightInv =  np.logical_and(isClear,isCoastNightInv) 
isCloudyCoastNightInv = np.logical_and(isCloudy, isCoastNightInv)
isClearCoastNight =  np.logical_and(isClear,isCoastNight) 
isCloudyCoastNight = np.logical_and(isCloudy, isCoastNight)
isClearIceDay = np.logical_and(isClear, isIceDay)
isCloudyIceDay = np.logical_and(isCloudy, isIceDay)
isClearSunglintDay = np.logical_and(isClear, isSunglintDay)
isCloudySunglintDay = np.logical_and(isCloudy, isSunglintDay)
isClearWaterDay = np.logical_and(isClear, isWaterDay)
isCloudyWaterDay = np.logical_and(isCloudy, isWaterDay)
isCloudyCirrusWaterDay = np.logical_and(isThinCirrus, isWaterDay)
isClearLandDay = np.logical_and(isClear, isLandDay)
isCloudyLandDay = np.logical_and(isCloudy, isLandDay)
isClearLandDayMount = np.logical_and(isClear, isLandDayMount)
isCloudyLandDayMount = np.logical_and(isCloudy, isLandDayMount)
isClearCoastDay = np.logical_and(isClear, isCoastDay)
isCloudyCoastDay = np.logical_and(isCloudy, isCoastDay)
isClearCoastDayMount = np.logical_and(isClear, isCoastDayMount)
isCloudyCoastDayMount = np.logical_and(isCloudy, isCoastDayMount)

isClearIceTwilight = np.logical_and(isClear, isIceTwilight)
isCloudyIceTwilight = np.logical_and(isCloudy, isIceTwilight)
isClearWaterTwilight = np.logical_and(isClear, isWaterTwilight)
isCloudyWaterTwilight = np.logical_and(isCloudy, isWaterTwilight)
isClearLandTwilight =   np.logical_and(isClear, isLandTwilight)
isCloudyLandTwilight =  np.logical_and(isCloudy, isLandTwilight)
isClearLandTwilightMount =  np.logical_and(isClear, isLandTwilightMount)
isCloudyLandTwilightMount =  np.logical_and(isCloudy, isLandTwilightMount)
isClearLandTwilightInv =  np.logical_and(isClear,isLandTwilightInv) 
isCloudyLandTwilightInv = np.logical_and(isCloudy, isLandTwilightInv)
isClearCoastTwilightInv =  np.logical_and(isClear,isCoastTwilightInv) 
isCloudyCoastTwilightInv = np.logical_and(isCloudy, isCoastTwilightInv)
isClearCoastTwilight =  np.logical_and(isClear,isCoastTwilight) 
isCloudyCoastTwilight = np.logical_and(isCloudy, isCoastTwilight)

nodata = np.logical_or(t12<= -9, t37<= -9)
t37t12 = np.ma.array(t37-t12, mask = nodata)
nodata = np.logical_or(t11<= -9, t37<= -9)
t11t37 = np.ma.array(t11-t37, mask = nodata)
nodata = np.logical_or(t11<= -9, surftemp<= -9)
t11ts = np.ma.array(t11-surftemp, mask = nodata)
nodata = t11<= -9
t11 = np.ma.array(t11, mask = nodata)
nodata = np.logical_or(t11<= -9, t12<= -9)
t11t12 = np.ma.array(t11-t12, mask = nodata)
nodata = t11text<= -9
t11text = np.ma.array(t11text, mask = nodata)
nodata = r06text<= -9
r06text = np.ma.array(r06text, mask = nodata)
nodata = t37t12text<= -9
t37t12text = np.ma.array(t37t12text, mask = nodata)
nodata = t37text<= -9
t37text = np.ma.array(t37text, mask = nodata)
nodata = r06<= -9
r06 = np.ma.array(r06, mask = nodata)
nodata = r09<= -9
r09 = np.ma.array(r09, mask = nodata)
nodata = r16<= -9
r16 = np.ma.array(r16, mask = nodata)
pseudor06_not_scaled=r06
r06=r06/np.cos(np.radians(sunz))
r09=r09/np.cos(np.radians(sunz))
nodata = np.logical_or(r16<=-9,np.logical_or(r06<=-0.9, r06==0))
qr16r06 = np.ma.array(r16/r06,  mask = nodata)
nodata = thr_r06<= -9
thr_r06 = np.ma.array(thr_r06, mask = nodata)
t37_t12_minus_threshold = t37t12 - thr_t37t12
t37_t12_minus_threshold_inv = t37t12 - thr_t37t12_inv
t11_t37_minus_threshold = t11t37 - thr_t11t37
t11_ts_minus_threshold = t11ts - thr_t11ts
t11_ts_minus_threshold_inv = t11ts - thr_t11ts_inv
t11_t12_minus_threshold = t11t12 - thr_t11t12
t11_t12_minus_threshold_inv = t11t12 - thr_t11t12_inv

#----------------------------------------------
#Plotting
#----------------------------------------------
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def keep_combined_ok(TestOk,TestOkAll):
    if hasattr(TestOk,'mask') and hasattr(TestOkAll,'mask'):               
        return np.logical_or(TestOk.data, TestOkAll.data)
    elif hasattr(TestOkAll,'mask'):               
        return np.logical_or(TestOk, TestOkAll.data)
    elif hasattr(TestOk,'mask'):
        return np.logical_or(TestOk.data, TestOkAll)
    else:
        return np.logical_or(TestOk, TestOkAll)

def plot_inner(args,isCloudy, isClear, TestOk, THRESHOLD):
    isClearPPS = args['isClearPPS']  
    isCloudyPPS = args['isCloudyPPS']    
    xvector = args['xvector']
    yvector = args['yvector']
    fig = plt.figure(figsize = (9,8))
    ax = fig.add_subplot(111)
    isClearPPSCloudy = np.logical_and(isClear,isCloudyPPS)
    isCloudyPPSClear = np.logical_and(isCloudy,isClearPPS)
    isDetectedByThisTest = np.logical_and(np.logical_and(isCloudy,isCloudyPPS),
                                          TestOk)
    isMissclassifiedByThisTest = np.logical_and(isClear,TestOk)
    isNotDetectedByThisTest = np.logical_and(np.logical_and(isCloudy, 
                                                             TestOk),
                                              isClearPPS)
    #pixels inlcuded in plot and ok test and pps cloudy.
    isPPSCloudyForTestOk = np.logical_and(TestOk,
                                          np.logical_or(isCloudy,isClear))
    POD_cloudy=np.divide(len(xvector[isDetectedByThisTest==True])*1.0,
                         len(xvector[isCloudy==True]))
    FAR_cloudy=np.divide(len(xvector[isMissclassifiedByThisTest==True])*1.0,
                         len(xvector[isPPSCloudyForTestOk==True]))
    POD_cloudy_missed = np.divide(len(xvector[isNotDetectedByThisTest==True]),
                                  1.0*len(xvector[isCloudy==True]))
    if len(xvector[isNotDetectedByThisTest == True]) !=0:
        print "warning missed %d"%(len(xvector[isNotDetectedByThisTest == True]))
    POD_FAR_INFO =  (
        "Number of cloudy pixels considered %d \n"%(
            len(xvector[isCloudy==True]))+
        "Number of clouds detected by this test %d \n"%(
            len(xvector[isDetectedByThisTest==True]))+
        "Number of clouds misclassified by this test %d \n"%(
            len(xvector[isMissclassifiedByThisTest==True]))+
        "Number of cloudy pixels could be detected by this test %d \n"%(
            len(xvector[isNotDetectedByThisTest==True]))+
        "POD cloudy by this test %2.1f\n"%(POD_cloudy*100)+
        "FAR cloudy %2.1f\n"%(FAR_cloudy*100)+
        "POD cloudy missed %2.1f"%(POD_cloudy_missed*100))
    print "-Test stat---------"
    print args['title']
    print POD_FAR_INFO
    print "-------------------"
    clfree_percentiles = np.percentile(
        yvector[ np.logical_and(isClear,yvector.mask==False)==True],
        [01, 10, 25, 50, 75, 90, 99])
    #cloudy_percentiles = np.percentile(
    #    yvector[np.logical_and(isCloudy,yvector.mask==False)==True],
    #    [01, 10, 25, 50, 75, 90, 99])isCloudyPPSCorrectAll
    plt.plot(xvector[isCloudy == True], 
             yvector[isCloudy == True], 'r.')
    plt.plot(xvector[isCloudyPPSClear == True], 
             yvector[isCloudyPPSClear == True], 'y.')
    plt.plot(xvector[isClear == True], 
             yvector[isClear == True], 'bx')
    plt.plot(xvector[isDetectedByThisTest == True], 
             yvector[isDetectedByThisTest == True], 'm.')
    plt.plot(xvector[isMissclassifiedByThisTest == True], 
             yvector[isMissclassifiedByThisTest == True], 'cx')
    plt.plot(xvector[isNotDetectedByThisTest == True], 
             yvector[isNotDetectedByThisTest == True], 'g.')
    plt.axhline(y = THRESHOLD, color = 'k',linewidth = 2)
    plt.axhline(y = clfree_percentiles[0], color = 'b',ls = '--')
    plt.axhline(y = clfree_percentiles[1], color = 'b',ls = '--')
    plt.axhline(y = clfree_percentiles[3], color = 'b',linewidth = 2)
    plt.axhline(y = clfree_percentiles[5], color = 'b',ls = '--')
    plt.axhline(y = clfree_percentiles[6], color = 'b',ls = '--')
    ax.set_ylabel(args['ylable'])
    ax.set_xlabel(args['xlable'])
    limits = ax.axis()
    ax.set_ylim(1.3*limits[2]-0.3*limits[3],limits[3])
    plt.text(0.9*limits[0]+0.1*limits[1],1.25*limits[2]-0.25*limits[3], 
             POD_FAR_INFO, backgroundcolor='w')
    fig_title= (" %s \n"%(args['title'])+
                "blue-cyan: clear (calipso), red-manga: cloudy (clipso)\n"+
                "manga: detected cloudy by this test, " +
                "cyan: missclassifed by this test)")
    ax.set_title(fig_title)
    #filename=args['title']+"_"+SATELLITE+'.png'
    #plt.savefig('/local_disk/nina_pps/'+ filename)
    #plt.show()

def plot_test(args,isCloudy, isClear, TestOk, THRESHOLD, show=False):
    plot_inner(args,isCloudy, isClear, TestOk, THRESHOLD)
    filename=args['title']+"_"+SATELLITE+'.png'
    plt.savefig('/local_disk/nina_pps/threshold_plots/' + filename)
    if show:
        plt.show()
    plt.close()

def plot_test_2_lim(args,isCloudy, isClear, TestOk, 
                    THRESHOLD1, THRESHOLD2, show=False):
    plot_inner(args,isCloudy, isClear, TestOk, THRESHOLD1)
    #Add some vertical lines with threshold and clear percentiles.
    xvector = args['xvector']
    clfree_percentiles_vert = np.percentile(
        np.array(xvector[ np.logical_and(isClear, xvector.mask==False)==True]),
        [01, 10, 25, 50, 75, 90, 99])
    plt.axvline(x = clfree_percentiles_vert[0], color = 'b',ls = '--')
    plt.axvline(x = clfree_percentiles_vert[1], color = 'b',ls = '--')
    plt.axvline(x = clfree_percentiles_vert[3], color = 'b',linewidth = 2)
    plt.axvline(x = clfree_percentiles_vert[5], color = 'b',ls = '--')
    plt.axvline(x = clfree_percentiles_vert[6], color = 'b',ls = '--')
    plt.axvline(x = THRESHOLD2, color = 'k',linewidth = 2)
    filename=args['title']+"_"+SATELLITE+'.png'
    plt.savefig('/local_disk/nina_pps/threshold_plots/' + filename)
 
    if show:
        plt.show()
    plt.close()





def print_stats(cloudtype, isCloudyStats, isClearStats, 
                isCloudyPPS, TestOkAll=None):
    print "*********************************"
    print "*** stats so far ****"
    print "Number of cloudy pixels %d"%(
        len(cloudtype[isCloudyStats==True]))
    print "Number of clear pixels  %d"%(
        len(cloudtype[isClearStats==True]))
    print "Number of clear pixels miss classed  %d"%(
        len(cloudtype[np.logical_and(isClearStats,isCloudyPPS)==True]))
    print "POD cloudy %f"%(
        np.divide(len(cloudtype[np.logical_and(isCloudyStats,isCloudyPPS)==True])*1.0,
                  len(cloudtype[isCloudyStats==True])))
    print "FAR cloudy %f"%(np.divide(
                len(cloudtype[np.logical_and(isClearStats,isCloudyPPS)==True])*1.0,
                len(cloudtype[isCloudyStats==True])))
    print "Part clear missclassed %f"%(np.divide(
                len(cloudtype[np.logical_and(isClearStats,isCloudyPPS)==True])*1.0,
                len(cloudtype[isClearStats==True])))
    if TestOkAll is not None:
        detected_so_far=np.logical_and(TestOkAll, np.logical_and(
                isCloudyStats,isCloudyPPS))
        would_have_been_detected_so_far = np.logical_and(
            TestOkAll, 
            np.logical_and(isCloudyStats,isPPSCloudyOrClear))
        would_have_been_missclassed_so_far = np.logical_and(
            TestOkAll, 
            np.logical_and(isClearStats,isPPSCloudyOrClear))
        false_so_far=np.logical_and(
            TestOkAll, 
            np.logical_and(isClearStats,isCloudyPPS))
        print "Number cloudy  detected so far %f"%(
            len(cloudtype[detected_so_far==True]))
        print "POD cloudy  detected so far %f"%(
            len(cloudtype[detected_so_far==True])*1.0/
            len(cloudtype[isCloudyStats==True]))
        print "FAR cloudy so far %f"%(np.divide(
                len(cloudtype[false_so_far==True])*1.0,
                (len(cloudtype[false_so_far==True])+
                 len(cloudtype[detected_so_far==True]))))
        print "POD cloudy  detected so far including cahnges%f"%(
            np.divide(len(cloudtype[would_have_been_detected_so_far==True])*1.0,
            len(cloudtype[isCloudyStats==True])))
        print "FAR cloudy so far including changes %f"%(np.divide(
                len(cloudtype[would_have_been_missclassed_so_far==True])*1.0,
                (len(cloudtype[would_have_been_detected_so_far==True])+
                 len(cloudtype[would_have_been_missclassed_so_far==True]))))
    print "*********************************"



isBadShemesCloudy=np.logical_or(isCloudyLandNightInv,np.logical_or(isCloudyLandNightMount,isCloudyLandTwilight))
isBadShemesClear=np.logical_or(isClearLandNightInv,np.logical_or(isClearLandNightMount,isClearLandTwilight))
isGoodShemesCloudy=np.logical_and(np.logical_and(isPPSCloudyOrClear,isCloudy),
                                  np.equal(isBadShemesCloudy, False))
isGoodShemesClear=np.logical_and(np.logical_and(isPPSCloudyOrClear,isClear),
                                 np.equal(isBadShemesClear, False))
clear_dict={}
cloudy_dict={}
clear_dict['AllShemesCirrus'] = isClear
cloudy_dict['AllShemesCirrus'] = isThinCirrus
clear_dict['BadShemes'] = isBadShemesClear
cloudy_dict['BadShemes'] = isBadShemesCloudy
clear_dict['GoodShemes'] = isGoodShemesClear
cloudy_dict['GoodShemes'] = isGoodShemesCloudy

clear_dict['IceNight'] = isClearIceNight
cloudy_dict['IceNight'] = isCloudyIceNight
clear_dict['WaterNight'] =  isClearWaterNight
cloudy_dict['WaterNight'] = isCloudyWaterNight
clear_dict['LandNight'] = isClearLandNight 
cloudy_dict['LandNight'] =isCloudyLandNight 
clear_dict['LandNightMount'] = isClearLandNightMount 
cloudy_dict['LandNightMount'] = isCloudyLandNightMount
clear_dict['LandNightInv'] =  isClearLandNightInv
cloudy_dict['LandNightInv'] = isCloudyLandNightInv
clear_dict['CoastNightInv'] = isClearCoastNightInv 
cloudy_dict['CoastNightInv'] =isCloudyCoastNightInv 
clear_dict['CoastNight'] = isClearCoastNight 
cloudy_dict['CoastNight'] =isCloudyCoastNight 
clear_dict['IceDay'] =  isClearIceDay
cloudy_dict['IceDay'] = isCloudyIceDay
clear_dict['SunglintDay'] = isClearSunglintDay 
cloudy_dict['SunglintDay'] =isCloudySunglintDay 
clear_dict['WaterDay'] = isClearWaterDay 
cloudy_dict['WaterDay'] =isCloudyWaterDay 
clear_dict['LandDay'] = isClearLandDay 
cloudy_dict['LandDay'] =isCloudyLandDay 
clear_dict['LandDayMount'] = isClearLandDayMount 
cloudy_dict['LandDayMount'] = isCloudyLandDayMount
clear_dict['CoastDay'] = isClearCoastDay 
cloudy_dict['CoastDay'] =isCloudyCoastDay 
clear_dict['CoastDayMount'] =  isClearCoastDayMount
cloudy_dict['CoastDayMount'] =isCloudyCoastDayMount
clear_dict['IceTwilight'] =  isClearIceTwilight
cloudy_dict['IceTwilight'] = isCloudyIceTwilight
clear_dict['WaterTwilight'] =  isClearWaterTwilight
cloudy_dict['WaterTwilight'] = isCloudyWaterTwilight
clear_dict['LandTwilight'] =  isClearLandTwilight
cloudy_dict['LandTwilight'] = isCloudyLandTwilight
clear_dict['LandTwilightMount'] =  isClearLandTwilightMount
cloudy_dict['LandTwilightMount'] = isCloudyLandTwilightMount
clear_dict['LandTwilightInv'] = isClearLandTwilightInv 
cloudy_dict['LandTwilightInv'] = isCloudyLandTwilightInv
clear_dict['CoastTwilightInv'] =  isClearCoastTwilightInv
cloudy_dict['CoastTwilightInv'] = isCloudyCoastTwilightInv
clear_dict['CoastTwilight'] =  isClearCoastTwilight
cloudy_dict['CoastTwilight'] = isCloudyCoastTwilight

TestOkAll = None
for key in cloudy_dict.keys():
    print key
    print_stats(cloudtype, cloudy_dict[key], clear_dict[key], isCloudyPPS)
####################################
# NIGHT LAND MOUNTAIN
####################################
#----------------------------------
#watercloudtest land night  mountain
#----------------------------------
args = {'title': "waterCloudTest_All_LandNightMount",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET'] + OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET']
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll=TestOk
plot_test(args,isCloudyLandNightMount,isClearLandNightMount,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightMount,isClearLandNightMount,isCloudyPPS,TestOkAll)

THRESHOLD = 0.0
TestOk = t11_t37_minus_threshold>THRESHOLD
args['title']= "waterCloudTest_All_LandNightMount_removed"
plot_test(args,isCloudyLandNightMount,isClearLandNightMount,TestOk,THRESHOLD)

#----------------------------------
#ColdWaterCloudTest land night mountaion
#----------------------------------
args = {'title': "coldwaterCloudTest_All_LandNightMount",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.5
THRESHOLD1 = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT']+ -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
TSUR_THRESHOLD = 230
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT'] 
TestOk = np.logical_and(surftemp>TSUR_THRESHOLD,
                        np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                                       t11_ts_minus_threshold<THRESHOLD1))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyLandNightMount,isClearLandNightMount, TestOk, 
                THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyLandNightMount,isClearLandNightMount,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest land night  mountain
#----------------------------------
args = {'title': "coldCloudTest_All_LandNightMount_without_tsur_threshold_opaque",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT'] + OFFSETS['QUALITY_MARGIN_T11TSUR'] # -7.0-1.0
TSUR_THRESHOLD = 230
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT'] 
 
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightMount,isClearLandNightMount,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightMount,isClearLandNightMount,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest land night  mountain
#----------------------------------
args = {'title': "nonexisting_coldCloudTest_All_LandNightMount_without_tsur_threshold",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT'] + OFFSETS['QUALITY_MARGIN_T11TSUR'] # -7.0-1.0
TSUR_THRESHOLD = 230
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_MOUNTAIN_NIGHT'] 
 
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightMount,isClearLandNightMount,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightMount,isClearLandNightMount,isCloudyPPS,TestOkAll)

#----------------------------------
#ThinCirrusPrimaryTest land night mountain
#----------------------------------
args = {'title': "thinCirrusPrimaryTest_All_LandNightMount",
        'xlable': 'Tsur',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': surftemp,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T37T12_OFFSET_LAND_NIGHT']+OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T37T12_OFFSET_LAND_NIGHT'] -1.0
TSUR_THRESHOLD = 230
TestOk = np.logical_and(t37_t12_minus_threshold>THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightMount,isClearLandNightMount,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightMount,isClearLandNightMount,isCloudyPPS,TestOkAll)

####################################
# NIGHT Coast INVERSION
####################################
#----------------------------------
#watercloudtest coast night  inversion
#----------------------------------
args = {'title': "waterCloudTest_All_CoastNightInv",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD =OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET'] + OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET'] 
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll=TestOk
plot_test(args,isCloudyCoastNightInv,isClearCoastNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyCoastNightInv,isClearCoastNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#ColdWaterCloudTest  coast night  inversion
#----------------------------------
args = {'title': "coldwaterCloudTest_All_CoastNightInv",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
tmp_off=np.min([OFFSETS['T11_OFFSET_SEA_NIGHT'],OFFSETS['T11_OFFSET_LAND_NIGHT']])
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.5
THRESHOLD1 = tmp_off -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = tmp_off 
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                        t11_ts_minus_threshold<THRESHOLD1)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyCoastNightInv,isClearCoastNightInv, TestOk, 
                THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyCoastNightInv,isClearCoastNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#watercloudtest coast night  inversion
#----------------------------------
args = {'title': "removed_waterCloudTest_All_CoastNightInv_without_security_offset",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD =OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = 0.0
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD,surftemp>TSUR_THRESHOLD)
plot_test(args,isCloudyCoastNightInv,isClearCoastNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyCoastNightInv,isClearCoastNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#ThinCirrusPrimaryTest coast night  inversion
#----------------------------------
args = {'title': "thinCirrusPrimaryTest_All_CoastNightInv",
        'xlable': 'Tsur',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': surftemp,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
tmp_off=np.min([OFFSETS['T37T12_OFFSET_SEA_NIGHT'],OFFSETS['T37T12_OFFSET_LAND_NIGHT']])
THRESHOLD = tmp_off+OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = tmp_off -1.0
TestOk = t37_t12_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyCoastNightInv,isClearCoastNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyCoastNightInv,isClearCoastNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest coast night  inversion
#----------------------------------
args = {'title': "coldCloudTest_All_CoastNightInv_without_tsur_threshold",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_INVERSION_WEAK'] + OFFSETS['QUALITY_MARGIN_T11TSUR'] # -7.0-1.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_INVERSION_WEAK'] 
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>0)#TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyCoastNightInv,isClearCoastNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyCoastNightInv,isClearCoastNightInv,isCloudyPPS,TestOkAll)


####################################
# NIGHT LAND INVERSION
####################################
#----------------------------------
#watercloudtest land night  inversion
#----------------------------------
args = {'title': "waterCloudTest_All_LandNightInv",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET'] + OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET'] + 2.0 
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll=TestOk
plot_test(args,isCloudyLandNightInv,isClearLandNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightInv,isClearLandNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#ColdWaterCloudTest land night inverison 
#----------------------------------
args = {'title': "coldwaterCloudTest_All_LandNightInv",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.5
THRESHOLD1 = OFFSETS['T11_OFFSET_LAND_NIGHT']+ -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = OFFSETS['T11_OFFSET_LAND_NIGHT'] 
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                        t11_ts_minus_threshold<THRESHOLD1)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyLandNightInv,isClearLandNightInv, TestOk, 
                THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyLandNightInv,isClearLandNightInv,isCloudyPPS,TestOkAll)

#----------------------------------
#ThinCirrusPrimaryTest land night inv
#----------------------------------
args = {'title': "thinCirrusPrimaryTest_All_LandNightInv",
        'xlable': 'Tsur',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': surftemp,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T37T12_OFFSET_LAND_NIGHT']+OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T37T12_OFFSET_LAND_NIGHT'] -1.0
TestOk = t37_t12_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightInv,isClearLandNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightInv,isClearLandNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest land night  inv
#----------------------------------
args = {'title': "coldCloudTest_All_LandNightInv_without_tsur_threshold",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_INVERSION_WEAK'] + OFFSETS['QUALITY_MARGIN_T11TSUR'] # -7.0-1.0
#TSUR_THRESHOLD = 
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_INVERSION_WEAK'] 
    #TSUR_THRESHOLD = 
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>0)#TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightInv,isClearLandNightInv,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyLandNightInv,isClearLandNightInv,isCloudyPPS,TestOkAll)
#----------------------------------
#thinCirrusSecondaryTest night land inversion
#----------------------------------
print "thinCirrusSecondaryTest sea day no ice"
args = {'title': "thinCirrusSecondaryTest_All_LandNightInv_lat",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T12_OFFSET_LAND_NIGHT'] + OFFSETS['QUALITY_MARGIN_T11T12']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T12_OFFSET_LAND_NIGHT'] 
TestOk = t11_t12_minus_threshold>THRESHOLD 
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyLandNightInv, isClearLandNightInv, TestOk, THRESHOLD)
print_stats(cloudtype,isCloudyLandNightInv,isClearLandNightInv,isCloudyPPS,TestOkAll)


####################################
# SEA NIGHT
####################################
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS)
#----------------------------------
#ColdWaterCloudTest sea night 
#----------------------------------
args = {'title': "coldwaterCloudTest_All_SeaNightNoIce",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.5
THRESHOLD1 = OFFSETS['T11_OFFSET_SEA_NIGHT']+ -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = OFFSETS['T11_OFFSET_SEA_NIGHT']
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                        t11_ts_minus_threshold<THRESHOLD1)
TestOkAll=TestOk
plot_test_2_lim(args,isCloudyWaterNight,isClearWaterNight, TestOk, 
                THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,
            isCloudyPPS,TestOkAll)


#----------------------------------
#ThinCirrusPrimaryTest sea night 
#----------------------------------
print "thinCirrusPrimarytest all"
args = {'title': "thinCirrusPrimaryTest_All_SeaNightNoIce",
        'xlable': 'Tsur',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': surftemp,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T37T12_OFFSET_SEA_NIGHT']+OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T37T12_OFFSET_SEA_NIGHT']
TestOk = t37_t12_minus_threshold>THRESHOLD
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print "thinCirrusPrimarytest cirrus night sea"
args['title']= "thinCirrusPrimaryTest_ThinCirrus_SeaNightNoIce"
plot_test(args,isCloudyCirrusWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)
print ciwv
args = {'title': "thinCirrusPrimaryTest_All_SeaNightNoIce_ciwv",
        'xlable': 'Ciwv',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': ciwv,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
plot_test(args,isCloudyCirrusWaterNight,isClearWaterNight,TestOk,THRESHOLD)
args = {'title': "thinCirrusPrimaryTest_All_SeaNightNoIce_lat",
        'xlable': 'Latitude',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
plot_test(args,isCloudyCirrusWaterNight,isClearWaterNight,TestOk,THRESHOLD)
args = {'title': "testThinCirrusPrimaryTest_All_SeaNightNoIce_abslat_linearthreshold",
        'xlable': 'abs Latitude',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': np.abs(latitude),
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T37T12_OFFSET_SEA_NIGHT']+OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
THRESHOLD_V=abs(latitude)*(THRESHOLD+1.0)/40-1.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T37T12_OFFSET_SEA_NIGHT']
    THRESHOLD_V=abs(latitude)*(THRESHOLD+1.0)/40-1.0
TestOk = args['yvector']>THRESHOLD_V
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyCirrusWaterNight,isClearWaterNight,TestOk,THRESHOLD)

args = {'title':  "testThinCirrusPrimaryTest_ThinCirrus_SeaNightNoIce_lat_modified_thr",
        'xlable': 'Latitude',
        'ylable': 'T37-T12 minus 0.5*dynamic threshold',
        'xvector': latitude,
        'yvector': t37t12 -0.5*thr_t37t12,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T37T12_OFFSET_SEA_NIGHT']+3**OFFSETS['QUALITY_MARGIN_T37T12']#2.0+0.3
if RunWithOutMargins:
    OFFSETS['T37T12_OFFSET_SEA_NIGHT']
TestOk = args['yvector']>THRESHOLD 
plot_test(args,isCloudyCirrusWaterNight, isClearWaterNight, TestOk, THRESHOLD)

#----------------------------------
#textureNightTest sea night 
#----------------------------------
print "textureNightTest sea night"
args = {'title': "texturNightTest_All_SeaNightNoIce",
        'xlable': 'T37-T12text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': t37t12text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_NIGHT'] + OFFSETS['QUALITY_MARGIN_T11TEXT']#0.85+0.15
THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT'] + OFFSETS['QUALITY_MARGIN_T37T12TEXT']#0.75+0.15
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_NIGHT']
    THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT']
TestOk = np.logical_and(t11text>THRESHOLD2, t37t12text>THRESHOLD1)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterNight, isClearWaterNight, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)
args = {'title': "testtexturNightTest_All_SeaNightNoIce",
        'xlable': 'T37-T12text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': t37t12text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = 0#OFFSETS['T11TEXT_OFFSET_SEA_NIGHT'] + OFFSETS['QUALITY_MARGIN_T11TEXT']#0.85+0.15
THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT'] + OFFSETS['QUALITY_MARGIN_T37T12TEXT']#0.75+0.15
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT']

TestOk = np.logical_and(t11text>THRESHOLD2, t37t12text>THRESHOLD1)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterNight, isClearWaterNight, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)

#----------------------------------
#notexistingCirrustest sea night 
#----------------------------------
print "notexistingCirrustest sea night"
args = {'title': "non_existingT11T12test_All_SeaNightNoIce",
      'xlable': 'Tsur',
      'ylable': 'T11-T12 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t12_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = 0.3
TestOk = t11_t12_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)

#----------------------------------
#coldcloudtest sea night 
#----------------------------------
args = {'title': "coldCloudTest_All_SeaNightNoIce_with_Tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_SEA_NIGHT'] #+ OFFSETS[] # -7.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']#
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_SEA_NIGHT'] 
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] 
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)
args = {'title': "coldCloudTest_All_SeaNightNoIce_with_Tsur_limit_lat",
      'xlable': 'Latitude',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': latitude,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
args = {'title': "coldCloudTest_All_SeaNightNoIce_with_Tsur_limit_ciwv",
      'xlable': 'Ciwv',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': ciwv,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)

#----------------------------------
#watercloudtest sea night 
#----------------------------------
print "watercloudtest sea night "
args = {'title': "waterCloudTest_All_SeaNightNoIce",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = 0.0 + OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = 0.0
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)
args = {'title': "waterCloudTest_All_SeaNightNoIce_lat",
      'xlable': 'Latitude',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': latitude,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
args = {'title': "waterCloudTest_All_SeaNightNoIce_ciwv",
      'xlable': 'Ciwv',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': ciwv,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)

#----------------------------------
#coldcloudtest sea night without tsur limit
#----------------------------------
print "coldcloudtest sea night"
args = {'title': "coldCloudTest_All_SeaNightNoIce_without_Tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_SEA_NIGHT_OPAQUE'] + -1*OFFSETS['QUALITY_MARGIN_T11TSUR'] #-15.0-1.0
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_SEA_NIGHT_OPAQUE']
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterNight,isClearWaterNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterNight,isClearWaterNight,isCloudyPPS,TestOkAll)


print "WatercloudTestt85t11sea"
print      "**not done yet**"
print "watercloudOverWaterTest"
print "*** need warmest neighbour to plot this test***"
####################################
# TWILIGHT ICE
####################################
isCloudyIceTwilight = np.logical_and(isCloudyIceTwilight, np.not_equal(cloudtype,4))
isClearIceTwilight = np.logical_and(isClearIceTwilight, np.not_equal(cloudtype,4))
print "***snow test, not implemented***"
#----------------------------------
#thinCirrusSecondaryTest sea twilight ice
#----------------------------------
args = {'title': "thinCirrusSecondaryTest_All_SeaTwilightIce_lat",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
tmp_thr = 0.5*(OFFSETS['T11T12_OFFSET_SEA_NIGHT'] + OFFSETS['T11T12_OFFSET_SEA_DAY'])
THRESHOLD =tmp_thr  + OFFSETS['QUALITY_MARGIN_T11T12']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD = tmp_thr 
TestOk = t11_t12_minus_threshold>THRESHOLD 
TestOkAll = TestOk
plot_test(args,isCloudyIceTwilight, isClearIceTwilight, TestOk, THRESHOLD, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS, TestOkAll)
#----------------------------------
#textureIrvisTest sea twilight  ice
#----------------------------------
args = {'title': "textureIrvisTest_All_SeaTwilightIce",
        'xlable': 'r06text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': r06text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['R06TEXT_OFFSET_SUNGLINT'] + OFFSETS['QUALITY_MARGIN_R06TEXT']
THRESHOLD1 = OFFSETS['T11TEXT_OFFSET_SUNGLINT'] + OFFSETS['QUALITY_MARGIN_T11TEXT']
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
SUNZ_THRESHOLD = OFFSETS['SUNZEN_DAY_MAX']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['R06TEXT_OFFSET_SUNGLINT']
    THRESHOLD1 = OFFSETS['T11TEXT_OFFSET_SUNGLINT']
    TSUR_THRESHOLD = 0.0#OFFSETS['COLDEST_SEASURFACE_TEMP']
    SUNZ_THRESHOLD = OFFSETS['SUNZEN_DAY_MAX']
TestOk = np.logical_and(np.logical_and(t11text>THRESHOLD2, 
                                       r06text>THRESHOLD1),
                        np.logical_and(sunz<SUNZ_THRESHOLD,
                                       surftemp> TSUR_THRESHOLD))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceTwilight, isClearIceTwilight, TestOk, THRESHOLD1, THRESHOLD2, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS, TestOkAll)
#----------------------------------
#textureNightTest sea twilight  ice
#----------------------------------
args = {'title': "texturNightTest_All_SeaTwilightIce",
        'xlable': 'T37-T12text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': t37t12text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_DAY'] + OFFSETS['QUALITY_MARGIN_T11TEXT']#0.85+0.15
THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_DAY'] + OFFSETS['QUALITY_MARGIN_T37T12TEXT']#0.75+0.15
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_DAY']
    THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_DAY']
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
TestOk = np.logical_and(t11text>THRESHOLD2, 
                        np.logical_and(t37t12text>THRESHOLD1, 
                                       surftemp> TSUR_THRESHOLD))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceTwilight, isClearIceTwilight, TestOk, THRESHOLD1, THRESHOLD2, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest sea twilight ice
#----------------------------------
args = {'title': "coldCloudTest_All_SeaTwilightIce_without_Tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE'] -1*OFFSETS['QUALITY_MARGIN_T11TSUR'] #-15.0-1.0
if RunWithOutMargins:
    THRESHOLD =  OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE']
TSUR_THRESHOLD=0.0
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyIceTwilight,isClearIceTwilight,TestOk,THRESHOLD, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#reflectingCloudTest sea twilight ice
#----------------------------------
args = {'title': "reflectingCloudTest_All_SeaTwilightIce",
      'xlable': 'r06 not scaled',
      'ylable': 'T37-T2 minus dynamic threshold',
      'xvector': pseudor06_not_scaled,
      'yvector': t37_t12_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
tmp_thr = 0.5*(OFFSETS['T37T12_OFFSET_SEA_NIGHT'] + OFFSETS['T37T12_OFFSET_SEA_DAY'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = tmp_thr +1*OFFSETS['QUALITY_MARGIN_T37T12']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = tmp_thr 
TestOk = np.logical_and(2>0,
                        np.logical_and(t37_t12_minus_threshold>THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceTwilight,isClearIceTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS, TestOkAll)

#----------------------------------
#pseudo06CloudTest3A sea twilight ice
#----------------------------------
args = {'title': "pseudo06CloudTest3A_All_SeaTwilightIce",
      'xlable': 'r06 not scaled',
      'ylable': 'qr16r06',
      'xvector': pseudor06_not_scaled,
      'yvector': qr16r06,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = OFFSETS['R06_R16_THR_LOWSUN'] + 1*OFFSETS['QUALITY_MARGIN_QR16R06']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = OFFSETS['R06_R16_THR_LOWSUN']
TestOk = np.logical_and(2>0,
                        np.logical_and(qr16r06>THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudy,isClear, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=False)
plot_test_2_lim(args,isCloudyIceTwilight,isClearIceTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)

#----------------------------------
#ColdWaterCloudTest sea twilight ice
#----------------------------------
args = {'title': "coldwaterCloudTest_All_SeaTwilightIce",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
tmp_thr = np.min([OFFSETS['T11_OFFSET_SEA_NIGHT'], OFFSETS['T11_OFFSET_SEA_DAY']])
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#
THRESHOLD1 = tmp_thr -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = tmp_thr 
TestOk = np.logical_and(surftemp>TSUR_THRESHOLD,
                        np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                                       t11_ts_minus_threshold<THRESHOLD1))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceTwilight,isClearIceTwilight, TestOk, 
                THRESHOLD1, THRESHOLD2, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#watercloudtest sea twilight ice
#----------------------------------
args = {'title': "waterCloudTest_All_SeaTwilightIce",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = 0.0 + OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = 0.0
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyIceTwilight,isClearIceTwilight,TestOk,THRESHOLD, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest sea twilight ice
#----------------------------------
args = {'title': "coldCloudTest_All_SeaTwilightIce_with_tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
tmp_thr=np.min([OFFSETS['T11_OFFSET_SEA_DAY'],OFFSETS['T11_OFFSET_SEA_NIGHT']])
THRESHOLD = tmp_thr -1*OFFSETS['QUALITY_MARGIN_T11TSUR'] #-15.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']
if RunWithOutMargins:
    THRESHOLD = tmp_thr
    TSUR_THRESHOLD= OFFSETS['COLDEST_SEASURFACE_TEMP']
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyIceTwilight,isClearIceTwilight,TestOk,THRESHOLD, show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#reflectingCloudTest sea twilight ice
#----------------------------------
args = {'title': "removed_reflectingCloudTestSea_All_SeaTwilightIce",
      'xlable': 'r06 not scaled',
      'ylable': 'T11',
      'xvector': pseudor06_not_scaled,
      'yvector': t11,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = OFFSETS['T11_SEA_MIN'] -1*OFFSETS['QUALITY_MARGIN_T11']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = OFFSETS['T11_SEA_MIN'] #+1*OFFSETS['QUALITY_MARGIN_T11']
TestOk = np.logical_and(2>0,
                        np.logical_and(t11<THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))
#TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudy,isClear, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=False)
plot_test_2_lim(args,isCloudyIceTwilight,isClearIceTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=False)
print_stats(cloudtype,isCloudyIceTwilight,isClearIceTwilight,isCloudyPPS,TestOkAll)

args = {'title': "T12T37_T11TS_All_SeaTwilightIce",
      'ylable': 'T12-Ts minus dynamic threshold',
      'xlable': 'T11-T37 minus dynamic threshold',
      'xvector': t37_t12_minus_threshold,
      'yvector': t11_ts_minus_threshold_inv,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
TestOk=np.where(TestOk,False,False)
plot_test_2_lim(args,isCloudyIceTwilight, isClearIceTwilight, TestOk, 0, 0, show=True)

####################################
# TWILIGHT SEA NO ICE 
####################################
isCloudyWaterTwilight = np.logical_and(isCloudyWaterTwilight, np.not_equal(cloudtype,4))
isClearWaterTwilight = np.logical_and(isClearWaterTwilight, np.not_equal(cloudtype,4))
print "***snow test, not implemented***"
#----------------------------------
#thinCirrusSecondaryTest sea twilightno ice
#----------------------------------
args = {'title': "thinCirrusSecondaryTest_All_SeaTwilightNoIce_lat",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
tmp_thr = 0.5*(OFFSETS['T11T12_OFFSET_SEA_NIGHT'] + OFFSETS['T11T12_OFFSET_SEA_DAY'])
THRESHOLD =tmp_thr  + OFFSETS['QUALITY_MARGIN_T11T12']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD = tmp_thr
TestOk = t11_t12_minus_threshold>THRESHOLD 
TestOkAll = TestOk
plot_test(args,isCloudyWaterTwilight, isClearWaterTwilight, TestOk, THRESHOLD, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS, TestOkAll)
#----------------------------------
#textureIrvisTest sea twilight no ice
#----------------------------------
args = {'title': "textureIrvisTest_All_SeaTwilightNoIce",
        'xlable': 'r06text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': r06text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['R06TEXT_OFFSET_SUNGLINT'] + OFFSETS['QUALITY_MARGIN_R06TEXT']
THRESHOLD1 = OFFSETS['T11TEXT_OFFSET_SUNGLINT'] + OFFSETS['QUALITY_MARGIN_T11TEXT']
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
SUNZ_THRESHOLD = OFFSETS['SUNZEN_DAY_MAX']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['R06TEXT_OFFSET_SUNGLINT']
    THRESHOLD1 = OFFSETS['T11TEXT_OFFSET_SUNGLINT']
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
    SUNZ_THRESHOLD = OFFSETS['SUNZEN_DAY_MAX']
TestOk = np.logical_and(np.logical_and(t11text>THRESHOLD2, 
                                       r06text>THRESHOLD1),
                        np.logical_and(sunz<SUNZ_THRESHOLD,
                                       surftemp> TSUR_THRESHOLD))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterTwilight, isClearWaterTwilight, TestOk, THRESHOLD1, THRESHOLD2, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS, TestOkAll)
#----------------------------------
#textureNightTest sea twilight no ice
#----------------------------------
args = {'title': "texturNightTest_All_SeaTwilightNoIce",
        'xlable': 'T37-T12text minus dynamic threshold',
        'ylable': 'T11text minus dynamic threshold',
        'xvector': t11text,
        'yvector': t37t12text,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_DAY'] + OFFSETS['QUALITY_MARGIN_T11TEXT']#0.85+0.15
THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_DAY'] + OFFSETS['QUALITY_MARGIN_T37T12TEXT']#0.75+0.15
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T11TEXT_OFFSET_SEA_DAY']
    THRESHOLD1 = OFFSETS['T37T12TEXT_OFFSET_SEA_DAY']
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
TestOk = np.logical_and(t11text>THRESHOLD2, 
                        np.logical_and(t37t12text>THRESHOLD1, 
                                       surftemp> TSUR_THRESHOLD))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterTwilight, isClearWaterTwilight, TestOk, THRESHOLD1, THRESHOLD2, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest sea twilightno ice
#----------------------------------
args = {'title': "coldCloudTest_All_SeaTwilightNoIce_without_Tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE'] -1*OFFSETS['QUALITY_MARGIN_T11TSUR'] #-15.0-1.0
if RunWithOutMargins:
    THRESHOLD =  OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE']
TSUR_THRESHOLD=0.0
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterTwilight,isClearWaterTwilight,TestOk,THRESHOLD, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#reflectingCloudTest sea twilightno ice
#----------------------------------
args = {'title': "reflectingCloudTest_All_SeaTwilightNoIce",
      'xlable': 'r06 not scaled',
      'ylable': 'T37-T2 minus dynamic threshold',
      'xvector': pseudor06_not_scaled,
      'yvector': t37_t12_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
tmp_thr = 0.5*(OFFSETS['T37T12_OFFSET_SEA_NIGHT'] + OFFSETS['T37T12_OFFSET_SEA_DAY'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = tmp_thr +1*OFFSETS['QUALITY_MARGIN_T37T12']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = tmp_thr 
TestOk = np.logical_and(2>0,
                        np.logical_and(t37_t12_minus_threshold>THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterTwilight,isClearWaterTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS, TestOkAll)

#----------------------------------
#pseudo06CloudTest3A sea twilightno ice
#----------------------------------
args = {'title': "pseudo06CloudTest3A_All_SeaTwilightNoIce",
      'xlable': 'r06 not scaled',
      'ylable': 'qr16r06',
      'xvector': pseudor06_not_scaled,
      'yvector': qr16r06,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = OFFSETS['R06_R16_THR_LOWSUN'] + 1*OFFSETS['QUALITY_MARGIN_QR16R06']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = OFFSETS['R06_R16_THR_LOWSUN']
TestOk = np.logical_and(2>0,
                        np.logical_and(qr16r06>THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudy,isClear, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=True)
plot_test_2_lim(args,isCloudyWaterTwilight,isClearWaterTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)

#----------------------------------
#ColdWaterCloudTest sea twilightno ice
#----------------------------------
args = {'title': "coldwaterCloudTest_All_SeaTwilightNoIce",
      'xlable': 'T11-T37 minus dynamic threshold',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
tmp_thr = np.min([OFFSETS['T11_OFFSET_SEA_NIGHT'], OFFSETS['T11_OFFSET_SEA_DAY']])
THRESHOLD2 = 0.0 +OFFSETS['QUALITY_MARGIN_T11T37']#
THRESHOLD1 = tmp_thr -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = 0.0
    THRESHOLD1 = tmp_thr 
TestOk = np.logical_and(surftemp>TSUR_THRESHOLD,
                        np.logical_and(t11_t37_minus_threshold>THRESHOLD2,
                                       t11_ts_minus_threshold<THRESHOLD1))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterTwilight,isClearWaterTwilight, TestOk, 
                THRESHOLD1, THRESHOLD2, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#watercloudtest sea twilightno ice
#----------------------------------
args = {'title': "waterCloudTest_All_SeaTwilightNoIce",
      'xlable': 'Latitude',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': latitude,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET']+ OFFSETS['QUALITY_MARGIN_T11T37']#0.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T37_WATERCLOUD_SECURITY_OFFSET']
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterTwilight,isClearWaterTwilight,TestOk,THRESHOLD, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#coldcloudtest sea twilightno ice
#----------------------------------
args = {'title': "coldCloudTest_All_SeaTwilightNoIce_with_tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
tmp_thr=np.min([OFFSETS['T11_OFFSET_SEA_DAY'],OFFSETS['T11_OFFSET_SEA_NIGHT']])
THRESHOLD = tmp_thr -1*OFFSETS['QUALITY_MARGIN_T11TSUR'] #-15.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']
if RunWithOutMargins:
    THRESHOLD = tmp_thr
    TSUR_THRESHOLD= OFFSETS['COLDEST_SEASURFACE_TEMP']
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterTwilight,isClearWaterTwilight,TestOk,THRESHOLD, show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)
#----------------------------------
#reflectingCloudTest sea twilightno ice
#----------------------------------
args = {'title': "reflectingCloudTestSea_All_SeaTwilightNoIce",
      'xlable': 'r06 not scaled',
      'ylable': 'T11',
      'xvector': pseudor06_not_scaled,
      'yvector': t11,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
vis_static = np.where(
    sunz>=90.0,
    OFFSETS['VIS_STATIC_SEA_OFFSET'],
    OFFSETS['VIS_STATIC_SEA_GAIN']*(90.0-sunz) + OFFSETS['VIS_STATIC_SEA_OFFSET'])
THRESHOLD2 = vis_static +OFFSETS['QUALITY_MARGIN_VIS_STATIC']
THRESHOLD1 = OFFSETS['T11_SEA_MIN'] -1*OFFSETS['QUALITY_MARGIN_T11']
TSUR_THRESHOLD = 0.0
if RunWithOutMargins:
    THRESHOLD2 = vis_static
    THRESHOLD1 = OFFSETS['T11_SEA_MIN'] -2.5 #+1*OFFSETS['QUALITY_MARGIN_T11']
TestOk = np.logical_and(2>0,
                        np.logical_and(t11<THRESHOLD1,
                                       pseudor06_not_scaled>THRESHOLD2))

TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudy,isClear, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=True)
plot_test_2_lim(args,isCloudyWaterTwilight,isClearWaterTwilight, TestOk, 
                THRESHOLD1, np.mean(THRESHOLD2), show=True)
print_stats(cloudtype,isCloudyWaterTwilight,isClearWaterTwilight,isCloudyPPS,TestOkAll)

args = {'title': "T12T37_T11TS_All_SeaTwilightNoIce",
      'ylable': 'T12-Ts minus dynamic threshold',
      'xlable': 'T11-T37 minus dynamic threshold',
      'xvector': t37_t12_minus_threshold,
      'yvector': t11_ts_minus_threshold_inv,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
TestOk=np.where(TestOk,False,False)
plot_test_2_lim(args,isCloudyWaterTwilight, isClearWaterTwilight, TestOk, 0, 0, show=True)


####################################
# NIGHT ICE
####################################
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS)
TestOkAll=None
#----------------------------------
#arcticwaterCloudTest sea night
#----------------------------------
print "arcticwatercloudTest sea night ice"
args = {'title': "arcticWaterCloudTest_All_SeaNightIce",
      'xlable': 't3712text',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': t37t12text,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD1 = 0.0 + OFFSETS['QUALITY_MARGIN_T11T37_ARCTIC']
THRESHOLD2 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT_ARCTIC']  + OFFSETS['QUALITY_MARGIN_T37T12TEXT']
if RunWithOutMargins:
    THRESHOLD1 = 0.0
    THRESHOLD2 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT_ARCTIC']
TestOk = np.logical_and(t11_t37_minus_threshold>THRESHOLD1,t37t12text<THRESHOLD2)
TestOkAll=TestOk
plot_test_2_lim(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD2, show=True)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#coldcloudtest sea night ice
#----------------------------------
args = {'title': "coldCloudTest_All_SeaNightIce_without_Tsur_limit",
      'xlable': 'Tsur',
      'ylable': 'T11-Ts minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_ts_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['OFFSET_T11TSUR_ARCTIC'] -1*OFFSETS['QUALITY_MARGIN_T11TSUR_ARCTIC'] #-15.0-1.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['OFFSET_T11TSUR_ARCTIC'] 
TSUR_THRESHOLD=0.0
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyIceNight,isClearIceNight,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticThinCirrusPrimaryTest sea night ice
#----------------------------------
args = {'title': "arcticThinCirrusPrimaryTest_All_SeaNightIce",
        'xlable': 'T37text',
        'ylable': 'T37-T12 minus dynamic threshold',
        'xvector': t37text,
        'yvector': t37_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T37TEXT_OFFSET_SEA_NIGHT_ARCTIC']+OFFSETS['QUALITY_MARGIN_T37TEXT']#2.0+0.3
THRESHOLD1 = OFFSETS['OFFSET_T37T12_ARCTIC'] + OFFSETS['QUALITY_MARGIN_T37T12_ARCTIC']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T37TEXT_OFFSET_SEA_NIGHT_ARCTIC']
    THRESHOLD1 = OFFSETS['OFFSET_T37T12_ARCTIC']
TestOk = np.logical_and(t37_t12_minus_threshold>THRESHOLD1, t37text<THRESHOLD2)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceNight,isClearIceNight,TestOk,THRESHOLD1, THRESHOLD2)
print "arcticthinCirrusPrimarytest cirrus night sea ice"
args['title']= "arcticthinCirrusPrimaryTest_ThinCirrus_SeaNightIce"
plot_test_2_lim(args,isCloudyCirrusIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticThinWaterCloudTest sea night ice
#----------------------------------
print "arcticThinWaterCloudTest all"
args = {'title': "arcticThinWaterCloudTest_All_SeaNightIce",
        'xlable': 'T37t12text',
        'ylable': 'T37-T12 minus dynamic threshold inv',
        'xvector': t37t12text,
        'yvector': t37_t12_minus_threshold_inv,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT_ARCTIC']+OFFSETS['QUALITY_MARGIN_T37T12TEXT']#2.0+0.3
THRESHOLD1 = OFFSETS['OFFSET_T37T12_ARCTIC_INV'] + OFFSETS['QUALITY_MARGIN_T37T12_ARCTIC']
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT_ARCTIC'] 
    THRESHOLD1 = OFFSETS['OFFSET_T37T12_ARCTIC_INV']

TestOk = np.logical_and(t37_t12_minus_threshold_inv<THRESHOLD1, t37t12text<THRESHOLD2)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceNight,isClearIceNight,TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticWarmcloudtest sea night ice
#----------------------------------
print "arcticWarmcloudtest sea night"
args = {'title': "removed_arcticWarmCloudTest_All_SeaNightIce",
      'xlable': 't37text',
      'ylable': 'T11-Ts minus dynamic threshold inv',
      'xvector': t37text,
      'yvector': t11_ts_minus_threshold_inv,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD1 = 0.0 -18.0#-1*OFFSETS['QUALITY_MARGIN_T11TSUR_ARCTIC_INV']
THRESHOLD2 = 1.5 + 0.5#OFFSETS['T37TEXT_OFFSET_SEA_NIGHT_ARCTIC']  + OFFSETS['QUALITY_MARGIN_T37TEXT']
TestOk = np.logical_and(t11_ts_minus_threshold_inv>THRESHOLD1,t37text<THRESHOLD2)
plot_test_2_lim(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticWarmcloudtest Salomons sea night ice
#----------------------------------
args = {'title': "SalomonsArcticWarmCloudTest_All_SeaNightIce",
      'ylable': 'T11-Ts minus dynamic threshold',
      'xlable': 'T11-T37 minus dynamic threshold',
      'xvector': t11_t37_minus_threshold,
      'yvector': t11_ts_minus_threshold_inv,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD1 = OFFSETS['OFFSET_T11TSUR_ARCTIC_INV'] + OFFSETS['QUALITY_MARGIN_T11TSUR_ARCTIC'] #3.0
THRESHOLD2 = OFFSETS['T37T12TEXT_OFFSET_SEA_NIGHT_ARCTIC'] + OFFSETS['QUALITY_MARGIN_T37T12TEXT'] #-0.4
THRESHOLD3 = OFFSETS['QUALITY_MARGIN_T11T37_ARCTIC'] #0.3
THRESHOLD4 = OFFSETS['QUALITY_MARGIN_T37T12_ARCTIC'] #0.6
TestOk = np.logical_and(np.logical_and(t11_ts_minus_threshold_inv>THRESHOLD1,
                                       t37_t12_minus_threshold_inv<THRESHOLD2),
                        np.logical_and(t11_t37_minus_threshold>THRESHOLD3,
                                       t37t12text<THRESHOLD4))
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD3)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticWarmCirrusSecondaryTest sea night
#----------------------------------
args = {'title': "arcticWarmCirrusSecondaryTest_All_SeaNightIce_tsur",
      'xlable': 'Tsur',
      'ylable': 'T11-T12 minus dynamic threshold inv',
      'xvector': surftemp,
      'yvector': t11_t12_minus_threshold_inv,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}

THRESHOLD = OFFSETS['OFFSET_T11T12_ARCTIC_INV'] -1* OFFSETS['QUALITY_MARGIN_T11T12_ARCTIC']
if RunWithOutMargins:
    pass
    #Not run without thresholds!
    #THRESHOLD = OFFSETS['OFFSET_T11T12_ARCTIC_INV'] #MARGIN are offset
TestOk = t11_t12_minus_threshold_inv<THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#arcticThinCirrusSecondaryTest sea night ice
#----------------------------------
args = {'title': "arcticthinCirrusSecondaryTest_All_SeaNightIce",
        'xlable': 'T37text',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': t37text,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD2 = OFFSETS['T37TEXT_OFFSET_SEA_NIGHT_ARCTIC']+OFFSETS['QUALITY_MARGIN_T37TEXT']
THRESHOLD1 = OFFSETS['OFFSET_T11T12_ARCTIC'] + OFFSETS['QUALITY_MARGIN_T11T12_ARCTIC']
print OFFSETS['OFFSET_T11T12_ARCTIC']
plt.show()
if RunWithOutMargins:
    THRESHOLD2 = OFFSETS['T37TEXT_OFFSET_SEA_NIGHT_ARCTIC']
    THRESHOLD1 = OFFSETS['OFFSET_T11T12_ARCTIC']
TestOk = np.logical_and(t11_t12_minus_threshold>THRESHOLD1, t37text<THRESHOLD2)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD2)
print "thinCirrusSecondarytest cirrus night sea ice"
args['title']= "arcticthinCirrusSecondaryTest_ThinCirrus_SeaNightIce"
plot_test_2_lim(args,isCloudyCirrusIceNight, isClearIceNight, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)

#----------------------------------
#extra waterCloudTest sea night
#----------------------------------
args = {'title': "removed_waterCloudTest_All_SeaNightIce_tsur",
      'xlable': 'Tsur',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': surftemp,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = 0.0 + OFFSETS['QUALITY_MARGIN_T11T37_ARCTIC_EXTRA']
if RunWithOutMargins:
    THRESHOLD = 0.0 + OFFSETS['QUALITY_MARGIN_T11T37_ARCTIC_EXTRA']
TestOk = t11_t37_minus_threshold>THRESHOLD
plot_test(args,isCloudyIceNight, isClearIceNight, TestOk, THRESHOLD)
print_stats(cloudtype,isCloudyIceNight,isClearIceNight,isCloudyPPS,TestOkAll)




####################################
# SEA DAY
####################################

print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS)
print "snowSeaTest sea day"
print "not done yet"

#----------------------------------
#coldCloudTest sea day
#----------------------------------
print "coldcloudtest sea day"
args = {'title': "coldCloudTest_All_SeaDayNoIce",
        'xlable': 'Tsur',
        'ylable': 'T11-Ts minus dynamic threshold',
        'xvector': surftemp,
        'yvector': t11_ts_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY'] + -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']#
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY']
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] 

TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll=TestOk
plot_test(args,isCloudyWaterDay,isClearWaterDay,TestOk,THRESHOLD)
args['title'] = "coldCloudTest_All_SeaDayNoIce_without_Tsur_limit"
THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE'] + OFFSETS['QUALITY_MARGIN_T11TSUR']#-13.0-1.0
TSUR_THRESHOLD=0.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11_OFFSET_SEA_DAY_OPAQUE'] 
    TSUR_THRESHOLD=0.0
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD,surftemp>TSUR_THRESHOLD)
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterDay,isClearWaterDay,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)
#----------------------------------
#coldBrightCloudTest sea day
#----------------------------------
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)
print "coldBrightCloudTest sea day no ice"
r06_minus_threshold_opaque =  r06 - 100.0*thr_r06*OFFSETS['R06_GAIN_SEA_OPAQUE']
r06_minus_threshold_opaque = np.ma.array(
    r06_minus_threshold_opaque, 
    mask=np.logical_or(r06.mask,thr_r06.mask))
print len(r06_minus_threshold_opaque[r06_minus_threshold_opaque.mask==False])
print len(t11_ts_minus_threshold)
args = {'title': "coldBrightCloudTest_All_SeaDayNoIce",
        'xlable': 'R06 minus dynamic threshold',
        'ylable': 'T11-Ts minus dynamic threshold',
        'xvector': r06_minus_threshold_opaque,
        'yvector': t11_ts_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD1 = OFFSETS['T11_OFFSET_SEA_DAY'] + -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']#
#100.0*threshold->r06*throff->sm_acmg_r06_gain_sea_opaque +
#      throff->sm_acmg_r06_offset_sea_opaque;
#100.0*threshold->r06*throff->sm_acmg_r06_gain_sea_opaque +
#      throff->sm_acmg_r06_offset_sea_opaque;
#/* The satellite reflectances are given in percent. Thus
#   multiply tabulated reflectances by 100.0!	*/
THRESHOLD2 = OFFSETS['R06_OFFSET_SEA_OPAQUE'] + OFFSETS['QUALITY_MARGIN_R06']
if RunWithOutMargins:
    HRESHOLD1 = OFFSETS['T11_OFFSET_SEA_DAY'] 
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP']
    THRESHOLD2 = OFFSETS['R06_OFFSET_SEA_OPAQUE']
TestOk = np.logical_and(np.logical_and(t11_ts_minus_threshold<THRESHOLD1,
                                       surftemp>TSUR_THRESHOLD),
                        r06_minus_threshold_opaque>THRESHOLD2)                        
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterDay, isClearWaterDay, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)

print "testcoldBrightCloudTest sea day no ice"
r06_minus_threshold_opaque =  r06 - 100.0*thr_r06*OFFSETS['R06_GAIN_SEA_OPAQUE']
r06_minus_threshold_opaque = np.ma.array(
    r06_minus_threshold_opaque, 
    mask=np.logical_or(r06.mask,thr_r06.mask))
print len(r06_minus_threshold_opaque[r06_minus_threshold_opaque.mask==False])
print len(t11_ts_minus_threshold)
args = {'title': "testcoldBrightCloudTest_All_SeaDayNoIce",
        'xlable': 'R06 minus dynamic threshold',
        'ylable': 'T11-Ts minus dynamic threshold',
        'xvector': r06_minus_threshold_opaque,
        'yvector': t11_ts_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD1 = OFFSETS['T11_OFFSET_SEA_DAY'] + -1*OFFSETS['QUALITY_MARGIN_T11TSUR']#-7.0-1.0
TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] + OFFSETS['QUALITY_MARGIN_TSUR']#

#100.0*threshold->r06*throff->sm_acmg_r06_gain_sea_opaque +
#      throff->sm_acmg_r06_offset_sea_opaque;
#100.0*threshold->r06*throff->sm_acmg_r06_gain_sea_opaque +
#      throff->sm_acmg_r06_offset_sea_opaque;
#/* The satellite reflectances are given in percent. Thus
#   multiply tabulated reflectances by 100.0!	*/
THRESHOLD2 = OFFSETS['R06_OFFSET_SEA_OPAQUE'] + OFFSETS['QUALITY_MARGIN_R06']
if RunWithOutMargins:
    THRESHOLD1 = OFFSETS['T11_OFFSET_SEA_DAY'] 
    TSUR_THRESHOLD = OFFSETS['COLDEST_SEASURFACE_TEMP'] 
    THRESHOLD2 = OFFSETS['R06_OFFSET_SEA_OPAQUE']
TestOk = np.logical_and(t11_ts_minus_threshold<THRESHOLD1,
                        r06_minus_threshold_opaque>THRESHOLD2)                        
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test_2_lim(args,isCloudyWaterDay, isClearWaterDay, TestOk, THRESHOLD1, THRESHOLD2)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)

#----------------------------------
#thinCirrusSecondaryTest sea day
#----------------------------------
print "thinCirrusSecondaryTest sea day no ice"
args = {'title': "thinCirrusSecondaryTest_All_SeaDayNoIce_lat",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY'] + OFFSETS['QUALITY_MARGIN_T11T12']#-7.0-1.0
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY'] 
TestOk = t11_t12_minus_threshold>THRESHOLD                        
plot_test(args,isCloudyWaterDay, isClearWaterDay, TestOk, THRESHOLD)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)
#also make plot with only cirrus
args['title'] = "thinCirrusSecondaryTest_ThinCirrus_SeaDayNoIce_lat"
plot_test(args,isCloudyCirrusWaterDay, isClearWaterDay, TestOk, THRESHOLD)
args['xlable'] ='Tsur'
args['xvector'] = surftemp
args['title'] = "thinCirrusSecondaryTest_ThinCirrus_SeaDayNoIce_tsur"
plot_test(args,isCloudyCirrusWaterDay, isClearWaterDay, TestOk, THRESHOLD)
#linear tsur dep threshold
args = {'title': "testThinCirrusPrimaryTest_All_SeaDayNoIce_lat_linearthreshold",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']+OFFSETS['QUALITY_MARGIN_T11T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']
THRESHOLD_V=THRESHOLD + (surftemp<305)*(surftemp>280)*(surftemp-280)*(THRESHOLD-1.5)/(305-280)+(surftemp>305)*(-1.5)
TestOk = args['yvector']>THRESHOLD_V
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyCirrusWaterDay,isClearWaterDay,TestOk,THRESHOLD)
args['title'] = "testThinCirrusSecondaryTest_All_SeaDayNoIce_lat_linearthreshold_1p5"
plot_test(args,isCloudyWaterDay,isClearWaterDay,TestOk,THRESHOLD)
args = {'title': "testThinCirrusPrimaryTest_All_SeaDayNoIce_lat_linearthreshold_1.0",
        'xlable': 'Latitude',
        'ylable': 'T11-T12 minus dynamic threshold',
        'xvector': latitude,
        'yvector': t11_t12_minus_threshold,
        'isCloudyPPS': isCloudyPPS,
        'isClearPPS': isClearPPS,   
}
THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']+OFFSETS['QUALITY_MARGIN_T11T12']#2.0+0.3
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']
THRESHOLD_V=THRESHOLD + (surftemp<305)*(surftemp>280)*(surftemp-280)*(THRESHOLD-1.0)/(305-280)+(surftemp>305)*(-1.0)
TestOk = args['yvector']>THRESHOLD_V
plot_test(args,isCloudyCirrusWaterDay,isClearWaterDay,TestOk,THRESHOLD)
args['title'] = "testThinCirrusSecondaryTest_All_SeaDayNoIce_lat_linearthreshold_10_margin02"
THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']+0.2
if RunWithOutMargins:
    THRESHOLD = OFFSETS['T11T12_OFFSET_SEA_DAY']
THRESHOLD_V=THRESHOLD + (surftemp<305)*(surftemp>280)*(surftemp-280)*(THRESHOLD-1.0)/(305-280)+(surftemp>305)*(-1.0)
TestOk = args['yvector']>THRESHOLD_V
plot_test(args,isCloudyCirrusWaterDay,isClearWaterDay,TestOk,THRESHOLD)

args['title'] = "testThinCirrusSecondaryTest_ThinCirrus_SeaDayNoIce_lat_modified_thr"
args['yvector'] =  t11t12 -0.75*thr_t11t12
TestOk = args['yvector']>THRESHOLD 
args['ylable'] = 'T11-T12 minus 0.75*dynamic threshold'
plot_test(args,isCloudyCirrusWaterDay, isClearWaterDay, TestOk, THRESHOLD)
plot_test(args,isCloudyWaterDay, isClearWaterDay, TestOk, THRESHOLD)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)
#----------------------------------
#notexistingCirrustest sea day
#----------------------------------
print "notexistingCirrustest sea day no ice"
args = {'title': "non_existingT11T37test_All_SeaDayNoIce_lat",
      'xlable': 'Latitude',
      'ylable': 'T11-T37 minus dynamic threshold',
      'xvector': latitude,
      'yvector': t11_t37_minus_threshold,
      'isCloudyPPS': isCloudyPPS,
      'isClearPPS': isClearPPS,   
}
THRESHOLD = 0.0
TestOk = t11_t37_minus_threshold>THRESHOLD
TestOkAll = keep_combined_ok(TestOk,TestOkAll)
plot_test(args,isCloudyWaterDay,isClearWaterDay,TestOk,THRESHOLD)
print_stats(cloudtype,isCloudyWaterDay,isClearWaterDay,isCloudyPPS,TestOkAll)


'3D'
fig = plt.figure()
ax = fig.gca(projection = '3d')
plt.plot(surftemp[isClearWaterDay == True],
         ciwv[isClearWaterDay == True], 
         t37_t12_minus_threshold[isClearWaterDay == True], 'bx')
plt.plot(surftemp[isCloudyWaterDay == True],
         ciwv[isCloudyWaterDay == True],
         t37_t12_minus_threshold[isCloudyWaterDay == True], 'r.')

#ax.legend()
#ax.set_xlim3d(0, 1)
#ax.set_ylim3d(0, 1)
#ax.set_zlim3d(-3, 10)
#ax.set_zlable('T37-T12')
#ax.set_ylable('Ciwv')
#ax.set_xlable('Tsur')
ax.set_title('T37-T12 minus t37-T12_threshold: \nblue clear, \nred-manga thin cirrus, \nmanga(detected by pps)')
#plt.show()

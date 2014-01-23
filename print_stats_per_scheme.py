#!/usr/bin/env python
# -*- coding: utf-8 -*-



"""Read all matched data and make some plotting of thresholds
"""

from glob import glob
import os.path
import os
import numpy as np
from scipy import histogram
import re
from pps_threshold_functions import (print_stats, 
                                 get_clear_and_cloudy_vectors)
from matchobject_io import (readCaliopAvhrrMatchObj,
                            CalipsoAvhrrTrackObject)

isLocalReception  = True
isACPGv2012=False
isGAC_v2012 = False
RunWithOutMargins=True
RunEdited= True
if isLocalReception and isACPGv2012:
    isACPGv2012=True
    isGAC=False
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20130911_2012_test2/Reshaped_Files/npp/1km/"
    ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20140103_v2012/Reshaped_Files/*/1km/"
    SATELLITE='npp_2012'
    files = glob(ROOT_DIR + "/????/??/arc*/*h5")
elif isLocalReception and  not isACPGv2012:
    isACPGv2012=False
    isGAC=False
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20130908_TEST1B_2/Reshaped_Files/npp/1km/"

    SATELLITE='npp'
    if RunEdited:
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM/Reshaped_Files/npp/1km/"
        #FewercasesROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_3_removeall_negativtest_correct_some_bugs/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_4_keep_low_quality_snow_abit_more_remove_bad_test_from_night_inv_sheme/Reshaped_Files/npp/1km/"
        
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_2/Reshaped_Files/npp/1km/"
        #ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_and_night_ice_2/Reshaped_Files/npp/1km/"
        #ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_and_night_ice_2/Reshaped_Files/npp/1km/"
	#ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_6_nightlandinv_landnightmount_and_night_ice_and_twilight_sea_ice_and_no_ice_and_night_coast_inv/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_8_shemes_10/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_12_and_half_shemes/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_12_and_half_shemes_18v2014coldtestsadded/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_12_and_half_shemes_18v2014coldtestsadded_sunz_thr_on_snow_tests_texture_and_ice_thr/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_12_and_half_shemes_18v2014coldtestsadded_sunz_thr_on_snow_tests_texture_and_ice_thr_all/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_2/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_2/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_coastalzone64percent_all/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_coastalzone0percent_4/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_coastalzone0percent_4_37cond_test_newlogic_day_Sea_tohre_rogh_limit/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_including_new_sst_coastalzone0percent_4_37cond_test_newlogic_day_Sea_tohre_rogh_limit_tuning4shcemes_4/Reshaped_Files/npp/1km/"
        ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20131014_Test_CM_ice_coast_int_ice_scheme_extratests_2_new_emiss_4_tuning_more_remove_one_seadaytest_second_3/Reshaped_Files/npp/1km/"
        #ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_early_val_final_tag_test1fgit_new_emisstiles/Reshaped_Files/npp/1km/"
    	#ROOT_DIR ="Reshaped_Files_2014/Reshaped_Files/npp6sh85/1km/"
        ROOT_DIR ="/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_20140116/Reshaped_Files/*/1km/"

        SATELLITE = 'npp_cm_edited'
    files = glob(ROOT_DIR + "/????/??/arc*/*h5")

elif isGAC_v2012:
    isGAC=True
    isACPGv2012=True
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_GAC_2012_el2010/Reshaped_Files/noaa18/5km/"
    files = glob(ROOT_DIR + "/????/??/cea*/*noaa18*h5")
    SATELLITE='avhrr18'
elif not isLocalReception and not isACPGv2012:
    isGAC=True
    isACPGv2012=False
    ROOT_DIR = "/local_disk/nina_pps/data_validation_ctth_patch_nov2012/VALIDATION_GAC_test1f/Reshaped_Files/noaa18/5km/"
    #ROOT_DIR ="Reshaped_Files_2014/Reshaped_Files/noaa18/5km/"
    files = glob(ROOT_DIR + "/????/??/cea*/*noaa18*h5")
    SATELLITE='avhrr18_v2014'


caObj = CalipsoAvhrrTrackObject()
for filename in files:
    print os.path.basename(filename)
    caObj = caObj + readCaliopAvhrrMatchObj(filename)
    
cloudObj = get_clear_and_cloudy_vectors(caObj, isACPGv2012, isGAC)
print cloudObj
all_schemes=cloudObj.isClear.all_arrays.keys()
all_schemes.sort()
for key in all_schemes:
    print key
    print_stats(key, caObj, cloudObj)
#    print_stats(cloudtype, cloudObj.isCloudy.all_arrays[key], cloudObj.isClear.all_arrays[key], isCloudyPPS,isClearPPS)
          

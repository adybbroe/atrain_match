"""Read all matched data and make some plotting
"""
import os
import re
from glob import glob
import numpy as np
from matchobject_io import (readCaliopAvhrrMatchObj,
                            CalipsoAvhrrTrackObject)
from plot_kuipers_on_area_util import (PerformancePlottingObject,
                                       ppsMatch_Imager_CalipsoObject)
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams.update({'font.size': 16})
from get_flag_info import get_calipso_clouds_of_type_i
from get_flag_info import (get_semi_opaque_info_pps2014,
                           get_calipso_high_clouds,
                           get_calipso_medium_clouds,
                           get_calipso_low_clouds)

def make_boxplot(caObj, name):
    low_clouds = get_calipso_low_clouds(caObj)
    high_clouds = get_calipso_high_clouds(caObj)
    medium_clouds = get_calipso_medium_clouds(caObj)
    height_c = (1000*caObj.calipso.all_arrays['layer_top_altitude'][:,0] - 
                caObj.calipso.all_arrays['elevation'])
    height_c1 = (1000*caObj.calipso.all_arrays['layer_top_altitude'][:,0] - 
                 caObj.calipso.all_arrays['elevation'])
    height_c2 = (1000*caObj.calipso.all_arrays['layer_top_altitude'][:,1] - 
                 caObj.calipso.all_arrays['elevation'])
    height_c3 = (1000*caObj.calipso.all_arrays['layer_top_altitude'][:,2] - 
                 caObj.calipso.all_arrays['elevation'])
    height_c4 = (1000*caObj.calipso.all_arrays['layer_top_altitude'][:,3] - 
                 caObj.calipso.all_arrays['elevation'])
    height_pps = caObj.avhrr.all_arrays['ctth_height']
    bias_1 =  height_pps - height_c1
    bias_2 =  height_pps - height_c2
    bias_3 =  height_pps - height_c3
    bias_4 =  height_pps - height_c4
    thin = np.logical_and(caObj.calipso.all_arrays['feature_optical_depth_532_top_layer_5km']<0.30, 
                          caObj.calipso.all_arrays['feature_optical_depth_532_top_layer_5km']>0) 
    very_thin = np.logical_and(caObj.calipso.all_arrays['feature_optical_depth_532_top_layer_5km']<0.10, 
                          caObj.calipso.all_arrays['feature_optical_depth_532_top_layer_5km']>0) 
    thin_top = np.logical_and(caObj.calipso.all_arrays['number_layers_found']>1, thin)
    thin_1_lay = np.logical_and(caObj.calipso.all_arrays['number_layers_found']==1, thin)
    #height_c[thin_top] =  height_c2[thin_top]
    #height_c[np.abs(bias_1)<np.abs(bias_2)] =  height_c1[np.abs(bias_1)<np.abs(bias_2)]
    #height_c[np.abs(bias_2)<np.abs(bias_1)] =  height_c2[np.abs(bias_2)<np.abs(bias_1)]
    #bias = height_pps - height_c
    #height_c[np.abs(bias_3)<np.abs(bias)] =  height_c3[np.abs(bias_3)<np.abs(bias)]
    #height_c[~thin_top] =  height_c1[~thin_top]
    #height_c[thin_top] =  height_c2[thin_top]

    
    
    use = np.logical_and(height_pps >-1,
                         caObj.calipso.all_arrays['layer_top_altitude'][:,0]>=0)
    use = np.logical_and(height_pps <45000,use)

    low = np.logical_and(low_clouds,use)
    medium = np.logical_and(medium_clouds,use)
    high = np.logical_and(high_clouds,use)
    c_all = np.logical_or(high,np.logical_or(low,medium))
    high_very_thin = np.logical_and(high, very_thin)
    high_thin = np.logical_and(high, np.logical_and(~very_thin,thin))
    high_thick = np.logical_and(high, ~thin)
    #print "thin, thick high", np.sum(high_thin), np.sum(high_thick) 
    bias = height_pps - height_c
    limit = np.percentile(bias[use],5)
    #print limit 
    abias = np.abs(bias)
    MAE = np.mean(abias[c_all])
    #abias[abias>2000]=2000
    print name.ljust(30, " "), "%3.1f"%(np.mean(abias[c_all])), "%3.1f"%(np.mean(abias[low])),"%3.1f"%(np.mean(abias[medium])),"%3.1f"%(np.mean(abias[high])), "%3.1f"%(limit)

    c_all = np.logical_or(np.logical_and(~very_thin,high),np.logical_or(low,medium))
    number_of = np.sum(c_all)
     
    #print name.ljust(30, " "), "%3.1f"%(np.sum(abias[c_all]<250)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<500)*100.0/number_of),  "%3.1f"%(np.sum(abias[c_all]<1000)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<1500)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<2000)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<3000)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<4000)*100.0/number_of), "%3.1f"%(np.sum(abias[c_all]<5000)*100.0/number_of)
    from matplotlib import rcParams
    rcParams.update({'figure.autolayout': True})
    fig = plt.figure(figsize = (6,9))        
    ax = fig.add_subplot(111)
    plt.xticks(rotation=70)
    #plt.tight_layout()
    #plt.subplots_adjust(left=0.2)
    #plt.subplots_adjust(left=10, bottom=10, right=10, top=10, wspace=0, hspace=0)

    ax.fill_between(np.arange(0,8),-500,500, facecolor='green', alpha=0.6)
    ax.fill_between(np.arange(0,8),-1000,1000, facecolor='green', alpha=0.4)
    ax.fill_between(np.arange(0,8),-1500,1500, facecolor='green', alpha=0.2)
    ax.fill_between(np.arange(0,8),2000,15000, facecolor='red', alpha=0.2)
    ax.fill_between(np.arange(0,8),-2000,-15000, facecolor='red', alpha=0.2)
    for y_val in [-5,-4,-3,-2,2,3,4,5]:
        plt.plot(np.arange(0,8), y_val*1000 + 0*np.arange(0,8),':k')
        plt.plot(np.arange(0,8), -10*1000 + 0*np.arange(0,8),':k')
    plt.plot(np.arange(0,8), 0 + 0*np.arange(0,8),'k')
    plt.boxplot([bias[low],bias[medium],bias[high],bias[high_thick],bias[high_thin],bias[high_very_thin]],whis=[5, 95],sym='',
                labels=["low","medium","high-all","high-thick\n od>0.4","high-thin \n 0.1<od<0.4","high-vthin\n od<0.1"],showmeans=True)
    ax.set_ylim(-14000,8000)
    plt.title("%s MAE = %3.0f"%(name,MAE))
    plt.savefig("/home/a001865/PICTURES_FROM_PYTHON/CTTH_LAPSE_RATE_INVESTIGATION/ctth_box_2018_plot_%s_5_95_filt.png"%(name))
    #plt.show()



def investigate_nn_ctth():
    ROOT_DIR_GAC_nnNina = ("/home/a001865/DATA_MISC/reshaped_files/"
                       "ATRAIN_RESULTS_GAC_nnNina/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn = ("/home/a001865/DATA_MISC/reshaped_files/"
                       "ATRAIN_RESULTS_GAC_nn21/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_old = ("/home/a001865/DATA_MISC/reshaped_files/"
                        "ATRAIN_RESULTS_GAC_old/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_oldCTTH_12x12 = ("/home/a001865/DATA_MISC/reshaped_files/"
                        "ATRAIN_RESULTS_GAC_oldCTTH_12x12/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_v2014 = ("/home/a001865/DATA_MISC/reshaped_files/"
                        "ATRAIN_RESULTS_GAC_v2014/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_v2014_12x12 = ("/home/a001865/DATA_MISC/reshaped_files/"
                                "ATRAIN_RESULTS_GAC_v2014_12x12/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn_new = ("/home/a001865/DATA_MISC/reshaped_files/"
                           "ATRAIN_RESULTS_GAC_nn20161125/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn_avhrr = ("/home/a001865/DATA_MISC/reshaped_files/"
                           "ATRAIN_RESULTS_GAC_nn20161130/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn_avhrr_tuned = ("/home/a001865/DATA_MISC/reshaped_files/"
                           "ATRAIN_RESULTS_GAC_tuned_nnAVHRR/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn_avhrr1_tuned = ("/home/a001865/DATA_MISC/reshaped_files/"
                           "ATRAIN_RESULTS_GAC_nnAVHRR1/Reshaped_Files/noaa18/")
    ROOT_DIR_GAC_nn_avhrr_with_gac = ("/home/a001865/DATA_MISC/reshaped_files/"
                           "ATRAIN_RESULTS_GAC_AVHRR_with_gac/Reshaped_Files/noaa18/")
    re_name = re.compile("_RESULTS_GAC_(\w+)\/")
    caobj_dict = {}
    for ROOT_DIR, name in zip([ROOT_DIR_GAC_nnNina, ROOT_DIR_GAC_nn, ROOT_DIR_GAC_old, ROOT_DIR_GAC_v2014, 
                               ROOT_DIR_GAC_nn_new, ROOT_DIR_GAC_nn_avhrr, 
                               ROOT_DIR_GAC_nn_avhrr_tuned, ROOT_DIR_GAC_nn_avhrr1_tuned, 
                               ROOT_DIR_GAC_v2014_12x12,
                               ROOT_DIR_GAC_oldCTTH_12x12,
                               ROOT_DIR_GAC_nn_avhrr_with_gac],
                              ["gac_nnLessIsMore","gac_nn21", "gac_CTTHold","gac_2014", 
                               "gac_nn20161125", "gac_nnAVHRR", 
                               "gac_nnAVHRR_tuned", "gac_nnAVHRR1_tuned", 
                               "gac_v2014_12x12","gac_CTTHold_12x12", "gac_17var_modis_noaa19"]):
        files = glob(ROOT_DIR + "5km/2009/*/*/*h5")
        caObj = CalipsoAvhrrTrackObject()
        for filename in files:
            caObj +=  readCaliopAvhrrMatchObj(filename) 
        caobj_dict[name] = caObj    
        make_boxplot(caObj, name) 
    #make_compare(caobj_dict['old'],caobj_dict['nn20161125'],'test')
    #make_compare(caobj_dict['nn20161130'],caobj_dict['nn20161125'],'test2')

def investigate_nn_ctth_viirs():
    ROOT_DIR_v2014 = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_v2014_20180110/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_v2018 = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_v2018_20180110/Reshaped_Files/npp/1km/2015/07/*/")
    #ROOT_DIR_14bug_maia = (
    #    "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
    #    "NPP_FULL_ORBIT_2014/Reshaped_Files/")
    ROOT_DIR_14bug = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_v2014_before_ctthbug_correction/"
        "Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_v2014_old = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_v2014_bug_corrected_20170313/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_avhrr = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnAVHRR_20170313/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_avhrr_tuned = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnAVHRR_20170313_tuned/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_avhrr1 = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnAVHRR1_20170313/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_viirs = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnVIIRS_20170310/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_viirs_new = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnVIIRS_20170313_new/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_viirs_CLAY4 = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_nnVIIRS_20170310_CLAY4/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_viirs_lm = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_viirs_lm/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_avhrr_lm = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_avhrr_lm/Reshaped_Files/npp/1km/2015/07/*/")
    ROOT_DIR_nn_avhrr_wg = (
        "/home/a001865/DATA_MISC/reshaped_files_jenkins_npp_modis/"
        "ATRAIN_RESULTS_NPP_AVHRR_with_gac/Reshaped_Files/npp/1km/2015/07/*/")
    caobj_dict = {}
    for ROOT_DIR, name in zip(
            [ROOT_DIR_v2014, ROOT_DIR_v2018, ROOT_DIR_nn_avhrr_wg, ROOT_DIR_nn_avhrr1,ROOT_DIR_nn_avhrr,ROOT_DIR_nn_avhrr_tuned, ROOT_DIR_v2014_old, ROOT_DIR_14bug, ROOT_DIR_nn_viirs, ROOT_DIR_nn_viirs_CLAY4, ROOT_DIR_nn_viirs_new,ROOT_DIR_nn_viirs_lm,ROOT_DIR_nn_avhrr_lm], 
            ["npp_CTTH-2014", "npp_CTTH-2018", "npp_CTTHnn_AVHRR_with_gac", "npp_CTTHnn_AVHRR1","npp_CTTHnn_AVHRR","npp_CTTHnn_AVHRR_tuned", "npp_CTTHv2014","npp_CTTHv2014_buggy","npp_CTTHnn_VIIRS","npp_CTTHnn_VIIRS_C4","npp_CTTHnn_VIIRS_tuned", "npp_nnVIIRS_LessIsMore", "npp_nnAVHRR_LessIsMore"]):
        print ROOT_DIR
        files = glob(ROOT_DIR + "*.h5")
        print files
        caObj = CalipsoAvhrrTrackObject()
        for filename in files:
            #print filename
            caObj +=  readCaliopAvhrrMatchObj(filename) 
        caobj_dict[name] = caObj    
        make_boxplot(caObj, name) 

def investigate_nn_ctth_modis_may():
   #november
    #may
    """
    ROOT_DIR_MODIS_nn = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_MAY/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_viirs = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_MAY_nnviirs_20161205/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_mersi2 = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_MAY_nnmersi2_20161206/Reshaped_Files/merged/")
    """
    ROOT_DIR_MODIS_old = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "global_modis_14th_created20161108/Reshaped_Files/merged/")

    caobj_dict = {}
    for ROOT_DIR, name in zip(
            [ROOT_DIR_MODIS_nn, ROOT_DIR_MODIS_nn_viirs, 
             ROOT_DIR_MODIS_nn_mersi2, ROOT_DIR_MODIS_old], 
            ["modis_november_CTTHnn_AVHRR",
             "modis_november_CTTHnn_VIIRS",
             "modis_november_CTTHnn_MERSI2",
             "modis_november_CTTHold"]):
        print name
        files = glob(ROOT_DIR + "/*11*.h5")
        caObj = CalipsoAvhrrTrackObject()
        for filename in files:
            #print filename
            caObj +=  readCaliopAvhrrMatchObj(filename) 
        caobj_dict[name] = caObj    
        make_boxplot(caObj, name) 
    #make_compare(caobj_dict["modis_nn18var"],
    #             caobj_dict["modis_CTTHold"],
    #             'compare_modis')


def investigate_nn_ctth_modis_november():
    #november
    ROOT_DIR_MODIS_nn_avhrr = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_viirs = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER_nnviirs_20161205/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_mersi2 = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER_AEROSOL/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_viirs_tuned = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER_nnVIIRS_20170315/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_mersi2_tuned = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER_nnMERSI2/Reshaped_Files/merged/")
    ROOT_DIR_MODIS_nn_avhrr_tuned = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "ATRAIN_RESULTS_MODIS_NOVEMBER_nnAVHRR_20170315/Reshaped_Files/merged/")

    ROOT_DIR_MODIS_old = (
        "/home/a001865/DATA_MISC/reshaped_files/"
        "global_modis_14th_created20161108/Reshaped_Files/merged/")

    caobj_dict = {}
    for ROOT_DIR, name in zip(
            [ROOT_DIR_MODIS_nn_avhrr, 
             ROOT_DIR_MODIS_nn_viirs, 
             ROOT_DIR_MODIS_nn_mersi2, 
             ROOT_DIR_MODIS_old,
             ROOT_DIR_MODIS_nn_viirs_tuned,  
             ROOT_DIR_MODIS_nn_mersi2_tuned,
             ROOT_DIR_MODIS_nn_avhrr_tuned], 
            ["modis_nov_nnAVHRR",
             "modis_nov_nnVIIRS",
             "modis_nov_nnMERSI2",
             "modis_nov_CTTHold",

             "modis_nov_nnVIIRS_tuned",
             "modis_nov_nnMERSI2_tuned",
             "modis_nov_nnAVHRR_tuned",
]):
        files = glob(ROOT_DIR + "/*11*.h5")
        caObj = CalipsoAvhrrTrackObject()
        for filename in files:
            #print filename
            caObj +=  readCaliopAvhrrMatchObj(filename) 
        caobj_dict[name] = caObj    
        make_boxplot(caObj, name) 
    #make_compare(caobj_dict["modis_nn18var"],
    #             caobj_dict["modis_CTTHold"],
    #             'compare_modis')

if __name__ == "__main__":
    #investigate_nn_ctth()
    #investigate_nn_ctth_modis_november() 
    investigate_nn_ctth_viirs()
  

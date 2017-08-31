#Program cloudsat_calipso_avhrr_statistics.py
import config
import sys
import logging
logger = logging.getLogger(__name__)
import numpy as np
from get_flag_info import (
    get_calipso_low_medium_high_classification,
    get_semi_opaque_info_pps2014, 
    get_semi_opaque_info_pps2012,
    get_sunglint_info_pps2014,
    get_high_terrain_info_pps2014,
    get_mountin_info_pps2014,
    get_inversion_info_pps2014,
    get_land_coast_sea_info_pps2014,
    get_land_coast_sea_info_pps2012,
    get_land_coast_sea_info_cci2014,
    get_ice_info_pps2014,
    get_ice_info_pps2012,
    get_day_night_twilight_info_pps2014,
    get_day_night_twilight_info_pps2012,
    get_day_night_twilight_info_cci2014,
    get_day_night_twilight_info_maia,
    get_sunglint_info_pps2012,
    get_mountin_info_pps2012,
    get_inversion_info_pps2012)

def calculate_ctth_stats(val_subset, imager_ctth_m_above_seasurface,caliop_max_height):
    avhrr_height_work = np.repeat(imager_ctth_m_above_seasurface[::],val_subset)
    caliop_max_height_work = np.repeat(caliop_max_height[::],val_subset)
    if len(caliop_max_height_work) > 0:
        if len(avhrr_height_work) > 20:
            corr_caliop_avhrr = np.corrcoef(caliop_max_height_work,
                                            avhrr_height_work)[0,1]
        else:
            corr_caliop_avhrr = -99.0
        diff = avhrr_height_work-caliop_max_height_work
        bias = np.mean(diff)
        diff_squared = diff*diff
        RMS_difference = np.sqrt(np.mean(diff_squared))
        diff_squared_biascorr = (diff-bias)*(diff-bias)
#        RMS_difference_biascorr = np.sqrt(np.mean(diff_squared_biascorr))
    else:
        corr_caliop_avhrr = -9.0
        bias = -9.0
        RMS_difference = -9.0
#        RMS_difference_biascorr = -9.0
        diff_squared_biascorr = np.array([-9.0])
    #return (corr_caliop_avhrr,bias,RMS_difference,avhrr_height_work,diff_squared_biascorr)
    return "%3.2f %3.2f %3.2f %s %3.2f "%(corr_caliop_avhrr,bias,RMS_difference,len(avhrr_height_work),sum(diff_squared_biascorr))

def get_subset_for_mode(caObj, mode):
  # First prepare possible subsetting of CALIOP datasets according to NSIDC
    # and IGBP surface types  
    if mode == 'ICE_COVER_SEA':
        cal_subset = np.logical_and(
            np.logical_and(np.less_equal(caObj.calipso.nsidc_surface_type,100),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.equal(caObj.calipso.igbp_surface_type,17))
    elif mode == 'ICE_FREE_SEA':
        cal_subset = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),np.equal(caObj.calipso.igbp_surface_type,17))
    elif mode == 'SNOW_COVER_LAND':
        cal_subset = np.logical_and(
            np.logical_and(np.less(caObj.calipso.nsidc_surface_type,104),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.not_equal(caObj.calipso.igbp_surface_type,17))
        # Notice that some uncertainty remains about the meaning of IGBP category 15 = "snow and ice". Can this possibly include also the Arctic ice sheet? We hope that it is not!!! However, if it is, the whole classification here might be wrong since this will affect also the definition of IGBP category 17./KG 
    elif mode == 'SNOW_FREE_LAND':
        cal_subset = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                    np.not_equal(caObj.calipso.igbp_surface_type,17))
    elif mode == 'COASTAL_ZONE':
        cal_subset = np.equal(caObj.calipso.nsidc_surface_type,255)
    
    elif mode == 'TROPIC_ZONE':
        cal_subset = np.abs(caObj.calipso.latitude) <= 10
    elif mode == 'TROPIC_ZONE_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                        np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) <= 10
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'TROPIC_ZONE_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                        np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) <= 10
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    
    elif mode == 'SUB_TROPIC_ZONE':
        cal_subset = np.logical_and((np.abs(caObj.calipso.latitude) > 10), 
                                    (np.abs(caObj.calipso.latitude) <= 45))    
    elif mode == 'SUB_TROPIC_ZONE_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and((np.abs(caObj.calipso.latitude) > 10), 
                                        (np.abs(caObj.calipso.latitude) <= 45))
        cal_subset_area = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                         np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'SUB_TROPIC_ZONE_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and((np.abs(caObj.calipso.latitude) > 10), 
                                        (np.abs(caObj.calipso.latitude) <= 45))
        cal_subset_area = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                         np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    
    elif mode == 'HIGH-LATITUDES':
        cal_subset = np.logical_and((np.abs(caObj.calipso.latitude) > 45), 
                                    (np.abs(caObj.calipso.latitude) <= 75))
    elif mode == 'HIGH-LATITUDES_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                        np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.logical_and((np.abs(caObj.calipso.latitude) > 45), 
                                         (np.abs(caObj.calipso.latitude) <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_SNOW_COVER_LAND':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less(caObj.calipso.nsidc_surface_type,104),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.logical_and((np.abs(caObj.calipso.latitude) > 45), (np.abs(caObj.calipso.latitude) <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                        np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.logical_and((np.abs(caObj.calipso.latitude) > 45), 
                                         (np.abs(caObj.calipso.latitude) <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'HIGH-LATITUDES_ICE_COVER_SEA':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less_equal(caObj.calipso.nsidc_surface_type,100),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.logical_and((np.abs(caObj.calipso.latitude) > 45), 
                                         (np.abs(caObj.calipso.latitude) <= 75))
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    
    
    elif mode == 'POLAR':
        cal_subset = np.abs(caObj.calipso.latitude) > 75
    elif mode == 'POLAR_SNOW_FREE_LAND':
        cal_subset_lat = np.logical_and(np.equal(caObj.calipso.nsidc_surface_type,0),
                                        np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_SNOW_COVER_LAND':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less(caObj.calipso.nsidc_surface_type,104),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.not_equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_ICE_FREE_SEA':
        cal_subset_lat = np.logical_and(
            np.equal(caObj.calipso.nsidc_surface_type,0),np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    elif mode == 'POLAR_ICE_COVER_SEA':
        cal_subset_lat = np.logical_and(
            np.logical_and(np.less_equal(caObj.calipso.nsidc_surface_type,100),
                           np.greater(caObj.calipso.nsidc_surface_type,10)),
            np.equal(caObj.calipso.igbp_surface_type,17))
        cal_subset_area = np.abs(caObj.calipso.latitude) > 75
        cal_subset = np.logical_and(cal_subset_lat, cal_subset_area)
    
    elif mode == 'BASIC':
        cal_subset = np.bool_(np.ones(caObj.calipso.igbp_surface_type.shape))
    elif mode == 'OPTICAL_DEPTH':
        cal_subset = np.bool_(np.ones(caObj.calipso.igbp_surface_type.shape))
    elif mode == 'STANDARD':
        cal_subset = np.bool_(np.ones(caObj.calipso.igbp_surface_type.shape))
    elif mode == 'OPTICAL_DEPTH_THIN_IS_CLEAR':
        cal_subset = np.bool_(np.ones(caObj.calipso.igbp_surface_type.shape))
    else:
        print('The mode %s is not added in statistic file' %mode)
        sys.exit()
    return cal_subset     

def get_day_night_info(cObj):
    daynight_flags = None
    cObj_imager = getattr(cObj, 'avhrr') #Same as cObj.avhrr
    cObj_truth_sat= getattr(cObj, cObj.truth_sat) #cObj.calipso or cObj.iss
    if config.CCI_CLOUD_VALIDATION or config.MAIA_CLOUD_VALIDATION:
        daynight_flags = get_day_night_twilight_info_cci2014(
        cObj_imager.sunz)
    if config.PPS_VALIDATION and  hasattr(cObj_imager, 'cloudtype_qflag'):
        if cObj_imager.cloudtype_qflag is not None:
            daynight_flags = get_day_night_twilight_info_pps2012(
                cObj_imager.cloudtype_qflag)
    if config.PPS_VALIDATION and  hasattr(cObj_imager, 'cloudtype_conditions'):
        if cObj_imager.cloudtype_conditions is not None:
            daynight_flags = get_day_night_twilight_info_pps2014(
                cObj_imager.cloudtype_conditions)     
    if config.PPS_VALIDATION and daynight_flags is None:
        daynight_flags = get_day_night_twilight_info_cci2014(
        cObj_imager.sunz)
    (no_qflag, night_flag, twilight_flag, day_flag, all_dnt_flag) = daynight_flags
    if (no_qflag.sum() + night_flag.sum() + twilight_flag.sum() + day_flag.sum()) != cObj_truth_sat.longitude.size:          
        print('something wrong with quality flags. It does not sum up. See beginning of statistic file')
        sys.exit()
    return daynight_flags
    
def get_semi_opaque_info(caObj):
    semi_flag = None    
    opaque_flag = None
    if hasattr(caObj.avhrr, 'cloudtype_qflag'):
        #print caObj.avhrr.ctth_opaque
        if caObj.avhrr.ctth_opaque is not None:
            semi_flag, opaque_flag = get_semi_opaque_info_pps2012(
                caObj.avhrr.ctth_opaque) 
    if hasattr(caObj.avhrr, 'cloudtype_conditions'):
        if caObj.avhrr.ctth_status is not None:
            #print caObj.avhrr.ctth_status
            semi_flag, opaque_flag = get_semi_opaque_info_pps2014(
                caObj.avhrr.ctth_status)
    return semi_flag, opaque_flag


def print_cloudsat_stats(clsatObj, statfile):
    cloudsat_cloud_mask=clsatObj.cloudsat.CPR_Cloud_mask
    cloudsat_cloud_mask=np.greater_equal(cloudsat_cloud_mask, 
                                         config.CLOUDSAT_CLOUDY_THR)
    cloudsat_cloud_fraction=np.zeros(clsatObj.cloudsat.latitude.shape[0])
    sum_cloudsat_cloud_mask = np.sum(cloudsat_cloud_mask, axis=1)
    if len(sum_cloudsat_cloud_mask) != (len(cloudsat_cloud_fraction)):
        raise ValueError('Boolean index-array should have same lenght as array!')
    cloudsat_cloud_fraction[sum_cloudsat_cloud_mask > 2] = 1 # requires at least two cloudy bins
    cloudsat_clear =  np.less(cloudsat_cloud_fraction,1)
    cloudsat_cloudy = np.greater_equal(cloudsat_cloud_fraction,1)
    #what version of pps_cloudtype is this not before 2012!
    pps_clear = np.logical_and(np.less_equal(clsatObj.avhrr.cloudtype,4),
                               np.greater(clsatObj.avhrr.cloudtype,0))
    pps_cloudy = np.logical_and(np.greater(clsatObj.avhrr.cloudtype,4),
                                np.less(clsatObj.avhrr.cloudtype,20))
    n_clear_clear = np.repeat(
        pps_clear, np.logical_and(cloudsat_clear,pps_clear)).shape[0]
    n_cloudy_cloudy = np.repeat(
        pps_cloudy,np.logical_and(cloudsat_cloudy,pps_cloudy)).shape[0]
    n_clear_cloudy = np.repeat(
        pps_cloudy,np.logical_and(cloudsat_clear,pps_cloudy)).shape[0]
    n_cloudy_clear = np.repeat(
        pps_clear,np.logical_and(cloudsat_cloudy,pps_clear)).shape[0]
        
    nclear = np.repeat(cloudsat_clear,cloudsat_clear).shape[0]
    ncloudy = np.repeat(cloudsat_cloudy,cloudsat_cloudy).shape[0]
    ncloudy_pps = n_cloudy_cloudy+n_clear_cloudy
    nclear_pps = n_cloudy_clear+n_clear_clear
    
    if ncloudy > 0:
        pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    else:
        pod_cloudy = -9.0
    if ncloudy_pps > 0:
        far_cloudy = float(n_clear_cloudy)/ncloudy_pps
    else:
        far_cloudy = -9.0

    if nclear > 0:
        pod_clear = float(n_clear_clear)/nclear
    else:
        pod_clear = -9.0
    if nclear_pps > 0:
        far_clear = float(n_cloudy_clear)/nclear_pps
    else:
        far_clear = -9.0
    
    mean_cloudsat=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
    mean_pps=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
    bias=mean_pps-mean_cloudsat
    statfile.write("CLOUD MASK CLOUDSAT-PPS TABLE: %s %s %s %s \n" % (n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
    statfile.write("CLOUD MASK CLOUDSAT-PPS PROB: %f %f %f %f %f \n" % (pod_cloudy,pod_clear,far_cloudy,far_clear,bias))


def print_cloudsat_modis_stats(clsatObj, statfile):
    modis_clear = np.logical_or(
        np.equal(clsatObj.cloudsat.MODIS_cloud_flag,1),
        np.equal(clsatObj.cloudsat.MODIS_cloud_flag,0))
    modis_cloudy = np.logical_or(
        np.equal(clsatObj.cloudsat.MODIS_cloud_flag,3),
        np.equal(clsatObj.cloudsat.MODIS_cloud_flag,2))
    cloudsat_cloud_mask=clsatObj.cloudsat.CPR_Cloud_mask
    cloudsat_cloud_mask=np.greater_equal(cloudsat_cloud_mask, 
                                         config.CLOUDSAT_CLOUDY_THR)
    cloudsat_cloud_fraction=np.zeros(clsatObj.cloudsat.latitude.shape[0])
    sum_cloudsat_cloud_mask = np.sum(cloudsat_cloud_mask, axis=1)
    if len(sum_cloudsat_cloud_mask) != (len(cloudsat_cloud_fraction)):
        raise ValueError('Boolean index-array should have same lenght as array!')
    cloudsat_cloud_fraction[sum_cloudsat_cloud_mask > 2] = 1 # requires at least two cloudy bins
    cloudsat_clear =  np.less(cloudsat_cloud_fraction,1)
    cloudsat_cloudy = np.greater_equal(cloudsat_cloud_fraction,1)

    n_clear_clear = np.repeat(
        modis_clear, np.logical_and(cloudsat_clear,modis_clear)).shape[0]
    n_cloudy_cloudy = np.repeat(
        modis_cloudy, np.logical_and(cloudsat_cloudy,modis_cloudy)).shape[0]
    n_clear_cloudy = np.repeat(
        modis_cloudy, np.logical_and(cloudsat_clear,modis_cloudy)).shape[0]
    n_cloudy_clear = np.repeat(
        modis_clear, np.logical_and(cloudsat_cloudy,modis_clear)).shape[0]
        
    nclear = np.repeat(cloudsat_clear,cloudsat_clear).shape[0]
    ncloudy = np.repeat(cloudsat_cloudy,cloudsat_cloudy).shape[0]
    ncloudy_modis = n_cloudy_cloudy+n_clear_cloudy
    nclear_modis = n_cloudy_clear+n_clear_clear
        
    if ncloudy > 0:
        pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    else:
        pod_cloudy = -9.0
    if ncloudy_modis > 0:
        far_cloudy = float(n_clear_cloudy)/ncloudy_modis
    else:
        far_cloudy = -9.0

    if nclear > 0:
        pod_clear = float(n_clear_clear)/nclear
    else:
        pod_clear = -9.0
    if nclear_modis > 0:
        far_clear = float(n_cloudy_clear)/nclear_modis
    else:
        far_clear = -9.0

    mean_cloudsat=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
    mean_modis=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
    bias=mean_modis-mean_cloudsat
    statfile.write("CLOUD MASK CLOUDSAT-MODIS TABLE: %s %s %s %s \n" % (n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
    statfile.write("CLOUD MASK CLOUDSAT-MODIS FROM CLOUDSAT FLAG POD-CLOUDY:  %3.2f \n" % (pod_cloudy*100))
    statfile.write("CLOUD MASK CLOUDSAT-MODIS FROM CLOUDSAT FLAG POD-CLEAR:   %3.2f \n" % (pod_clear)*100)
    statfile.write("CLOUD MASK CLOUDSAT-MODIS FROM CLOUDSAT FLAG FAR-CLOUDY:  %3.2f \n" % (far_cloudy*100))
    statfile.write("CLOUD MASK CLOUDSAT-MODIS FROM CLOUDSAT FLAG FAR-CLEAR:   %3.2f \n" % (far_clear*100))
    statfile.write("CLOUD MASK CLOUDSAT-MODIS FROM CLOUDSAT FLAG BIAS percent: %3.2f \n" % ( bias*100)) 



def print_calipso_cmask_stats(caObj, statfile, val_subset):
    # CLOUD MASK EVALUATION
    #=======================    
    # CORRELATION CLOUD MASK: CALIOP/ISS - IMAGER

    cObj_truth_sat = getattr(caObj, caObj.truth_sat)

    calipso_clear = np.logical_and(
        np.less(cObj_truth_sat.cloud_fraction,config.CALIPSO_CLEAR_MAX_CFC),val_subset)
    calipso_cloudy = np.logical_and(
        np.greater(cObj_truth_sat.cloud_fraction,config.CALIPSO_CLOUDY_MIN_CFC),val_subset)        
    # For the combined 1km + 5km dataset cloud_fraction can only have values (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). So the threshold should
    # really be set to 0.4, i.e., at least two 1 km columns should be cloudy!. 
    
    pps_clear = np.logical_and(np.logical_and(np.less_equal(caObj.avhrr.cloudtype,4),np.greater(caObj.avhrr.cloudtype,0)),val_subset)
    pps_cloudy = np.logical_and(np.logical_and(np.greater(caObj.avhrr.cloudtype,4),np.less(caObj.avhrr.cloudtype,20)),val_subset)
    if config.USE_CMA_FOR_CFC_STATISTICS:
        pps_clear = np.logical_or(np.equal(caObj.avhrr.cloudmask,3),
                                  np.equal(caObj.avhrr.cloudmask,0))
        pps_cloudy = np.logical_or(np.equal(caObj.avhrr.cloudmask,1),
                                   np.equal(caObj.avhrr.cloudmask,2))
    
    n_clear_clear = np.repeat(
        pps_clear,np.logical_and(calipso_clear,pps_clear)).shape[0]
    n_cloudy_cloudy = np.repeat(
        pps_cloudy,np.logical_and(calipso_cloudy,pps_cloudy)).shape[0]
    n_clear_cloudy = np.repeat(
        pps_cloudy,np.logical_and(calipso_clear,pps_cloudy)).shape[0]
    n_cloudy_clear = np.repeat(
        pps_clear,np.logical_and(calipso_cloudy,pps_clear)).shape[0]
    nclear = np.repeat(calipso_clear,calipso_clear).shape[0]
    ncloudy = np.repeat(calipso_cloudy,calipso_cloudy).shape[0]
    ncloudy_pps = n_cloudy_cloudy+n_clear_cloudy
    nclear_pps = n_cloudy_clear+n_clear_clear
    
    
    if ncloudy > 0:
        pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    else:
        pod_cloudy = -9.0
    if ncloudy_pps > 0:
        far_cloudy = float(n_clear_cloudy)/ncloudy_pps
    else:
        far_cloudy = -9.0
    if nclear > 0:
        pod_clear = float(n_clear_clear)/nclear
    else:
        pod_clear = -9.0
    if nclear_pps > 0:
        far_clear = float(n_cloudy_clear)/nclear_pps
    else:
        far_clear = -9.0
    
    if (n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy) > 0:
        mean_caliop=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        mean_pps=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
        bias=mean_pps-mean_caliop
    else:
        bias = -9.0
    statfile.write("CLOUD MASK %s-IMAGER TABLE: %s %s %s %s \n" % (caObj.truth_sat.upper(), n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
    #statfile.write("CLOUD MASK %s-IMAGER PROB:%3.2f \n" % (caObj.truth_sat.upper(), pod_cloudy,pod_clear,far_cloudy,far_clear,bias))
    statfile.write("CLOUD MASK %s-IMAGER POD-CLOUDY: %3.2f \n" % (caObj.truth_sat.upper(), pod_cloudy*100))
    statfile.write("CLOUD MASK %s-IMAGER POD-CLEAR:  %3.2f \n" %  (caObj.truth_sat.upper(), pod_clear*100))
    statfile.write("CLOUD MASK %s-IMAGER FAR-CLOUDY: %3.2f \n" % (caObj.truth_sat.upper(), far_cloudy*100))
    statfile.write("CLOUD MASK %s-IMAGER FAR-CLEAR:  %3.2f \n" %  (caObj.truth_sat.upper(), far_clear*100))
    statfile.write("CLOUD MASK %s-IMAGER BIAS percent: %3.2f \n" %  (caObj.truth_sat.upper(), bias*100))

def print_calipso_modis_stats(caObj, statfile, val_subset, cal_MODIS_cflag):    
    # CORRELATION CLOUD MASK: CALIOP - MODIS
    calipso_clear = np.logical_and(np.less(caObj.calipso.cloud_fraction,0.34),
                                   val_subset)
    calipso_cloudy = np.logical_and(
        np.greater(caObj.calipso.cloud_fraction,0.66),val_subset)
    if cal_MODIS_cflag is not None:
        modis_clear = np.logical_and(
            np.logical_or(np.equal(cal_MODIS_cflag,1),
                          np.equal(cal_MODIS_cflag,0)),val_subset)
        modis_cloudy = np.logical_and(
            np.logical_or(np.equal(cal_MODIS_cflag,3),
                          np.equal(cal_MODIS_cflag,2)),val_subset)

    if cal_MODIS_cflag is not None:
        n_clear_clear = np.repeat(
            modis_clear,
            np.logical_and(calipso_clear,modis_clear)).shape[0]
        n_cloudy_cloudy = np.repeat(
            modis_cloudy,
            np.logical_and(calipso_cloudy,modis_cloudy)).shape[0]
        n_clear_cloudy = np.repeat(
            modis_cloudy,
            np.logical_and(calipso_clear,modis_cloudy)).shape[0]
        n_cloudy_clear = np.repeat(
            modis_clear,
            np.logical_and(calipso_cloudy,modis_clear)).shape[0]
        nclear = np.repeat(calipso_clear,calipso_clear).shape[0]
        ncloudy = np.repeat(calipso_cloudy,calipso_cloudy).shape[0]
        ncloudy_modis = n_cloudy_cloudy+n_clear_cloudy
        nclear_modis = n_cloudy_clear+n_clear_clear
            
        if ncloudy > 0:
            pod_cloudy = float(n_cloudy_cloudy)/ncloudy
        else:
            pod_cloudy = -9.0
        if ncloudy_modis > 0:
            far_cloudy = float(n_clear_cloudy)/ncloudy_modis
        else:
            far_cloudy = -9.0

        if nclear > 0:
            pod_clear = float(n_clear_clear)/nclear
        else:
            pod_clear = -9.0
        if nclear_modis > 0:
            far_clear = float(n_cloudy_clear)/nclear_modis
        else:
            far_clear = -9.0

        if (n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy) > 0:
            mean_caliop=((n_clear_clear+n_clear_cloudy)*0.0 + (n_cloudy_clear+n_cloudy_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
            mean_modis=((n_clear_clear+n_cloudy_clear)*0.0 + (n_cloudy_cloudy+n_clear_cloudy)*1.0)/(n_clear_clear+n_clear_cloudy+n_cloudy_clear+n_cloudy_cloudy)
            bias=mean_modis-mean_caliop
        else:
            bias=-9.0
        statfile.write("CLOUD MASK CALIOP-MODIS TABLE: %s %s %s %s \n" % (n_clear_clear,n_clear_cloudy,n_cloudy_clear,n_cloudy_cloudy))
        #statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG PROB: %f %f %f %f %f \n" % (pod_cloudy,pod_clear,far_cloudy,far_clear,bias))
        statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG POD-CLOUDY:  %3.2f \n" % (pod_cloudy*100))
        statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG POD-CLEAR:   %3.2f \n" % (pod_clear*100))
        statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG FAR-CLOUDY:  %3.2f \n" % (far_cloudy*100))
        statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG FAR-CLEAR:   %3.2f \n" % (far_clear*100))
        statfile.write("CLOUD MASK CALIOP-MODIS FROM CLOUDSAT FLAG BIAS percent: %3.2f \n" % ( bias*100))    
 
    
def print_calipso_stats_ctype(caObj, statfile, val_subset, low_medium_high_class):
    if config.CCI_CLOUD_VALIDATION :
        logger.info("Cloudtype validation not useful for CCI validation")
        return
    
    # CLOUD TYPE EVALUATION - Based exclusively on CALIPSO data (Vertical Feature Mask)
    # =======================
    calipso_low = np.logical_and(low_medium_high_class['low_clouds'],
                                 val_subset)
    calipso_medium = np.logical_and(low_medium_high_class['medium_clouds'],
                                    val_subset)
    calipso_high = np.logical_and(low_medium_high_class['high_clouds'],
                                 val_subset)

    if  caObj.avhrr.cloudtype_conditions is not None: 
        logger.info("Assuming cloudtype structure from pps v2014")
        avhrr_low = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,5),
                           np.less_equal(caObj.avhrr.cloudtype,6)),
            val_subset)
        avhrr_medium = np.logical_and(
            np.equal(caObj.avhrr.cloudtype,7), val_subset)
        avhrr_high_op = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,8),
                           np.less_equal(caObj.avhrr.cloudtype,9)),
            val_subset)
        avhrr_high_semi = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,11),
                           np.less_equal(caObj.avhrr.cloudtype,15)),
            val_subset)
        avhrr_high = np.logical_or(avhrr_high_op,avhrr_high_semi)
        avhrr_frac = np.logical_and(np.equal(caObj.avhrr.cloudtype,10), 
                                    val_subset)

    else:
        logger.info("Assuming cloudtype structure from pps v2012")
        avhrr_low = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,5),
                           np.less_equal(caObj.avhrr.cloudtype,8)),
            val_subset)
        avhrr_medium = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,9),
                           np.less_equal(caObj.avhrr.cloudtype,10)),
            val_subset)
        avhrr_high = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,11),
                           np.less_equal(caObj.avhrr.cloudtype,18)),
            val_subset)
        avhrr_frac = np.logical_and(
            np.logical_and(np.greater_equal(caObj.avhrr.cloudtype,19),
                           np.less_equal(caObj.avhrr.cloudtype,19)),
            val_subset)

    calipso_clear = np.logical_and(
        np.less(caObj.calipso.cloud_fraction,0.34),val_subset)
    calipso_cloudy = np.logical_and(
        np.greater(caObj.calipso.cloud_fraction,0.66),val_subset)
    avhrr_clear = np.logical_and(
        np.logical_and(np.less_equal(caObj.avhrr.cloudtype,4),
                       np.greater(caObj.avhrr.cloudtype,0)),
        val_subset)
    
    
    # Notice that we have unfortunately changed order in notation compared to cloud mask
    # Here the PPS category is mentioned first and then the CALIOP category 

    n_low_low = np.repeat(
        avhrr_low,
        np.logical_and(calipso_low,avhrr_low)).shape[0]
    n_low_medium = np.repeat(
        avhrr_low,
        np.logical_and(calipso_medium,avhrr_low)).shape[0]
    n_low_high = np.repeat(
        avhrr_low,
        np.logical_and(calipso_high,avhrr_low)).shape[0]
    n_medium_low = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_low,avhrr_medium)).shape[0]
    n_medium_medium = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_medium,avhrr_medium)).shape[0]
    n_medium_high = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_high,avhrr_medium)).shape[0]
    n_high_low = np.repeat(
        avhrr_high, 
        np.logical_and(calipso_low,avhrr_high)).shape[0]
    n_high_medium = np.repeat(
        avhrr_high,
        np.logical_and(calipso_medium,avhrr_high)).shape[0]
    n_high_high = np.repeat(
        avhrr_high,
        np.logical_and(calipso_high,avhrr_high)).shape[0]
    n_frac_low = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_low,avhrr_frac)).shape[0]
    n_frac_medium = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_medium,avhrr_frac)).shape[0]
    n_frac_high = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_high,avhrr_frac)).shape[0]

    n_clear_low = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_low,avhrr_clear)).shape[0]
    n_clear_medium = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_medium,avhrr_clear)).shape[0]
    n_clear_high = np.repeat(
        avhrr_clear,
        np.logical_and(calipso_high,avhrr_clear)).shape[0]
    n_low_clear = np.repeat(
        avhrr_low,
        np.logical_and(calipso_clear,avhrr_low)).shape[0]
    n_medium_clear = np.repeat(
        avhrr_medium,
        np.logical_and(calipso_clear,avhrr_medium)).shape[0]
    n_high_clear = np.repeat(
        avhrr_high,
        np.logical_and(calipso_clear,avhrr_high)).shape[0]
    n_frac_clear = np.repeat(
        avhrr_frac,
        np.logical_and(calipso_clear,avhrr_frac)).shape[0]

    if (n_low_low+n_medium_low+n_high_low+n_frac_low) > 0:
        pod_low = float(n_low_low + n_frac_low)/(n_low_low+n_medium_low+n_high_low+n_frac_low)
        far_low = float(n_medium_low+n_high_low)/(n_low_low+n_medium_low+n_high_low+n_frac_low)
    else:
        pod_low = -9.0
        far_low = -9.0
    if (n_low_medium+n_medium_medium+n_high_medium+n_frac_medium) > 0:
        pod_medium = float(n_medium_medium)/(n_low_medium+n_medium_medium+n_high_medium+n_frac_medium)
        far_medium = float(n_low_medium+n_high_medium+n_frac_medium)/(n_low_medium+n_medium_medium+n_high_medium+n_frac_medium)
    else:
        pod_medium =-9.0
        far_medium =-9.0
    if (n_low_high+n_medium_high+n_high_high+n_frac_high) > 0:
        pod_high = float(n_high_high)/(n_low_high+n_medium_high+n_high_high+n_frac_high)
        far_high = float(n_low_high+n_medium_high+n_frac_high)/(n_low_high+n_medium_high+n_high_high+n_frac_high)
    else:
        pod_high =-9.0
        far_high =-9.0

    statfile.write("CLOUD TYPE %s-IMAGER TABLE: %s %s %s %s %s %s %s %s %s %s %s %s \n" % (caObj.truth_sat.upper(),n_low_low,n_low_medium,n_low_high,n_medium_low,n_medium_medium,n_medium_high,n_high_low,n_high_medium,n_high_high,n_frac_low,n_frac_medium,n_frac_high))
    statfile.write("CLOUD TYPE %s-IMAGER PROB: %f %f %f %f %f %f \n" % (caObj.truth_sat.upper(),pod_low,pod_medium,pod_high,far_low,far_medium,far_high))
    statfile.write("CLOUD TYPE %s-IMAGER TABLE MISSED: %s %s %s %s %s %s %s \n" % (caObj.truth_sat.upper(),n_clear_low,n_clear_medium,n_clear_high,n_low_clear,n_medium_clear,n_high_clear,n_frac_clear))
            

def print_cloudsat_stats_ctop(clsatObj, statfile):

    # CLOUD TOP EVALUATION
    #=======================
    imager_ctth_m_above_seasurface = clsatObj.avhrr.imager_ctth_m_above_seasurface
    # CORRELATION: CLOUDSAT - AVHRR HEIGHT
    
    #print "STATISTICS CLOUD TOP HEIGHT: CLOUDSAT - AVHRR"
    clsat_max_height = -9 + 0*np.zeros(clsatObj.cloudsat.latitude.shape)
    
    for i in range(125):
        height = clsatObj.cloudsat.Height[:,i]
        cmask_ok = clsatObj.cloudsat.CPR_Cloud_mask[:,i]
        top_height = height+120
        #top_height[height<240*4] = -9999 #Do not use not sure why these are not used Nina 20170317
        is_cloudy = cmask_ok > config.CLOUDSAT_CLOUDY_THR
        top_height[~is_cloudy] = -9999
        clsat_max_height[clsat_max_height<top_height] =  top_height[clsat_max_height<top_height] 

    okarr = np.greater_equal(imager_ctth_m_above_seasurface,0.0)
    okarr = np.logical_and(okarr,np.greater_equal(clsat_max_height,0.0))
    out_stats = calculate_ctth_stats(okarr,imager_ctth_m_above_seasurface,
                                     clsat_max_height)  
    #statfile.write("CLOUD HEIGHT CLOUDSAT: %s \n" % (out_stats))

    print_height_all_low_medium_high("CLOUDSAT", okarr,  statfile, 
                                     None, imager_ctth_m_above_seasurface,
                                     clsat_max_height)

def print_height_all_low_medium_high(NAME, val_subset,  statfile, 
                                     low_medium_high_class, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height):

    out_stats = calculate_ctth_stats(val_subset,imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height)
    statfile.write("CLOUD HEIGHT %s ALL: %s\n" %(NAME, out_stats))
    if low_medium_high_class is None:
        #Nothing more can be done!
        return
    cal_low_ok = np.logical_and(low_medium_high_class['low_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_low_ok,imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height)   
    statfile.write("CLOUD HEIGHT %s LOW: %s \n" % (NAME, out_stats))
    cal_mid_ok = np.logical_and(low_medium_high_class['medium_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_mid_ok, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height)   
    statfile.write("CLOUD HEIGHT %s MEDIUM: %s \n" % (NAME, out_stats))
    cal_high_ok = np.logical_and(low_medium_high_class['high_clouds'],
                                 val_subset)
    out_stats = calculate_ctth_stats(cal_high_ok, imager_ctth_m_above_seasurface,
                                     truth_sat_validation_height) 
    statfile.write("CLOUD HEIGHT %s HIGH: %s \n" % (NAME, out_stats))

def print_calipso_stats_ctop(cObj, statfile, val_subset, low_medium_high_class):

    # CORRELATION: CALIOP - IMAGER HEIGHT
    # FIRST TOTAL FIGURES

    cObj_imager = getattr(cObj, 'avhrr') #Same as cObj.avhrr
    cObj_truth_sat= getattr(cObj, cObj.truth_sat) #cObj.calipso or cObj.iss
    imager_ctth_m_above_seasurface = cObj_imager.imager_ctth_m_above_seasurface  
    truth_sat_validation_height = cObj_truth_sat.validation_height

    both_have_heights = np.logical_and(
        np.greater_equal(truth_sat_validation_height,0),
        np.greater_equal(imager_ctth_m_above_seasurface,0))
    val_subset = np.logical_and(both_have_heights, val_subset)
 
    #print "ALL CLOUDS:" 
    print_height_all_low_medium_high(cObj.truth_sat.upper(),
                                     val_subset, 
                                     statfile, low_medium_high_class, 
                                     imager_ctth_m_above_seasurface, truth_sat_validation_height)
    
    if "CALIPSO" not in cObj.truth_sat.upper():
        print "WARNING WARNING WARNING only printing over all statistics for cloudtop for ISS"
        return
    if config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC:
        statfile.write("CLOUD HEIGHT SINGLE-LAYER\n")
        val_subset_single = np.logical_and(
            val_subset, 
            np.equal(cObj.calipso.number_layers_found,1)) 
        print_height_all_low_medium_high("CALIOP-SINGLE-LAYER", 
                                         val_subset_single,
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)

    if (config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC and
        (config.ALSO_USE_5KM_FILES or config.RESOLUTION==5)): 
        statfile.write("CLOUD HEIGHT SINGLE-LAYER, NOT THIN\n")
        lim=2*config.OPTICAL_DETECTION_LIMIT
        val_subset_single_not_thinnest = np.logical_and(
            val_subset_single, 
            np.greater_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-SINGLE-LAYER>%f"%(lim), 
                                         val_subset_single_not_thinnest,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
        
        statfile.write("CLOUD HEIGHT NOT VERY THIN TOP LAYER\n")
        lim=config.OPTICAL_DETECTION_LIMIT
        val_subset_not_thinnest_top_layer = np.logical_and(
            val_subset, 
            np.greater_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-TOP-LAYER>%f"%(lim), 
                                         val_subset_not_thinnest_top_layer,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)

        lim=config.OPTICAL_DETECTION_LIMIT
        statfile.write("CLOUD HEIGHT VERY THIN TOP LAYER\n")
        val_subset_thinnest_top_layer = np.logical_and(
            val_subset, 
            np.less_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-TOP-LAYER<=%f"%(lim), 
                                         val_subset_thinnest_top_layer,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
           
    """    
    if (config.COMPILE_RESULTS_SEPARATELY_FOR_SEMI_AND_OPAQUE and 
        semi_flag is not None and
        opaque_flag is not None):
            
        #Opaque stats
        statfile.write("CLOUD HEIGHT OPAQUE\n")
        val_subset_opaque_pps = np.logical_and(val_subset, opaque_flag)
        print_height_all_low_medium_high("CALIOP-OPAQUE", 
                                         val_subset_opaque_pps,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)

        #Semi-transparent stats
        statfile.write("CLOUD HEIGHT SEMI\n")
        val_subset_semi_pps = np.logical_and(val_subset, semi_flag)
        print_height_all_low_medium_high("CALIOP-SEMI", 
                                         val_subset_semi_pps,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)


    if (config.COMPILE_RESULTS_SEPARATELY_FOR_SINGLE_LAYERS_ETC and
        (config.ALSO_USE_5KM_FILES or config.RESOLUTION==5) and
        config.COMPILE_RESULTS_SEPARATELY_FOR_SEMI_AND_OPAQUE and 
        semi_flag is not None and
        opaque_flag is not None):
            
        #Thin top layer
        #Opaque stats
        lim=config.OPTICAL_DETECTION_LIMIT
        statfile.write("CLOUD HEIGHT OPAQUE TOP LAYER VERY NOT-THIN\n")
        val_subset_opaque_pps_not_thin = np.logical_and(
            np.logical_and(val_subset, opaque_flag),
            np.greater(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-OPAQUE-TOP-LAYER>%f"%(lim), 
                                         val_subset_opaque_pps_not_thin,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
        #Semi-transparent stats
        statfile.write("CLOUD HEIGHT SEMI TOP LAYER VERY NOT-THIN\n")
        val_subset_semi_pps_not_thin = np.logical_and(
            np.logical_and(val_subset, semi_flag),
            np.greater(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-SEMI-TOP-LAYER>%f"%(lim), 
                                         val_subset_semi_pps_not_thin,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
        #Not thin top layer
        #Opaque stats
        lim=config.OPTICAL_DETECTION_LIMIT
        statfile.write("CLOUD HEIGHT OPAQUE TOP LAYER VERY THIN\n")
        val_subset_opaque_pps_thin = np.logical_and(
            np.logical_and(val_subset, opaque_flag),
            np.less_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-OPAQUE-TOP-LAYER<=%f"%(lim), 
                                         val_subset_opaque_pps_thin,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
        #Semi-transparent stats
        statfile.write("CLOUD HEIGHT SEMI TOP LAYER VERY THIN\n")
        val_subset_semi_pps_thin = np.logical_and(
            np.logical_and(val_subset, semi_flag),
            np.less_equal(cObj.calipso.feature_optical_depth_532_top_layer_5km,lim))
        print_height_all_low_medium_high("CALIOP-SEMI-TOP-LAYER<=%f"%(lim), 
                                         val_subset_semi_pps_thin,  
                                         statfile, low_medium_high_class, 
                                         imager_ctth_m_above_seasurface, truth_sat_validation_height)
    """
def print_main_stats(cObj, statfile):
    val_object = getattr(cObj,cObj.truth_sat)
    num_val_data_ok = len(getattr(val_object,'elevation'))
    statfile.write("%s min and max time diff: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),
        cObj.diff_sec_1970.min(),
        cObj.diff_sec_1970.max()))

    statfile.write("%s start and stop Latitude: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),
        val_object.latitude[0],
        val_object.latitude[-1]))

    statfile.write("%s start and stop Longitude: %3.2f %3.2f \n" %(
        cObj.truth_sat.upper(),                            
        val_object.longitude[0],
        val_object.longitude[-1]))

    statfile.write("%s-IMAGER number of matches: %d\n"%(
        cObj.truth_sat.upper(), 
        num_val_data_ok))


def CalculateStatistics(mode, statfilename, caObj, clsatObj, issObj,
                        dnt_flag=None):


    import sys

    if clsatObj is not None:
        #curretnly only mode BASIC
        statfile = open(statfilename.replace('xxx','cloudsat'),"w")
        print_main_stats(clsatObj, statfile)
        print_cloudsat_stats(clsatObj, statfile)
        print_cloudsat_stats_ctop(clsatObj, statfile)
        statfile.close()
    
    if caObj is not None:
        statfile = open(statfilename.replace('xxx','calipso'),"w")
        cal_MODIS_cflag = caObj.calipso.cal_MODIS_cflag
        val_subset = get_subset_for_mode(caObj, mode)
        low_medium_high_class = get_calipso_low_medium_high_classification(caObj)

        semi_flag, opaque_flag = get_semi_opaque_info(caObj)
        (no_qflag, night_flag, twilight_flag, day_flag, all_dnt_flag) = get_day_night_info(caObj)

        if dnt_flag is None:
            print('dnt_flag = %s' %'NO DNT FLAG -> ALL PIXELS')
            val_subset = np.logical_and(val_subset, all_dnt_flag)
        elif dnt_flag.upper() == 'DAY':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, day_flag)
        elif dnt_flag.upper() == 'NIGHT':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, night_flag)
        elif dnt_flag.upper() == 'TWILIGHT':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, twilight_flag)
        else:
            print('dnt_flag = %s' %dnt_flag.upper())
            print('statistic calculation is not prepared for this dnt_flag')
            sys.exit()

        print_main_stats(caObj, statfile)
        print_calipso_cmask_stats(caObj, statfile, val_subset)
        print_calipso_modis_stats(caObj, statfile, val_subset, cal_MODIS_cflag)
        print_calipso_stats_ctype(caObj, statfile, val_subset, low_medium_high_class)
        print_calipso_stats_ctop(caObj, statfile, val_subset, low_medium_high_class) 
        statfile.close()
    
    if issObj is not None:
        statfile = open(statfilename.replace('xxx','iss'),"w")
        val_subset = np.bool_(np.ones(issObj.iss.elevation.shape))

        #""" Currently only CFC statistics

        #semi_flag, opaque_flag = get_semi_opaque_info(issObj)
        (no_qflag, night_flag, twilight_flag, day_flag, all_dnt_flag) = get_day_night_info(issObj)

        if dnt_flag is None:
            print('dnt_flag = %s' %'NO DNT FLAG -> ALL PIXELS')
            val_subset = np.logical_and(val_subset, all_dnt_flag)
        elif dnt_flag.upper() == 'DAY':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, day_flag)
        elif dnt_flag.upper() == 'NIGHT':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, night_flag)
        elif dnt_flag.upper() == 'TWILIGHT':
            print('dnt_flag = %s' %dnt_flag.upper())
            val_subset = np.logical_and(val_subset, twilight_flag)
        else:
            print('dnt_flag = %s' %dnt_flag.upper())
            print('statistic calculation is not prepared for this dnt_flag')
            sys.exit()
        #"""    
        print_main_stats(issObj, statfile)
        print_calipso_cmask_stats(issObj, statfile, val_subset)
        #print_calipso_stats_ctype(issObj, statfile, val_subset, cal_vert_feature)
        print_calipso_stats_ctop(issObj, statfile, val_subset, None)
        statfile.close()

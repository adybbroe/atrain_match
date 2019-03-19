"""
  Use this module to read patmosx cloudproducts
  2018 SMHI, N.Hakansson a001865
"""

import time
import os
import netCDF4
import numpy as np
import calendar
from datetime import datetime
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)

from imager_cloud_products.read_cloudproducts_and_nwp_pps import (CtypeObj, CtthObj, CmaObj,
                                            createImagerTime,
                                            imagerAngObj, imagerGeoObj)
from utils.runutils import do_some_geo_obj_logging
import config 
ATRAIN_MATCH_NODATA = config.NODATA
#from utils.get_flag_info import get_patmosx_ct_flag, get_day_night_twilight_info_patmosx

def get_satid_datetime_orbit_from_fname_patmosx(imager_filename, SETTINGS, cross):
    # Get satellite name, time, and orbit number from imager_file
    # patmosx_v05r03_NOAA-18_asc_d20090102_c20140317.nc 
    #patmosx_noaa-18_des_2009_122.level2b.hdf

    sl_ = os.path.basename(imager_filename).split('_')
    if ".nc" in imager_filename:
        date_time = datetime.strptime(sl_[4], 'd%Y%m%d')
    else:
        date_time = datetime.strptime(sl_[3]+sl_[4], '%Y%j.level2b.hdf')
    asc_or_des = "asc"
    if "_des_" in imager_filename:
        asc_or_des = "des"

    date_time = cross.time
    #date_time_end = cross.time + timedelta(seconds=SETTINGS['SAT_ORBIT_DURATION'])

    sat_id = sl_[2].replace('-','').lower()
    values = {"satellite": sat_id,
              "date_time": date_time,
              "orbit": "99999",
              "date": date_time.strftime("%Y%m%d"),
              "year": date_time.year,
              "month": "%02d" % (date_time.month),
              "time": date_time.strftime("%H%M"),
              "extrai": asc_or_des,
              #"basename":sat_id + "_" + date_time.strftime("%Y%m%d_%H%M_99999"),#"20080613002200-ESACCI",
              "ccifilename": imager_filename,
              "ppsfilename": None}
    values['basename'] = values["satellite"] + "_" + \
        values["date"] + "_" + values["time"] + "_" + values["orbit"] + "_" + asc_or_des
    return values

def patmosx_read_all(filename, Cross, SETTINGS):
    if ".nc" in filename:
        return patmosx_read_all_nc(filename, Cross, SETTINGS)
    else:   
        return patmosx_read_all_hdf(filename, Cross, SETTINGS)

def patmosx_read_all_nc(filename, Cross, SETTINGS):
    """Read geolocation, angles info, ctth, and cma
    """
    patmosx_nc = netCDF4.Dataset(filename, 'r', format='NETCDF4')
    logger.info("Opening file %s", filename)
    logger.info("Reading angles ...")
    imagerAngObj = read_patmosx_angobj(patmosx_nc)
    logger.info("Reading cloud type ...")
    # , imagerAngObj)
    ctype, cma, ctth = read_patmosx_ctype_cmask_ctth(patmosx_nc)
    logger.info("Reading longitude, latitude and time ...")
    imagerGeoObj = read_patmosx_geoobj(patmosx_nc, filename, Cross, SETTINGS)
    logger.info("Not reading surface temperature")
    surft = None
    logger.info("Not reading cloud microphysical properties")
    cpp = None
    logger.info("Not reading channel data")
    imagerObj = None
    return imagerAngObj, ctth, imagerGeoObj, ctype,  imagerObj, surft, cpp, cma

def read_patmosx_ctype_cmask_ctth(patmosx_nc):
    """Read cloudtype and flag info from filename
    """
    ctth = CtthObj()
    ctype = CtypeObj()
    cma = CmaObj()
    ctth.height = patmosx_nc.variables['cld_height_acha'][0,:,:].astype(np.float)
    ctth.h_nodata = patmosx_nc.variables['cld_height_acha']._FillValue
    if np.ma.is_masked(ctth.height):     
        ctth.height.data[ctth.height.mask]  = ATRAIN_MATCH_NODATA
        ctth.height = ctth.height.data
    ctth.height = 1000*ctth.height
    cf = patmosx_nc.variables['cloud_fraction'][0,:,:].astype(np.float)
    cma.cma_ext = np.where(cf>=0.5, 1, 0)
    if np.ma.is_masked(cf):
       cma.cma_ext[cf.mask] = 255 
    ctype.phaseflag = None
    ctype.ct_conditions = None
    return ctype, cma, ctth


def read_patmosx_angobj(patmosx_nc):
    """Read angles info from filename
    """
    AngObj = imagerAngObj()
    AngObj.satz.data = patmosx_nc.variables['sensor_zenith_angle'][0,:,:].astype(np.float)
    AngObj.sunz.data = patmosx_nc.variables['solar_zenith_angle'][0,:,:].astype(np.float)
    AngObj.azidiff.data = None
    return AngObj



def read_patmosx_geoobj(patmosx_nc, filename, cross, SETTINGS):
    """Read geolocation and time info from filename
    """
    GeoObj = imagerGeoObj()
    latitude_v = patmosx_nc.variables['latitude'][:].astype(np.float)
    longitude_v = patmosx_nc.variables['longitude'][:].astype(np.float)
    GeoObj.latitude = np.repeat(latitude_v[:,np.newaxis], len(longitude_v), axis=1)
    GeoObj.longitude = np.repeat(longitude_v[np.newaxis,:], len(latitude_v), axis=0)
    GeoObj.nodata=-999
    date_time_start = cross.time
    date_time_end = cross.time + timedelta(seconds=SETTINGS['SAT_ORBIT_DURATION'])
    GeoObj.sec1970_start = calendar.timegm(date_time_start.timetuple())
    GeoObj.sec1970_end = calendar.timegm(date_time_end.timetuple())
    frac_hour = patmosx_nc.variables['scan_line_time'][0,:,:].astype(np.float)
    if np.ma.is_masked(frac_hour):
        frac_hour = frac_hour.data
    seconds = frac_hour*60*60.0
    GeoObj.time = seconds +  patmosx_nc.variables['time']
    do_some_geo_obj_logging(GeoObj)
    return GeoObj


def patmosx_read_all_hdf(filename, Cross, SETTINGS):
    """Read geolocation, angles info, ctth, and cma
    """
    from pyhdf.SD import SD, SDC
    from pyhdf.HDF import HDF, HC
    import pyhdf.VS 
    patmosx_hdf = SD(filename, SDC.READ)
    logger.info("Opening file %s", filename)
    logger.info("Reading angles ...")
    imagerAngObj = read_patmosx_angobj_hdf(patmosx_hdf)
    logger.info("Reading cloud type ...")
    # , imagerAngObj)
    ctype, cma, ctth = read_patmosx_ctype_cmask_ctth_hdf(patmosx_hdf)
    logger.info("Reading longitude, latitude and time ...")
    imagerGeoObj = read_patmosx_geoobj_hdf(patmosx_hdf, filename, Cross, SETTINGS)
    logger.info("Not reading surface temperature")
    surft = None
    logger.info("Not reading cloud microphysical properties")
    cpp = None
    logger.info("Not reading channel data")
    imagerObj = None
    return imagerAngObj, ctth, imagerGeoObj, ctype,  imagerObj, surft, cpp, cma

def read_patmosx_ctype_cmask_ctth_hdf(patmosx_hdf):
    """Read cloudtype and flag info from filename
    """
    ctth = CtthObj()
    ctype = CtypeObj()
    cma = CmaObj()
    name = 'cld_height_acha'
    height_unscaled =  np.array(patmosx_hdf.select(name).get())
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    ctth.height = height_unscaled * gain + offset
    ctth.h_nodata = patmosx_hdf.select(name)._FillValue
    #ctth.height = 1000*ctth.height
    ctth.height[height_unscaled==ctth.h_nodata] = ATRAIN_MATCH_NODATA
    name = 'cloud_fraction'
    cf_unscaled =  np.array(patmosx_hdf.select(name).get())
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    cf = cf_unscaled * gain + offset
    cf[cf_unscaled== patmosx_hdf.select(name)._FillValue] =  ATRAIN_MATCH_NODATA
    cma.cma_ext = np.where(cf>=0.5, 1, 0)
    ctype.phaseflag = None
    ctype.ct_conditions = None
    return ctype, cma, ctth


def read_patmosx_angobj_hdf(patmosx_hdf):
    """Read angles info from filename
    """
    AngObj = imagerAngObj()
    name = 'sensor_zenith_angle'
    temp = patmosx_hdf.select(name).get().astype(np.float)
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    AngObj.satz.data =  temp * gain + offset
    
    name = 'solar_zenith_angle' 
    temp = patmosx_hdf.select(name).get().astype(np.float)
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    AngObj.sunz.data = temp * gain + offset
    AngObj.azidiff.data = None
    return AngObj



def read_patmosx_geoobj_hdf(patmosx_hdf, filename, cross, SETTINGS):
    """Read geolocation and time info from filename
    """
    GeoObj = imagerGeoObj()
    name = 'latitude'
    temp = patmosx_hdf.select(name).get().astype(np.float)
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    latitude_v = temp * gain + offset
    name = 'longitude'
    temp = patmosx_hdf.select(name).get().astype(np.float)
    offset = patmosx_hdf.select(name).attributes()['add_offset']
    gain = patmosx_hdf.select(name).attributes()['scale_factor']
    longitude_v = temp * gain + offset

    GeoObj.latitude = np.repeat(latitude_v[:,np.newaxis], len(longitude_v), axis=1)
    GeoObj.longitude = np.repeat(longitude_v[np.newaxis,:], len(latitude_v), axis=0)
    GeoObj.nodata=-999
    date_time_start = cross.time
    date_time_end = cross.time + timedelta(seconds=SETTINGS['SAT_ORBIT_DURATION'])
    GeoObj.sec1970_start = calendar.timegm(date_time_start.timetuple())
    GeoObj.sec1970_end = calendar.timegm(date_time_end.timetuple())
    frac_hour = patmosx_hdf.select('scan_line_time').get().astype(np.float)
    if np.ma.is_masked(frac_hour):
        frac_hour = frac_hour.data
    seconds = frac_hour*60*60.0
    time_s = patmosx_hdf.attributes()['time_coverage_start']
    dt_obj = datetime.strptime(time_s, "%Y-%m-%dT%H:%M:%SZ")
    time_sec_1970 =  calendar.timegm(dt_obj.timetuple())
    GeoObj.time = seconds +  time_sec_1970
    do_some_geo_obj_logging(GeoObj)
    return GeoObj


if __name__ == "__main__":
    pass

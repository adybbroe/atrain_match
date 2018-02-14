"""
  Use this module to read cci cloudproducts
  2013 SMHI, N.Hakansson a001865
"""
from read_cloudproducts_and_nwp_pps import (CtypeObj, CtthObj, CppObj, CmaObj, 
                                            imagerAngObj, imagerGeoObj)
import os
import netCDF4	
import numpy as np
import calendar
import datetime 
import logging
logger = logging.getLogger(__name__)
import time
from config import NODATA
ATRAIN_MATCH_NODATA = NODATA
#import h5py
#from mpop.satin.nwcsaf_pps import NwcSafPpsChannel
def get_satid_datetime_orbit_from_fname_cci(avhrr_filename):
    # Get satellite name, time, and orbit number from avhrr_file
    #avhrr_file = "20080613002200-ESACCI-L2_CLOUD-CLD_PRODUCTS-AVHRRGAC-NOAA18-fv1.0.nc"
    sl_ = os.path.basename(avhrr_filename).split('-')
    date_time = datetime.datetime.strptime(sl_[0], '%Y%m%d%H%M%S')
    
    sat_id = "noaa18"#sl_[5]_lower,
    values= {"satellite": sat_id,
             "date_time": date_time,
             "orbit": "99999",
             "date":date_time.strftime("%Y%m%d"),
             "year":date_time.year,
             "month":"%02d"%(date_time.month),    
             "time":date_time.strftime("%H%M"),
             #"basename":sat_id + "_" + date_time.strftime("%Y%m%d_%H%M_99999"),#"20080613002200-ESACCI",
             "ccifilename":avhrr_filename,
             "ppsfilename":None}
    values['basename'] = values["satellite"] + "_" + values["date"] + "_" + values["time"] + "_" + values["orbit"]
    return values

def daysafter4713bc_to_sec1970(bcdate_array):
    """Translating days after 4713bc 12:00 to sec since 1970
    """
    #import pps_time_util #@UnresolvedImport
    #first date if several in the file, swath at midnight   
    bcdate = np.min(bcdate_array)
    # days since 4713 bc 12:00:00
    ddays = np.floor(bcdate)
    #seconds after 12:00:00 
    dseconds = np.floor(24*60*60*(bcdate-ddays))
    mseconds = np.floor(10**6*(24*60*60*(bcdate-ddays)-dseconds))
    # to avoid too large numbers count from 1950-01-01 12:00
    # time datetime.datetime(1950, 1, 1, 12, 0,0,0) == julian day 2433283
    ddays = ddays-2433283

    time_delta = datetime.timedelta(days=ddays, seconds=dseconds, 
                                    microseconds = mseconds)
    the_time = datetime.datetime(1950, 1, 1, 12, 0,0,0) + time_delta
    sec_1970 = calendar.timegm(the_time.timetuple()) + the_time.microsecond/(1.0*10**6)
    sec_1970_array = 24*60*60*(bcdate_array - bcdate) + sec_1970
    return sec_1970_array

def cci_read_all(filename):
    """Read geolocation, angles info, ctth, and cloudtype
    """
    #cci_nc = netCDF4.Dataset(filename, 'r', format='NETCDF4')
    #dir(cci_nc)
    #cci_nc.variables
    #cci_nc.variables['cth'].add_offset
    #cci_nc.variables['cth'][:] 
    #cci_nc.variables['cth'].scale_factor
    logger.info("Opening file %s"%(filename))
    cci_nc = netCDF4.Dataset(filename, 'r', format='NETCDF4')
    logger.info("Reading ctth ...")
    ctth = read_cci_ctth(cci_nc)
    logger.info("Reading angles ...")
    avhrrAngObj = read_cci_angobj(cci_nc)
    logger.info("Reading cloud type ...")
    cma = read_cci_cma(cci_nc, avhrrAngObj)
    logger.info("Reading longitude, latitude and time ...")
    avhrrGeoObj = read_cci_geoobj(cci_nc)
    logger.info("Not reading surface temperature")
    surft = None
    logger.info("Reading cloud phase")
    cpp = read_cci_phase(cci_nc)
    logger.info("Not reading channel data")
    avhrrObj = None  
    if cci_nc:
        cci_nc.close()
    ctype = None    
    return avhrrAngObj, ctth, avhrrGeoObj, ctype, avhrrObj, surft, cpp, cma 


def cci_read_prod(filename, prod_type='ctth'):
    """Read geolocation, angles info, ctth, and cloudtype
    """
    #cci_nc = netCDF4.Dataset(filename, 'r', format='NETCDF4')
    #dir(cci_nc)
    #cci_nc.variables
    #cci_nc.variables['cth'].add_offset
    #cci_nc.variables['cth'][:] 
    #cci_nc.variables['cth'].scale_factor
    logger.info("Opening file %s"%(filename))
    cci_nc = netCDF4.Dataset(filename, 'r', format='NETCDF4')
    if prod_type == 'ctth':
        logger.info("Reading ctth ...")
        retv = read_cci_ctth(cci_nc)
        if cci_nc:
            cci_nc.close()
        return retv
    if prod_type == 'ang':
        logger.info("Reading angles ...")
        retv =  read_cci_angobj(cci_nc)
        if cci_nc:
            cci_nc.close()
        return retv    
    if prod_type == 'ctype': 
        logger.info("Reading angles ...")
        avhrrAngObj =  read_cci_angobj(cci_nc)
        logger.info("Reading cloud type ...")
        retv = read_cci_cma(cci_nc, avhrrAngObj)
        if cci_nc:
            cci_nc.close()
        return  retv
    if prod_type == 'geotime':      
        logger.info("Reading longitude, latitude and time ...")
        retv = read_cci_geoobj(cci_nc)
        if cci_nc:
            cci_nc.close()
        return retv
    if prod_type == 'phase':  
        logger.info("Reading cloud phase")
        retv = read_cci_phase(cci_nc)
        if cci_nc:
            cci_nc.close()
        return retv    
    return None

def read_cci_cma(cci_nc, avhrrAngObj):
    """Read cloudtype and flag info from filename
    """
    cma = CmaObj()
    #cci_nc.variables['cc_total'][:])
    #cci_nc.variables['ls_flag'][:])
    #ctype = CtypeObj()
    #pps 0 cloudfree 3 cloudfree snow 1: cloudy, 2:cloudy
    #cci lsflag 0:sea 1:land
    cma.cma_ext = 0*cci_nc.variables['lsflag'][::]
    cma.cma_ext[cci_nc.variables['cc_total'][::]>0.5] = 1
    #ctype.landseaflag = cci_nc.variables['lsflag'][::]
    return cma

def read_cci_angobj(cci_nc):
    """Read angles info from filename
    """
    avhrrAngObj = imagerAngObj()
    avhrrAngObj.satz.data = cci_nc.variables['satellite_zenith_view_no1'][::] 
    avhrrAngObj.sunz.data = cci_nc.variables['solar_zenith_view_no1'][::]
    avhrrAngObj.azidiff = None #cci_nc.variables['rel_azimuth_view_no1']??
    return avhrrAngObj
def read_cci_phase(cci_nc):
    """Read angles info from filename
    """
    cpp_obj = CppObj()
    data = cci_nc.variables['phase'][::] 
    setattr(cpp_obj, 'cpp_phase', data)
    #if hasattr(phase, 'mask'):
    #    phase_out = np.where(phase.mask, -999, phase.data)
    #else:
    #    phase_out = phase.data
    #print phase    
    return cpp_obj

def read_cci_geoobj(cci_nc):
    """Read geolocation and time info from filename
    """
    GeoObj = imagerGeoObj()
    logger.info("Min lon: %s, max lon: %d"%(
            np.min(cci_nc.variables['lon'][::]),np.max(cci_nc.variables['lon'][::])))
    #cci_nc.variables['lon'].add_offset
    #GeoObj.longitude = cci_nc.variables['lon'][::]
    GeoObj.nodata = -999.0
    in_fillvalue = cci_nc.variables['lon']._FillValue
    GeoObj.longitude = cci_nc.variables['lon'][::]
    GeoObj.longitude[cci_nc.variables['lon'][::] == in_fillvalue] = GeoObj.nodata
    GeoObj.latitude = cci_nc.variables['lon'][::]
    GeoObj.latitude[cci_nc.variables['lon'][::] == in_fillvalue] = GeoObj.nodata
    np.where(
        np.logical_and(
            np.greater_equal(cci_nc.variables['lon'][::],
                             cci_nc.variables['lon'].valid_min),
            np.less_equal(cci_nc.variables['lon'][::],
                          cci_nc.variables['lon'].valid_max)),
        cci_nc.variables['lon'][::],
        GeoObj.nodata)
    #GeoObj.latitude = cci_nc.variables['lat'][::] 
    GeoObj.latitude = np.where(
        np.logical_and(
            np.greater_equal(cci_nc.variables['lat'][::],
                             cci_nc.variables['lat'].valid_min),
            np.less_equal(cci_nc.variables['lat'][::],
                          cci_nc.variables['lat'].valid_max)),
        cci_nc.variables['lat'][::],
        GeoObj.nodata)
    #cci_nc.variables['lon'].scale_factor
    #cci_nc.variables['lat'].add_offset

    #cci_nc.variables['lat'].scale_factor
    #for pps these are calculated in calipso.py, but better read them
    # from file because time are already available on arrays in the netcdf files
    #dsec = calendar.timegm((1993,1,1,0,0,0,0,0,0)) #TAI to UTC
    time_temp = daysafter4713bc_to_sec1970(cci_nc.variables['time'][::])
    GeoObj.time = time_temp[::]#[:,0] #time_temp[:,0]

    GeoObj.sec1970_start = np.min(GeoObj.time)  
    GeoObj.sec1970_end = np.max(GeoObj.time)

    tim1 = time.strftime("%Y%m%d %H:%M", 
                         time.gmtime(GeoObj.sec1970_start))
    tim2 = time.strftime("%Y%m%d %H:%M", 
                         time.gmtime(GeoObj.sec1970_end))
    logger.info("Starttime: %s, end time: %s"%(tim1, tim2))
    logger.info("Min lon: %f, max lon: %d"%(
            np.min(np.where(
                    np.equal(GeoObj.longitude, GeoObj.nodata),
                    99999,
                    GeoObj.longitude)),
            np.max(GeoObj.longitude)))
    logger.info("Min lat: %d, max lat: %d"%(
            np.min(GeoObj.latitude),np.max(GeoObj.latitude)))

    return  GeoObj

def read_cci_ctth(cci_nc):
    """Read cloud top: temperature, height and pressure from filename
    """
    ctth = CtthObj()
    cth = cci_nc.variables['cth'][::]
    if hasattr(cth, 'mask'):
        cth_data = np.where(cth.mask, ATRAIN_MATCH_NODATA, cth.data)
    else:
        cth_data = cth.data # already scaled!
    
    ctth.h_gain = 1.0
    ctth.h_intercept = 0.0
    ctth.h_nodata = ATRAIN_MATCH_NODATA
    data = (1/ctth.h_gain)*(1000*cth_data-ctth.h_intercept) #*1000 data in km
    ctth.height = 1000*cth_data
        
    ctt = cci_nc.variables['ctt'][::]
    if hasattr(ctt, 'mask'):
        ctt_data = np.where(ctt.mask, ATRAIN_MATCH_NODATA, ctt.data)
    else:
        ctt_data = ctt.data
    #*cci_nc.variables['cth'].scale_factor+cci_nc.variables['cth'].add_offset)
    ctth.t_gain = 1.0
    ctth.t_intercept = 0.0
    ctth.t_nodata = ATRAIN_MATCH_NODATA
    ctth.temperature = ctt_data
    
    ctp = cci_nc.variables['ctp'][::]
    if hasattr(ctp, 'mask'):
        ctp_data = np.where(ctp.mask,  ATRAIN_MATCH_NODATA, ctp.data)#Upscaled
    else:
        ctp_data = ctp.data
    #*cci_nc.variables['cth'].scale_factor+cci_nc.variables['cth'].add_offset)
    ctth.p_gain = 1.0
    ctth.p_intercept = 0.0
    ctth.p_nodata =  ATRAIN_MATCH_NODATA
    ctth.pressure =  ctp_data

    return ctth

if __name__ == "__main__":
    filename="20080613002200-ESACCI-L2_CLOUD-CLD_PRODUCTS-AVHRRGAC-NOAA18-fv1.0.nc"
    PPS_OBJECTS = cci_read_ctth(filename)
    print PPS_OBJECTS

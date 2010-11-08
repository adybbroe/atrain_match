
import pdb

import os, string
import sys
from pps_basic_configure import *
from pps_error_messages import *

ESTAT_DIR = os.environ["DIR_ANA"]

ACPG_SOURCE="/local_disk/laptop/acpgDevelop"
#ACPG_SOURCE="/data/proj/saf/adybbroe/acpgDevelop"
sys.path.append("%s/angles/test"%(ACPG_SOURCE))

import Numeric

from calipso import *
from config import AREA1KM, RESHAPE_DIR
#MAIN_DIR = "/data/proj/safworks/adam/calipso_data"
#MAIN_DIR = "/local_disk/calipso_data"
#SUB_DIR = "metop02_calipso_2007spring"
#SUB_DIR = "noaa18_calipso_2007Aug"

#CTYPE_DIR = "%s/%s"%(MAIN_DIR,SUB_DIR)
#AVHRR_DIR = "%s/%s"%(MAIN_DIR,SUB_DIR)
#CALIPSO_DIR = "%s/%s"%(MAIN_DIR,SUB_DIR)
#SATPOS_DIR = "%s/%s"%(MAIN_DIR,SUB_DIR)
#EPHE_DIR = "%s/%s"%(MAIN_DIR,SUB_DIR)


# -----------------------------------------------------
def getCaliopAvhrrMatch(avhrrfile,calipsofile,ctypefile,ctthfile,surftfile,sunanglefile):
    import string,os
    import pps_io
    import epshdf
    import Numeric

    basename = os.path.basename(ctypefile).split(".h5")[0]
    base_sat = basename.split("_")[-8]
    base_year = basename.split("_")[-7][0:4]
    base_month = basename.split("_")[-7][4:6]

    basename = string.join(basename.split("_")[0:4],"_")
    #dirname = os.path.dirname(ctypefile).split("/")[0:2]
    #dirname = string.join(dirname,"/")

    savepath = "%s/%s/1km/%s/%s/%s" %(RESHAPE_DIR, base_sat, base_year, base_month, AREA1KM)
    ca_match_file = "%s/1km_%s_caliop_avhrr_match.h5"%(savepath,basename)

    if not os.path.exists(savepath):
        os.makedirs(savepath)
    #print "Match-up file: ",ca_match_file

    if not os.path.exists(ca_match_file):
        # Read AVHRR lon,lat data
        write_log("INFO","Read AVHRR geolocation data")
        avhrrGeoObj = pps_io.readAvhrrGeoData(avhrrfile)
        # Read AVHRR sunsatangels (satellite zenith angle)
        write_log("INFO","Read AVHRR Sun -and Satellites Angels data")
        avhrrAngObj = pps_io.readSunSatAngles(sunanglefile) #, withAbsoluteAzimuthAngles=True)

        # Read AVHRR data
        write_log("INFO","Read AVHRR data")
        avhrrObj = pps_io.readAvhrrData(avhrrfile)

        # Read PPS Cloud Type data
        write_log("INFO","Read PPS Cloud Type")
        ctype = epshdf.read_cloudtype(ctypefile,1,1,0)
        try:
            ctth = epshdf.read_cloudtop(ctthfile,1,1,1,0,1)
        except:
            ctth = None
        # --------------------------------------------------------------------
        write_log("INFO","Read CALIPSO data")
        # Read CALIPSO Lidar (CALIOP) data:
        calipso = reshapeCalipso1km(calipsofile,avhrrGeoObj)
        # Read remapped NWP Surface temperature data
        write_log("INFO","Read NWP surface temperature")
        nwpinst = epshdf.read_nwpdata(surftfile)
        surft = nwpinst.gain*nwpinst.data.astype('d')+nwpinst.intercept
        
        retv,min_diff,max_diff = match_calipso_avhrr(ctypefile,calipso,avhrrGeoObj,avhrrObj,ctype,ctth,surft,avhrrAngObj)
        writeCaliopAvhrrMatchObj(ca_match_file,retv,6)
    else:
        retv = readCaliopAvhrrMatchObj(ca_match_file)
        min_diff = -9.0    # We don't store this information - only extracted during first time of processing
        max_diff = -9.0    # We don't store this information - only extracted during first time of processing

    return retv,min_diff,max_diff

# -----------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
	write_log("INFO","Usage: %s <calipso-hdf5-file> <pps cloudtype file> <pps ctth file> <pps avhrr file>"%sys.argv[0],moduleid=MODULE_ID)
	sys.exit(-9)
    else:
        calipsofile = "%s/%s"%(CALIPSO_DIR,sys.argv[1])
        ctypefile = "%s/%s"%(CTYPE_DIR,sys.argv[2])
        ctthfile = "%s/%s"%(CTYPE_DIR,sys.argv[3])
        avhrrfile = "%s/%s"%(AVHRR_DIR,sys.argv[4])

    import string,os
    import Numeric
    import rpy
    
    basename = os.path.basename(ctypefile).split(".h5")[0]
    basename = string.join(basename.split("_")[0:4],"_")
    
    sl = string.split(sys.argv[2],"_")
    platform = sl[0]
    norbit = string.atoi(sl[3])
    yyyymmdd = sl[1]

    caObj = getCaliopAvhrrMatch(avhrrfile,calipsofile,ctypefile,ctthfile)


    # Make AVHRR cloud mask:
    """
    import _pypps_filters

    ndim = caObj.avhrr.cloudtype.shape[0]
    avhrr_clmask = Numeric.greater(caObj.avhrr.cloudtype,4)
    avhrr_clfrac=Numeric.zeros((3,ndim),'d')

    avhclmask = Numeric.concatenate((avhrr_clmask,avhrr_clmask))
    avhclmask = Numeric.concatenate((avhclmask,avhrr_clmask))
    avhclmask = Numeric.reshape(avhclmask,(3,ndim)).astype('d')

    _pypps_filters.texture(avhclmask,avhrr_clfrac,3,"mean")
    avhrr_clfrac = avhrr_clfrac[1,::]
    """
    avhrr_clfrac = Numeric.greater(caObj.avhrr.cloudtype,4).astype('d')


    # PPS Cloud Type:
    #pps_cloudy = Numeric.greater(caObj.avhrr.cloudtype,4)
    pps_cloudy = Numeric.greater(avhrr_clfrac,0.66)
    # Assume no no-data (nodata will be treated cloud free):
    #pps_clear = Numeric.less_equal(caObj.avhrr.cloudtype,4) 
    pps_clear = Numeric.less_equal(avhrr_clfrac,0.34)

    calipso_clear = Numeric.less(caObj.calipso.cloud_fraction,0.34)
    calipso_cloudy = Numeric.greater(caObj.calipso.cloud_fraction,0.66)
    #calipso_clear = Numeric.less(caObj.calipso.cloud_fraction,0.1)
    #calipso_cloudy = Numeric.greater(caObj.calipso.cloud_fraction,0.9)
    
    n_clear_clear = Numeric.repeat(pps_clear,
                                   Numeric.logical_and(calipso_clear,pps_clear)).shape[0]
    n_cloudy_cloudy = Numeric.repeat(pps_clear,
                                     Numeric.logical_and(calipso_cloudy,pps_cloudy)).shape[0]
    n_clear_cloudy = Numeric.repeat(pps_clear,
                                    Numeric.logical_and(calipso_clear,pps_cloudy)).shape[0]
    n_cloudy_clear = Numeric.repeat(pps_clear,
                                    Numeric.logical_and(calipso_cloudy,pps_clear)).shape[0]

    nclear = Numeric.repeat(calipso_clear,calipso_clear).shape[0]
    ncloudy = Numeric.repeat(calipso_cloudy,calipso_cloudy).shape[0]

    # Print some statistics:
    print "Number of clear points (CALIPSO): ",nclear
    print "Number of cloudy points (CALIPSO): ",ncloudy
    print "Clear-Clear,Cloudy-Cloudy",n_clear_clear,n_cloudy_cloudy
    print "Calipso-Clear PPS-Cloudy, Calipso-Cloudy PPS-Clear",n_clear_cloudy,n_cloudy_clear

    pod_cloudy = float(n_cloudy_cloudy)/ncloudy
    pod_clear = float(n_clear_clear)/nclear
    #far_cloudy = float(n_cloudy_clear)/ncloudy
    #far_clear = float(n_clear_cloudy)/nclear
    far_cloudy = float(n_clear_cloudy)/(n_clear_cloudy + n_cloudy_cloudy)
    far_clear = float(n_cloudy_clear)/(n_clear_clear + n_clear_cloudy)
    
    print "POD-Cloudy: ",pod_cloudy
    print "POD-Clear: ",pod_clear
    print "FAR-Cloudy: ",far_cloudy
    print "FAR-Clear: ",far_clear    



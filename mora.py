import numpy as np
import pandas as pd
import time
import calendar
from datetime import datetime, timedelta
from calendar import timegm
TAI93 = datetime(1993, 1, 1)
from config import (RESOLUTION, NODATA, MORA_REQUIRED, sec_timeThr_synop)
from matchobject_io import (MoraAvhrrTrackObject, 
                            MoraObject)
from calipso import (find_break_points, calipso_track_from_matched,
                     do_some_logging)

from common import (ProcessingError, MatchupError, elements_within_range)
from extract_imager_along_track import avhrr_track_from_matched
import logging
logger = logging.getLogger(__name__)

TEST_FILE ="/home/a001865/DATA_MISC/atrain_match_testcases/mora/cb_2010.dat"

def get_mora_data(filename):

    convert_datefunc = lambda x: datetime.strptime(x, '%Y%m%dT%H%M')

    dtype = [('station', '|S5'),
             ('lat', 'f8'), 
             ('lon', 'f8'),
             ('x', 'f8'), 
             ('date', object), 
             ('cloud_base_height', 'i4')]

    data = np.genfromtxt(filename,
                         skip_header=0,
                         skip_footer=0,
                         usecols=(
                             0, 1, 2, 3, 4, 5),
                         dtype=dtype,
                         unpack=True,
                         converters={
                                     #2: lambda x: float(x) / 100.,
                                     #3: lambda x: float(x) / 100.,
                             4: convert_datefunc,
                                     #6: lambda x: float(x) / 10.,
                                     #7: lambda x: float(x) / 10.,
                                     #8: lambda x: float(x) / 10., 
                         })
    return pd.DataFrame(data)
    
def reshapeMora(morafiles, avhrr):
    start_t = datetime.utcfromtimestamp(avhrr.sec1970_start)
    end_t = datetime.utcfromtimestamp(avhrr.sec1970_end)
    #datetime.datetime.fromtimestamp(
    items = [get_mora_data(filename) for filename in morafiles]
    panda_moras = pd.concat(items, ignore_index=True)
    #import pdb
    #pdb.set_trace()
    dt_ = timedelta(seconds=sec_timeThr_synop)
    newmoras = panda_moras[panda_moras['date'] < end_t + dt_]
    panda_moras = newmoras[newmoras['date']  >  start_t - dt_ ]
    retv = MoraObject()
    retv.longitude = np.array(panda_moras['lon'])
    retv.latitude = np.array(panda_moras['lat'])
    retv.cloud_fraction = np.array(panda_moras['cloud_base_height'])

    retv.sec_1970 = np.array([calendar.timegm(tobj.timetuple()) for tobj in panda_moras['date']])
    return retv

def match_mora_avhrr(moraObj, imagerGeoObj, imagerObj, ctype, cma, ctth, nwp,
                     imagerAngObj, cpp, nwp_segments):
    retv = MoraAvhrrTrackObject()
    from common import map_avhrr
    cal, cap = map_avhrr(imagerGeoObj, 
                         moraObj.longitude.ravel(),
                         moraObj.latitude.ravel(),
                         radius_of_influence=RESOLUTION*0.7*1000.0)
    calnan = np.where(cal == NODATA, np.nan, cal)
    if (~np.isnan(calnan)).sum() == 0:
        if MORA_REQUIRED:
            raise MatchupError("No matches within region.")
        else:
            logger.warning("No matches within region.")
            return None   
    #check if it is within time limits:
    if len(imagerGeoObj.time.shape)>1:
        imager_time_vector = [imagerGeoObj.time[line,pixel] for line, pixel in zip(cal,cap)]
        imager_lines_sec_1970 = np.where(cal != NODATA, imager_time_vector, np.nan)
    else:
        imager_lines_sec_1970 = np.where(cal != NODATA, imagerGeoObj.time[cal], np.nan)
    idx_match = elements_within_range(moraObj.sec_1970, imager_lines_sec_1970, sec_timeThr_synop)
    if idx_match.sum() == 0:
        if MORA_REQUIRED:
            raise MatchupError("No within time threshold %d s." % sec_timeThr_synop)  
        else:
            logger.warning("No matches in region within time threshold %d s.", sec_timeThr_synop)
            return None
    retv.mora = calipso_track_from_matched(retv.mora, moraObj, idx_match)
    # Mora line,pixel inside AVHRR swath (one nearest neighbour):
    retv.mora.imager_linnum = np.repeat(cal, idx_match).astype('i')
    retv.mora.imager_pixnum = np.repeat(cap, idx_match).astype('i')
    # Imager time
    retv.avhrr.sec_1970 = np.repeat(imager_lines_sec_1970, idx_match)
    retv.diff_sec_1970 = retv.mora.sec_1970 - retv.avhrr.sec_1970

    do_some_logging(retv, moraObj)
    logger.debug("Extract imager along track!")
    
    retv = avhrr_track_from_matched(retv, imagerGeoObj, imagerObj, imagerAngObj, 
                                    nwp, ctth, ctype, cma,  
                                    cpp=cpp, nwp_segments=None)
    return retv

if __name__ == "__main__":
    get_mora_data(TEST_FILE)

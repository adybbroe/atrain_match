"""
Configuration file for ``atrain_match``. Most configuration options and constants
used in ``atrain_match`` are set in this file. However, there may
still be some modules which have internal constants defined.

"""

import os

def get_environ(name, default=None):
    """Get the environment variable *name*. If it is not defined, return 
    *default*."""
    try:
        return os.environ[name]
    except KeyError:
        return default


RESOLUTION = 1 #1 or 5
clsat_type = 1 #1=GEOPROG 2=CWC_RVOD
SAT_DIR = get_environ('SAT_DIR', default="/data/proj/saf/ejohansson/Satellite_Data")

match_files = ["/data/proj/saf/ejohansson/SNO_tools/Snotimes/08/matchups_augsep_2008_mod.dat"]

MAIN_RUNDIR = os.getcwd()
MAIN_DIR = get_environ('VALIDATION_RESULTS_DIR', MAIN_RUNDIR)
SUB_DIR = "%s/Matchups" %MAIN_DIR
RESHAPE_DIR = "%s/Reshaped_Files" %MAIN_DIR
DATA_DIR = "%s/Data" %MAIN_DIR
PLOT_DIR = "%s/Plot" %MAIN_DIR
RESULT_DIR = "%s/Results" %MAIN_DIR
PPS_DATA_DIR = get_environ('PPS_DATA_DIR', '/data/arkiv/proj/safworks/data/pps') # The naming of the PPS env variable DATA_DIR is a bit unfortunate...
CLOUDSAT_DIR = "%s/CloudSat" % SAT_DIR
CLOUDSAT_TYPE = 'GEOPROF'
CALIPSO_DIR = "%s/Calipso" % SAT_DIR

SAT_ORBIT_DURATION = 90*60 # Duration of a satellite orbit in seconds

CTTH_FILE = get_environ('CTTH_FILE', 'ctth') # One of 'ctth', 'ctth_opaque', and 'ctth_semitransparent'

sec_timeThr = 60*20 # Allowed time deviation in seconds between AVHRR and CALIPSO/CloudSat matchup

CLOUDSAT_CLOUDY_THR = 30.0  # Recommended cloud threshold for the CloudSat cloud mask. In 5km data this threshold have already been aplied therfore no reason to change it for thise data set. 

MAXHEIGHT = 25000.0 #This should be taken care of in plot function. Se plot function for 1 km

#: Range of allowed (AVHRR) satellite azimuth angles, in degrees
AZIMUTH_RANGE = (0., 360.)

# CloudSat sampling frequency in km (or rather the most likely
# resolution difference between CALIPSO 1 km datasets and
# the CloudSat 2B-GEOPROF dataset). Nominally CloudSat sampling
# rate is said to be 1.1 km but it seems as the CALIPSO sampling
# rate is not exactly 1 km but slightly above - as based on the
# optimised matching of plots of the two datasets. /KG
CLOUDSAT_TRACK_RESOLUTION = 1.076
CLOUDSAT5KM_TRACK_RESOLUTION = 1.076#*5.0

EMISS_MIN_HEIGHT = 2000.0
EMISS_LIMIT = 0.2 # A value of 0.2-0.3 in cloud emissivity seems reasonable

ALLOWED_MODES = ['BASIC',
             'EMISSFILT',        # Filter out cases with the thinnest topmost CALIPSO layers
             'ICE_COVER_SEA',    # Restrict to ice cover over sea using NSIDC and IGBP data
             'ICE_FREE_SEA',     # Restrict to ice-free sea using NSIDC and IGBP data
             'SNOW_COVER_LAND',  # Restrict to snow over land using NSIDC and IGBP data
             'SNOW_FREE_LAND',   # Restrict to snow-free land using NSIDC and IGBP data
             'COASTAL_ZONE']      # Restrict to coastal regions using NSIDC data (mixed microwave region)
             
if RESOLUTION == 1:
    DSEC_PER_AVHRR_SCALINE = 0.1667 # Full scan period, i.e. the time interval between two consecutive lines (sec)
    SWATHWD=2048
    AREA = "arctic_super_5010"

elif RESOLUTION == 5:
    DSEC_PER_AVHRR_SCALINE = 1.0/6*4 # A "work for the time being" solution.
    SWATHWD=409
    AREA = "arctic_super_1002_5km"
    ALLOWED_MODES.append('OPTICAL_DEPTH')      # Filter out cases with the thinnest topmost CALIPSO layers. Define MIN_OPTICAL_DEPTH below
                 
MIN_OPTICAL_DEPTH = 1 # Threshold for optical thickness. If optical thickness is below this value it will be filtered out.


COMPRESS_LVL = 6
NLINES=6000
NODATA=-9

PLOT_MODES = ['BASIC']

if True: # Do we use this def? Yes we do.
    def subdir(self, satname, date):
        """This method is used by FileFinders for finding the correct subdir."""
        dir = "%dkm/%d/%02d" % (RESOLUTION, date.year, date.month)
        try:
            if 'avhrr' in self.ending:
                dir = os.path.join(dir,"import/PPS_data")                
            if 'sunsatangles' in self.ending:
                dir = os.path.join(dir, "import/ANC_data")
            if 'nwp' in self.ending:
                dir = os.path.join(dir,"import/NWP_data")
            for ending in ['cloudmask', 'cloudtype', 'ctth', 'precip']:
                if ending in self.ending:
                    dir = os.path.join(dir, "export")
            
            #for ending in ['avhrr', 'sunsatangles', 'nwp_tsur']:
            #    if ending in self.ending:
            #        dir = os.path.join(dir, 'import')
            #for ending in ['cloudtype', 'ctth']:
            #    if ending in self.ending:
            #        dir = os.path.join(dir, 'export')
        except (AttributeError, TypeError):
            # We're dealing with some other satellite data, e.g. Calipso or Cloudsat
            pass
        return dir


#========== Statistics setup ==========#
CASES = [{'satname': 'noaa18', 'year': 2009, 'month': 1},
         {'satname': 'noaa18', 'year': 2009, 'month': 7},
         {'satname': 'noaa19', 'year': 2009, 'month': 7}]
MAP = [AREA]
MAIN_DATADIR = MAIN_DIR # Should contain the Results directory
COMPILED_STATS_FILENAME = '%s/Results/compiled_stats' %MAIN_DATADIR
SURFACES = ["ICE_COVER_SEA","ICE_FREE_SEA","SNOW_COVER_LAND","SNOW_FREE_LAND","COASTAL_ZONE"]

# The following are used in the old-style script interface
SATELLITE = ['noaa18', 'noaa19']
STUDIED_YEAR = ["2009"]
STUDIED_MONTHS = ['01', "07"]
OUTPUT_DIR = "%s/Ackumulering_stat/Results/%s" % (MAIN_DATADIR, SATELLITE[0])

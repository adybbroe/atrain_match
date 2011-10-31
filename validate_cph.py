"""
Use this script to validate the CPP cloud phase (cph) product

"""

import os
from amsr_avhrr.util import get_avhrr_lonlat, get_cpp_product
from amsr_avhrr.match import match_lonlat
from runutils import process_scenes

import logging
logger = logging.getLogger(__name__)


#: Directory for mapper files
MATCH_DIR = os.environ.get('MATCH_DIR', '.')

#: h5py compression settings (True, or an integer in range(10))
_COMPRESSION = True

#: Calipso cloud phase bits
CALIPSO_PHASE_BITS = range(5, 7)

#: Calipso cloud phase values
CALIPSO_PHASE_VALUES = dict(unknown=0,
                            ice=1,
                            water=2,
                            horizontal_oriented_ice=3)

#: Water (no mixed) value
CALIPSO_WATER_VALUE = 2

#: Calipso quality bits
CALIPSO_QUAL_BITS = range(7, 9)

#: Calipso quality values
CALIPSO_QUAL_VALUES = dict(none=0,
                           low=1,
                           medium=2,
                           high=3)


#: CPP cph value meanings
CPP_PHASE_VALUES = dict(no_cloud=0,
                        liquid=1,
                        ice=2,
                        mixed=3,
                        uncertain=6,
                        no_observation=-1)


def get_calipso_lonlat(calipso_filename):
    import h5py
    with h5py.File(calipso_filename) as f:
        lon = f['Longitude'][:]
        lat = f['Latitude'][:]
    
    return lon, lat


def get_bits(value, bits, shift=False):
    """
    Returns value for bits *bits* in *value*.
    
    Examples
    
    >>> get_bits(6, [0, 1])
    2
    >>> get_bits(6, [1, 2])
    6
    
    If *shift* is True, shift the obtained value by min(bits) bits:
    
    >>> get_bits(6, [1, 2], shift=True)
    3
    
    """
    selected = value & sum([2**i for i in bits])
    if shift:
        return selected >> min(bits)
    return selected


def get_calipso_phase(calipso_filename, qual_min=CALIPSO_QUAL_VALUES['medium'],
                      max_layers=1):
    """
    Returns Calipso cloud phase.
    
    Pixels with quality lower than *qual_min* are masked out.
    
    Screen out pixels with more than *max_layers* layers.
    
    """
    import numpy as np
    import h5py
    with h5py.File(calipso_filename) as f:
        features = f['Feature_Classification_Flags'][:]
    
    # Reduce to single layer, masking any multilayer pixels
    features = np.ma.array(features[:, 0],
                           mask=(features[:, max_layers:] > 1).any(axis=-1))
    
    phase = get_bits(features, CALIPSO_PHASE_BITS, shift=True)
    qual = get_bits(features, CALIPSO_QUAL_BITS, shift=True)
    # Don't care about pixels with lower than *qual_min* quality
    return np.ma.array(phase, mask=qual < qual_min)


def find_calipso(avhrr_filename):
    """
    Find Calipso files matching *avhrr_filename*. Returns a list of file paths.
    
    """
    from file_finders import CalipsoFileFinder, PpsFileFinder
    pps_finder = PpsFileFinder()
    parsed = pps_finder.parse(avhrr_filename)
    
    # Limit matching to AMSR-E files starting 45 min (duration of one half
    # orbit) before up to 20 min (duration of one EARS AVHRR swath) after the
    # start of the AVHRR swath
    amsr_finder = CalipsoFileFinder(time_window=(-45 * 60, 20 * 60))
    return amsr_finder.find(parsed['datetime'])


def process_noaa_scene(satname, orbit, **kwargs):
    """
    Match this noaa scene with cloudsat scenes and process.
    
    """
    from pps_runutil import get_ppsProductArguments
    from pps_basic_configure import AVHRR_DIR, OUTPUT_DIR
    
    #argv = [sys.argv[0], 'satproj', satname, orbit]
    # get_ppsProductArguments can't take non-string orbit
    argv = ['', 'satproj', satname, str(orbit)]
    ppsarg, arealist = get_ppsProductArguments(argv) #@UnusedVariable
    avhrr_filename = os.path.join(AVHRR_DIR, ppsarg.files.avhrr)
    
    calipso_filenames = find_calipso(avhrr_filename)
    logger.debug("Found Calipso files: %r" % calipso_filenames)
    
    cpp_filename = os.path.join(OUTPUT_DIR, ppsarg.files.cpp)
    
    for calipso_filename in calipso_filenames:
        process_case(calipso_filename, avhrr_filename, cpp_filename, **kwargs)


def _filename_base(avhrr_filename, calipso_filename):
    return "match--%s--%s" % (os.path.basename(avhrr_filename),
                              os.path.basename(calipso_filename))

def get_mapper(avhrr_filename, calipso_filename):
    """
    Restore mapper object from file or create a new mapper and write it to file.
    
    Returns :class:`MatchMapper` instance mapping AVHRR to Calipso.
    
    """
    match_file = _filename_base(avhrr_filename, calipso_filename) + '.h5'
    match_path = os.path.join(MATCH_DIR, match_file)
    if os.path.exists(match_path):
        logger.info("Reading match from %r" % match_path)
        from amsr_avhrr.match import MatchMapper
        mapper = MatchMapper.from_file(match_path)
    else:
        logger.debug("Getting AVHRR lon/lat")
        avhrr_lonlat = get_avhrr_lonlat(avhrr_filename)
        logger.debug("Getting Calipso lon/lat")
        calipso_lonlat = get_calipso_lonlat(calipso_filename)
        logger.debug("Matching AVHRR to Calipso lon/lat")
        mapper = match_lonlat(avhrr_lonlat, calipso_lonlat, n_neighbours=1)
        mapper.write(match_path, compression=_COMPRESSION)
        logger.info("Match written to %r" % match_path)
    
    return mapper


def write_matched_values(filename, cpp_phase, cal_phase):
    import h5py
    selected = (~cpp_phase.mask & ~cal_phase.mask)
    with h5py.File(filename, 'w') as f:
        f.create_dataset('cpp_phase', data=cpp_phase[selected],
                         compression=_COMPRESSION)
        f.create_dataset('calipso_phase', data=cal_phase[selected],
                         compression=_COMPRESSION)


def validate(cpp_phase, cal_phase, verbose=False):
    """
    Validate CPP (*cpp_phase*) and Calipso (*cal_phase*) cloud phase.
    Prints results to stdout.
    
    If *verbose* is True, print extended matrix.
    
    """
    import sys
    if hasattr(cpp_phase, 'mask'):
        n_pixels = (~(cpp_phase.mask | cal_phase.mask)).sum()
    else:
        n_pixels = cpp_phase.size
        print("Number of matching pixels: %d" % n_pixels)
    cpp_keys = ['liquid', 'ice', 'mixed', 'uncertain']
    
    cal_name_len = 40
    cpp_name_len = 15
    print((' ' * (cal_name_len) +
           ''.join([k.rjust(cpp_name_len) for k in cpp_keys])).rjust(cal_name_len))
    
    def print_values(cal_ice_or_water, cpp_keys=cpp_keys):
        N = {}
        for k in cpp_keys:
            n = (cal_ice_or_water & (cpp_phase == CPP_PHASE_VALUES[k])).sum()
            N[k] = n
            sys.stdout.write("% 15d" % n)
        sys.stdout.write('\n')
        return N
    
    sys.stdout.write("Calipso water: ".rjust(cal_name_len))
    water_N = print_values(cal_phase == CALIPSO_PHASE_VALUES['water'])
    sys.stdout.write("Calipso ice: ".rjust(cal_name_len))
    ice_N = print_values((cal_phase == CALIPSO_PHASE_VALUES['ice']) |
                         (cal_phase == CALIPSO_PHASE_VALUES['horizontal_oriented_ice']))
    
    pod_water = 1. * water_N['liquid'] / (water_N['liquid'] + water_N['ice'])
    pod_ice = 1. * ice_N['ice'] / (ice_N['liquid'] + ice_N['ice'])
    far_water = 1. * ice_N['liquid'] / (water_N['liquid'] + ice_N['liquid'])
    far_ice = 1. * water_N['ice'] / (water_N['ice'] + ice_N['ice'])
    
    print('')
    print("POD: ".rjust(cal_name_len) + "% 15.2f% 15.2f" % (pod_water, pod_ice))
    print("FAR: ".rjust(cal_name_len) + "% 15.2f% 15.2f" % (far_water, far_ice))
    
    if verbose:
        print('')
        print((' ' * (cal_name_len) +
               ''.join([k.rjust(cpp_name_len) for k in CPP_PHASE_VALUES.keys()])).rjust(cal_name_len))
        for k in CALIPSO_PHASE_VALUES.keys():
            sys.stdout.write(("Calipso %s: " % k).rjust(cal_name_len))
            print_values(cal_phase == CALIPSO_PHASE_VALUES[k], CPP_PHASE_VALUES.keys())


def process_case(calipso_filename, avhrr_filename, cpp_filename, verbose=False,
                 max_layers=9, qual_min=CALIPSO_QUAL_VALUES['medium']):
    """
    This is the work horse.
    
    """
    
    mapper = get_mapper(avhrr_filename, calipso_filename)
    
    logger.debug("Getting CPP water")
    cpp_phase = mapper(get_cpp_product(cpp_filename, 'cph'))
    cpp_phase = cpp_phase[:, 0, 0] # mapper returns 3-d array (spatial + neighbours)
    logger.debug("Getting Calipso water")
    cal_phase = get_calipso_phase(calipso_filename, max_layers=max_layers,
                                  qual_min=qual_min)
    
    filename = _filename_base(avhrr_filename, calipso_filename) + '--values.h5'
    write_matched_values(filename, cpp_phase, cal_phase)
    
    logger.debug("Validating")
    validate(cpp_phase, cal_phase, verbose)


def validate_all(matched_values_files, verbose=False):
    """
    Read all *matched_values_files* and perform validation on the concatenated
    arrays.
    
    """
    import h5py
    import numpy as np
    cpp_phases = []
    cal_phases = []
    for filename in matched_values_files:
        with h5py.File(filename, 'r') as f:
            cpp_phases.append(f['cpp_phase'][:])
            cal_phases.append(f['calipso_phase'][:])
    
    validate(np.concatenate(cpp_phases), np.concatenate(cal_phases), verbose)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="Usage: %prog [options] satproj "
                                "<satname> <orbit> \n"
                                "or:    %prog [options] CASE [...]\n"
                                "          where CASE ~ 'possible/path/"
                                "noaa19_20110916_0959_03456*'")
    parser.add_option('-v', '--verbose', action='store_true')
    parser.add_option('-d', '--debug', action='store_true',
                      help="Don't ignore errors")
    parser.add_option('-l', '--max-layers', type='int', metavar='N',
                      help="Screen out pixels with more than N layers (default 1)")
    parser.add_option('-q', '--quality', type='int',
                      help="Screen out pixels with lower quality than N. "
                      "N must be in 0..3 (default 2)")
    opts, args = parser.parse_args()
    
    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Verbose")
    else:
        logging.basicConfig(level=logging.WARNING)
    
    processing_kwargs = {}
    if opts.verbose is not None:
        processing_kwargs['verbose'] = opts.verbose
    if opts.max_layers is not None:
        processing_kwargs['max_layers'] = opts.max_layers
    if opts.quality is not None:
        processing_kwargs['qual_min'] = opts.quality
    
    # Command line handling
    if args[0] == 'satproj':
        satname, orbit = args[1:]
        process_noaa_scene(satname, orbit, **processing_kwargs)
    else:
        process_scenes(args, process_noaa_scene, ignore_errors=not opts.debug,
                       **processing_kwargs)


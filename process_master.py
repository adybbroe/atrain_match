#!/usr/bin/python
"""
This module is the main entry point for matching noaa and/or metop data with
Cloudsat and Calipso data, and produce statistics for validation of PPS
cloud mask, cloud type and cloud top temperature and height products.

It is really a wrapper to :func:`cloudsat_calipso_avhrr_match.run`, for running
through a set of SNO matchups.

.. note::

    This module has a command line interface.

"""

from pps_error_messages import write_log
import config
#print "config.SAT_DIR:", config.SAT_DIR
#print "config.CALIPSO_DIR:", config.CALIPSO_DIR

def process_matchups(matchups, run_modes, reprocess=False, debug=False):
    """
    Run the given SNO *matchups* through the validation system.
    
    *matchups* should be a list of :class:`find_crosses.Cross` instances.
    
    If *reprocess* is True, disregard any previously generated Cloudsat- and
    Calipso-AVHRR matchup files.
    
    """
    import cloudsat_calipso_avhrr_match
    from common import MatchupError
    import os
    import ConfigParser
    from config import CONFIG_PATH
    CONF = ConfigParser.ConfigParser()
    CONF.read(os.path.join(CONFIG_PATH, "atrain_match.cfg"))
    OPTIONS = {}
    for option, value in CONF.items('general', raw = True):
        OPTIONS[option] = value

    problematic = set()
    no_matchup_files = []
    for match in sorted(matchups):

#        match = matchups[i + 50]
#        import datetime
#        if match.time1 < datetime.datetime(2008,01,01):
#            continue
        for mode in run_modes:
            print mode
            #import pdb
            #cloudsat_calipso_avhrr_match.run(match, mode, reprocess)
            #pdb.set_trace()
            if mode in ["OPTICAL_DEPTH","OPTICAL_DEPTH_DAY","OPTICAL_DEPTH_NIGHT","OPTICAL_DEPTH_TWILIGHT"]:
                for num in range(len(config.MIN_OPTICAL_DEPTH)):
                    min_optical_depth = config.MIN_OPTICAL_DEPTH[num]
                    try:
                        cloudsat_calipso_avhrr_match.run(match, mode,  OPTIONS, min_optical_depth, reprocess)
                    except MatchupError, err:
                        write_log('WARNING', "Matchup problem: %s" % str(err))
                        no_matchup_files.append(match)
                        break
                    except:
                        problematic.add(match)
                        write_log('WARNING', "Couldn't run cloudsat_calipso_avhrr_match.")
                        if debug is True:
                            raise
                        break
            else:
                min_optical_depth = None 
                #min_optical_depth = 0.35 #Assuming this is the detection limit /KG 13/12 2012
                                          #But you also need to modify basic python module and config.py
                                          #if you want to filter for all cases!
                try:
                    cloudsat_calipso_avhrr_match.run(match, mode,  OPTIONS, min_optical_depth, reprocess)
                except MatchupError, err:
                    write_log('WARNING', "Matchup problem: %s" % str(err))
                    import traceback
                    traceback.print_exc()
                    no_matchup_files.append(match)
                    break
                except:
                    import traceback
                    traceback.print_exc()
                    problematic.add(match)
                    write_log('WARNING', "Couldn't run cloudsat_calipso_avhrr_match.")
                    if debug is True:
                        raise
                    break

                
    if len(no_matchup_files) > 0:
        write_log('WARNING', 
                  "%d of %d cases had no matchups in region, within the time window:\n%s" % \
                  (len(no_matchup_files), len(matchups),
                   '\n'.join([str(m) for m in no_matchup_files])))
    if len(problematic) > 0:
        write_log('WARNING', "%d of %d cases had unknown problems:\n%s" % \
                  (len(problematic), len(matchups),
                   '\n'.join([str(m) for m in problematic])))
    

def main(args=None):
    """
    Process command line options and run matchup and validation.
    
    If *args* is provided, it should be a list of command line arguments (e.g.
    sys.argv[1:]).
    
    For a complete usage description, run 'python process_master -h'.
    
    """
    import find_crosses
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--mode', '-M', type=str, required=False, choices=config.ALLOWED_MODES,
                      help=("Run validation software in MODE "))
    parser.add_argument('--reprocess', '-r', const=True, nargs='?', required=False,
                        help="Disregard any previously generated Cloudsat- and "
                        "Calipso-AVHRR matchup files.")
    parser.add_argument('-d', '--debug', const=True, nargs='?', required=False, 
                        help="Get debug logging")
    group.add_argument( '--pps_okay_scene', '-os', 
                      help="Interpret arguments as PPS okay scenes instead of "
                      "sno_output_files (e.g. noaa19_20101201_1345_27891*)")
    group.add_argument( '--pps_product_file', '-pf', 
                      help="Interpret arguments as inputfile with "  
                      "list of pps files")
    group.add_argument('--sno_file', '-sf', 
                      help="Interpret arguments as sno_output_file")

    options = parser.parse_args()
    
    if options.mode is not None:
        run_modes = [options.mode]
    else:
        run_modes = config.ALLOWED_MODES

    reprocess = False    
    if options.reprocess is not None:
        reprocess = options.reprocess

    config.DEBUG = options.debug
    if options.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    matchups = []
    if options.pps_okay_scene:
        # Simulate crosses from PPS scenes
        from find_crosses import Cross
        from runutils import parse_scene
        scene = options.pps_okay_scene
        satname, time, orbit = parse_scene(scene) #@UnusedVariable
        matchups.append(Cross(satname, '', time, time, -999, -999))
    elif options.sno_file is not None:
        sno_output_file = options.sno_file
        found_matchups = find_crosses.parse_crosses_file(sno_output_file)
        if len(found_matchups) == 0:
            write_log('WARNING', "No matchups found in SNO output file %s" %
                      sno_output_file)
            if options.debug is True:
                raise Warning()
        else:
            matchups.extend(found_matchups)
    elif options.pps_product_file is not None:
        from find_crosses import Cross
        from runutils import  parse_scenesfile_v2014
        pps_output_file = options.pps_product_file
        read_from_file = open(pps_output_file,'r')
        for line in read_from_file:
            satname, time = parse_scenesfile_v2014(line)
            matchups.append(Cross(satname, '', time, time, -999, -999))

    process_matchups(matchups, run_modes, reprocess, options.debug)
    
    return 0

#------------------------------------------------------------------------------
if __name__=='__main__':
    main()

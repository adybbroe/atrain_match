# Program orrb_CFC_stat_emissfilt

# This program calculates basic statistics for the cloud amount (CFC) product for
# each month after filtering of t

import os, string, glob
import sys, math
import pdb
import numpy

SATELLITE = ["metop02"]
RESOLUTION = ["1km"]
#STUDIED_MONTHS = ["200706","200707","200708","200712"]
STUDIED_YEAR = ["2008"]
STUDIED_MONTHS = ["08","09"]
MAP = ["arctic_super_5010"]
#MAIN_DATADIR = "/data/proj/saf/kgkarl/calipso_cloudsat/scr/orr-b-stat/results/"
MAIN_DATADIR = "/data/proj/saf/ejohansson/atrain_match"
OUTPUT_DIR = "%s/Ackumulering_stat" % MAIN_DATADIR
BASIC_INDATA_DIR = "%s/Results/%s/%s/%s/BASIC/" % (MAIN_DATADIR, SATELLITE[0], RESOLUTION[0] , STUDIED_YEAR[0])
MISSFILT_INDATA_DIR = "%s/Results/%s/%s/%s/EMISSFILT/" % (MAIN_DATADIR, SATELLITE[0], RESOLUTION[0] , STUDIED_YEAR[0])
SURFACES = ["ICE_COVER_SEA","ICE_FREE_SEA","SNOW_COVER_LAND","SNOW_FREE_LAND","COASTAL_ZONE"]

# -----------------------------------------------------
if __name__ == "__main__":
    result=[]
    for i in range(len(STUDIED_MONTHS)):
        month="%s%s" %(STUDIED_YEAR[0],STUDIED_MONTHS[i])
        emissfilt_indata_dir = "%s/Results/%s/%s/%s/%s/%s/EMISSFILT/" % (MAIN_DATADIR, SATELLITE[0], RESOLUTION[0] , STUDIED_YEAR[0], STUDIED_MONTHS[i], MAP[0])
        datafiles = glob.glob("%s*1.dat" % emissfilt_indata_dir)
        datafiles2 = glob.glob("%s*1.dat" % emissfilt_indata_dir)
        n_clear_clear_csa = 0
        n_clear_cloudy_csa = 0
        n_cloudy_clear_csa = 0
        n_cloudy_cloudy_csa = 0
        n_clear_clear_cal = 0
        n_clear_cloudy_cal = 0
        n_cloudy_clear_cal = 0
        n_cloudy_cloudy_cal = 0
        n_clear_clear_cal_MODIS = 0
        n_clear_cloudy_cal_MODIS = 0
        n_cloudy_clear_cal_MODIS = 0
        n_cloudy_cloudy_cal_MODIS = 0
        samples_csa = 0
        samples_cal = 0

        scenes = len(datafiles)
        cfc_sum_csa = 0
        cfc_sum_cal = 0
        
        for datafile in datafiles:
            current_datafile = open(datafile, "r")
            datalist = current_datafile.readlines()
            #print "Datafile: ", datafile
            csa_data = string.split(datalist[4])
            cal_data = string.split(datalist[8])
            modis_data = string.split(datalist[10])

            # Accumulate CloudSat statistics
            
            n_clear_clear_csa = n_clear_clear_csa + int(csa_data[4])
            n_clear_cloudy_csa = n_clear_cloudy_csa + int(csa_data[5])
            n_cloudy_clear_csa = n_cloudy_clear_csa + int(csa_data[6])
            n_cloudy_cloudy_csa = n_cloudy_cloudy_csa + int(csa_data[7])
            
            # Accumulate CALIOP statistics
            
            n_clear_clear_cal = n_clear_clear_cal + int(cal_data[4])
            n_clear_cloudy_cal = n_clear_cloudy_cal + int(cal_data[5])
            n_cloudy_clear_cal = n_cloudy_clear_cal + int(cal_data[6])
            n_cloudy_cloudy_cal = n_cloudy_cloudy_cal + int(cal_data[7])

            # Accumulate CALIOP-MODIS statistics
            
            n_clear_clear_cal_MODIS = n_clear_clear_cal_MODIS + int(modis_data[4])
            n_clear_cloudy_cal_MODIS = n_clear_cloudy_cal_MODIS + int(modis_data[5])
            n_cloudy_clear_cal_MODIS = n_cloudy_clear_cal_MODIS + int(modis_data[6])
            n_cloudy_cloudy_cal_MODIS = n_cloudy_cloudy_cal_MODIS + int(modis_data[7])

            current_datafile.close()
            
        if month == "200712":   # Add second half of CALIOP matches
            for datafile in datafiles2:
                current_datafile = open(datafile, "r")
                datalist = current_datafile.readlines()
                #print "Datafile: ", datafile
                csa_data = string.split(datalist[4])
                cal_data = string.split(datalist[8])
                
                # Don't accumulate CloudSat statistics (they will otherwise be duplicated!)
                
                #n_clear_clear_csa = n_clear_clear_csa + int(csa_data[4])
                #n_clear_cloudy_csa = n_clear_cloudy_csa + int(csa_data[5])
                #n_cloudy_clear_csa = n_cloudy_clear_csa + int(csa_data[6])
                #n_cloudy_cloudy_csa = n_cloudy_cloudy_csa + int(csa_data[7])
                
                
                # Accumulate CALIOP statistics
                
                n_clear_clear_cal = n_clear_clear_cal + int(cal_data[4])
                n_clear_cloudy_cal = n_clear_cloudy_cal + int(cal_data[5])
                n_cloudy_clear_cal = n_cloudy_clear_cal + int(cal_data[6])
                n_cloudy_cloudy_cal = n_cloudy_cloudy_cal + int(cal_data[7])
                
                # Accumulate CALIOP-MODIS statistics
            
                n_clear_clear_cal_MODIS = n_clear_clear_cal_MODIS + int(modis_data[4])
                n_clear_cloudy_cal_MODIS = n_clear_cloudy_cal_MODIS + int(modis_data[5])
                n_cloudy_clear_cal_MODIS = n_cloudy_clear_cal_MODIS + int(modis_data[6])
                n_cloudy_cloudy_cal_MODIS = n_cloudy_cloudy_cal_MODIS + int(modis_data[7])

                current_datafile.close()
            
        samples_csa = n_clear_clear_csa + n_clear_cloudy_csa + n_cloudy_clear_csa +\
                      n_cloudy_cloudy_csa
        samples_cal = n_clear_clear_cal + n_clear_cloudy_cal + n_cloudy_clear_cal +\
                      n_cloudy_cloudy_cal
        mean_CFC_csa = 100.0*(n_cloudy_cloudy_csa+n_cloudy_clear_csa)/samples_csa
        mean_CFC_cal = 100.0*(n_cloudy_cloudy_cal+n_cloudy_clear_cal)/samples_cal
        bias_csa = float(n_clear_cloudy_csa - n_cloudy_clear_csa)/float(samples_csa)
        bias_cal = float(n_clear_cloudy_cal - n_cloudy_clear_cal)/float(samples_cal)
        bias_modis = float(n_clear_cloudy_cal_MODIS - n_cloudy_clear_cal_MODIS)/float(samples_cal-1)
        bias_csa_perc = 100.0*float(n_clear_cloudy_csa - n_cloudy_clear_csa)/float(samples_csa)
        bias_cal_perc = 100.0*float(n_clear_cloudy_cal - n_cloudy_clear_cal)/float(samples_cal)
        bias_modis_perc = 100.0*float(n_clear_cloudy_cal_MODIS - n_cloudy_clear_cal_MODIS)/float(samples_cal-1)

        square_sum_csa =  float(n_clear_clear_csa+n_cloudy_cloudy_csa)*bias_csa*bias_csa + \
                         n_cloudy_clear_csa*(-1.0-bias_csa)*(-1.0-bias_csa) + \
                         n_clear_cloudy_csa*(1.0-bias_csa)*(1.0-bias_csa)
        rms_csa = 100.0*math.sqrt(square_sum_csa/(samples_csa-1))
        square_sum_cal =  float(n_clear_clear_cal+n_cloudy_cloudy_cal)*bias_cal*bias_cal + \
                         n_cloudy_clear_cal*(-1.0-bias_cal)*(-1.0-bias_cal) + \
                         n_clear_cloudy_cal*(1.0-bias_cal)*(1.0-bias_cal)
        rms_cal = 100.0*math.sqrt(square_sum_cal/(samples_cal-1))
        square_sum_modis =  float(n_clear_clear_cal+n_cloudy_cloudy_cal)*bias_modis*bias_modis + \
                         n_cloudy_clear_cal*(-1.0-bias_modis)*(-1.0-bias_modis) + \
                         n_clear_cloudy_cal*(1.0-bias_modis)*(1.0-bias_modis)
        rms_modis = 100.0*math.sqrt(square_sum_modis/(samples_cal-1))

        print "Month is:  %s" % month
        print "Total number of matched scenes is: %s" % scenes
        print "Total number of Cloudsat matched FOVs: %d " % samples_csa
        print "Mean CFC Cloudsat: %f " % mean_CFC_csa
        print "Mean error: %f" % bias_csa_perc
        print "RMS error: %f" % rms_csa
        print
        print "Total number of CALIOP matched FOVs: %d" % samples_cal
        print "Mean CFC CALIOP: %f " % mean_CFC_cal
        print "Mean error: %f" % bias_cal_perc
        print "RMS error: %f" % rms_cal
        print "Mean error MODIS: %f" % bias_modis_perc
        print "RMS error MODIS: %f" % rms_modis
        print
    
        result.append("Month is:  %s\n" % month)
        result.append("Total number of matched scenes is: %s\n" % scenes)
        result.append("Total number of Cloudsat matched FOVs: %d\n" % samples_csa)
        result.append("Mean CFC Cloudsat: %f\n" % mean_CFC_csa)
        result.append("Mean error: %f\n" % bias_csa_perc)
        result.append("RMS error: %f\n" % rms_csa)
        result.append("\n")
        result.append("Total number of CALIOP matched FOVs: %d\n" % samples_cal)
        result.append("Mean CFC CALIOP: %f\n" % mean_CFC_cal)
        result.append("Mean error: %f\n" % bias_cal_perc)
        result.append("RMS error: %f\n" % rms_cal)
        result.append("Mean error MODIS: %f\n" % bias_modis_perc)
        result.append("RMS error MODIS: %f\n" % rms_modis)
        result.append("\n")
    fd=open("./Results/cfc_results_emissfilt_summary_%s%s-%s%s.dat" %(STUDIED_YEAR[0],STUDIED_MONTHS[0],STUDIED_YEAR[-1],STUDIED_MONTHS[-1]),'w')
    fd.writelines(result)
    fd.close()    
        
        
        
        

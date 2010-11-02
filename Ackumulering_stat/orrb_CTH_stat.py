# Program orrb_CTH_stat

# This program calculates basic statistics for the cloud top (CTH) product for
# each month

import string
import math

from orrb_stat_class import OrrbStats

# -----------------------------------------------------
class CloudTopStats(OrrbStats):
    def do_stats(self):
        from numpy import divide
        
        scenes = len(self.results_files)
        
        # First calculate total number of cases
        csa_samples = 0
        cal_all_samples = 0
        cal_low_samples = 0
        cal_medium_samples = 0
        cal_high_samples = 0
        mean_error_csa_sum = 0.0
        mean_error_cal_all_sum = 0.0
        mean_error_cal_low_sum = 0.0
        mean_error_cal_medium_sum = 0.0
        mean_error_cal_high_sum = 0.0
        rms_error_csa_sum = 0.0
        rms_error_cal_all_sum = 0.0
        rms_error_cal_low_sum = 0.0
        rms_error_cal_medium_sum = 0.0
        rms_error_cal_high_sum = 0.0
        for datafile in self.results_files:
            current_datafile = open(datafile, "r")
            datalist = current_datafile.readlines()
            current_datafile.close()
            
            csa_data = string.split(datalist[15])
            cal_all_data = string.split(datalist[16])
            cal_low_data = string.split(datalist[17])
            cal_medium_data = string.split(datalist[18])
            cal_high_data = string.split(datalist[19])
    
            # Accumulate CloudSat statistics
                                
            csa_samples = csa_samples + int(csa_data[6])
            mean_error_csa_sum = mean_error_csa_sum + int(csa_data[6])*float(csa_data[4])  
            rms_error_csa_sum = rms_error_csa_sum + int(csa_data[6])*float(csa_data[5])  
    
            
    
            # Accumulate CALIOP statistics
    
            cal_all_samples = cal_all_samples + int(cal_all_data[7])
            cal_low_samples = cal_low_samples + int(cal_low_data[7])
            cal_medium_samples = cal_medium_samples + int(cal_medium_data[7])
            cal_high_samples = cal_high_samples + int(cal_high_data[7])
            mean_error_cal_all_sum = mean_error_cal_all_sum + \
                                        int(cal_all_data[7])*float(cal_all_data[5])  
            mean_error_cal_low_sum = mean_error_cal_low_sum + \
                                        int(cal_low_data[7])*float(cal_low_data[5])  
            mean_error_cal_medium_sum = mean_error_cal_medium_sum + \
                                        int(cal_medium_data[7])*float(cal_medium_data[5])  
            mean_error_cal_high_sum = mean_error_cal_high_sum + \
                                        int(cal_high_data[7])*float(cal_high_data[5])  
    
    # Notice that the original linear averaging of RMS values is wrong! We have now changed to a correct averaging!/KG 20091126
    ##             rms_error_cal_all_sum = rms_error_cal_all_sum + \
    ##                                      int(cal_all_data[7])*float(cal_all_data[6])  
    ##             rms_error_cal_low_sum = rms_error_cal_low_sum + \
    ##                                      int(cal_low_data[7])*float(cal_low_data[6])  
    ##             rms_error_cal_medium_sum = rms_error_cal_medium_sum + \
    ##                                         int(cal_medium_data[7])*float(cal_medium_data[6])  
    ##             rms_error_cal_high_sum = rms_error_cal_high_sum + \
    ##                                       int(cal_high_data[7])*float(cal_high_data[6])  
            rms_error_cal_all_sum = rms_error_cal_all_sum + \
                                    int(cal_all_data[7])*float(cal_all_data[6])*float(cal_all_data[6])  
            rms_error_cal_low_sum = rms_error_cal_low_sum + \
                                    int(cal_low_data[7])*float(cal_low_data[6])*float(cal_low_data[6])  
            rms_error_cal_medium_sum = rms_error_cal_medium_sum + \
                                        int(cal_medium_data[7])*float(cal_medium_data[6])*float(cal_medium_data[6])  
            rms_error_cal_high_sum = rms_error_cal_high_sum + \
                                        int(cal_high_data[7])*float(cal_high_data[6])*float(cal_high_data[6])  
            
        
        # Check to see that we have some samples...
        tot_samples = [csa_samples, cal_all_samples, cal_low_samples, cal_medium_samples, cal_high_samples]
        if 0 in tot_samples:
            raise ValueError("Num samples: %s" % ', '.join([str(n) for n in tot_samples]))
        
        bias_csa = mean_error_csa_sum/csa_samples
        bias_cal_all = mean_error_cal_all_sum/cal_all_samples
        bias_cal_low = mean_error_cal_low_sum/cal_low_samples
        bias_cal_medium = mean_error_cal_medium_sum/cal_medium_samples
        bias_cal_high = mean_error_cal_high_sum/cal_high_samples
        rms_csa = rms_error_csa_sum/csa_samples
    
    
    # Notice that the original linear averaging of RMS values is wrong! We have now changed to a correct averaging!/KG 20091126
    ##         rms_cal_all = rms_error_cal_all_sum/cal_all_samples
    ##         rms_cal_low = rms_error_cal_low_sum/cal_low_samples
    ##         rms_cal_medium = rms_error_cal_medium_sum/cal_medium_samples
    ##         rms_cal_high = rms_error_cal_high_sum/cal_high_samples
    
        rms_cal_all = math.sqrt(rms_error_cal_all_sum/cal_all_samples)
        rms_cal_low = math.sqrt(rms_error_cal_low_sum/cal_low_samples)
        rms_cal_medium = math.sqrt(rms_error_cal_medium_sum/cal_medium_samples)
        rms_cal_high = math.sqrt(rms_error_cal_high_sum/cal_high_samples)
    
    ##         square_sum_csa =  float(n_clear_clear_csa+n_cloudy_cloudy_csa)*bias_csa*bias_csa + \
    ##                          n_cloudy_clear_csa*(-1.0-bias_csa)*(-1.0-bias_csa) + \
    ##                          n_clear_cloudy_csa*(1.0-bias_csa)*(1.0-bias_csa)
    ##         rms_csa = 100.0*math.sqrt(square_sum_csa/(samples_csa-1))
    ##         square_sum_cal =  float(n_clear_clear_cal+n_cloudy_cloudy_cal)*bias_cal*bias_cal + \
    ##                          n_cloudy_clear_cal*(-1.0-bias_cal)*(-1.0-bias_cal) + \
    ##                          n_clear_cloudy_cal*(1.0-bias_cal)*(1.0-bias_cal)
    ##         rms_cal = 100.0*math.sqrt(square_sum_cal/(samples_cal-1))
        
        self.scenes = scenes
        self.csa_samples = csa_samples
        self.bias_csa = bias_csa
        self.rms_csa = rms_csa
        self.cal_all_samples = cal_all_samples
        self.cal_low_samples = cal_low_samples
        self.cal_medium_samples = cal_medium_samples
        self.cal_high_samples = cal_high_samples
        self.bias_cal_all = bias_cal_all
        self.bias_cal_low = bias_cal_low
        self.bias_cal_medium = bias_cal_medium
        self.bias_cal_high = bias_cal_high
        self.rms_cal_all = rms_cal_all
        self.rms_cal_low = rms_cal_low
        self.rms_cal_medium = rms_cal_medium
        self.rms_cal_high = rms_cal_high
    
    
    def printout(self):
        lines = []
        lines.append("Total number of matched scenes is: %s" % self.scenes)
        lines.append("Total number of Cloudsat matched cloudtops: %d " % self.csa_samples)
        lines.append("Mean error: %f" % self.bias_csa)
        lines.append("Weighted RMS error: %f" % self.rms_csa)
        #lines.append("RMS error: %f" % self.rms_csa)
        lines.append("")
        lines.append("Total number of CALIOP matched cloudtops: %d" % self.cal_all_samples)
        lines.append("Number of CALIOP matched low cloudtops: %d" % self.cal_low_samples)
        lines.append("Number of CALIOP matched medium cloudtops: %d" % self.cal_medium_samples)
        lines.append("Number of CALIOP matched high cloudtops: %d" % self.cal_high_samples)
        lines.append("Mean error total cases: %f" % self.bias_cal_all)
        lines.append("Mean error low-level cases: %f" % self.bias_cal_low)
        lines.append("Mean error medium-level cases: %f" % self.bias_cal_medium)
        lines.append("Mean error high-level cases: %f" % self.bias_cal_high)
        lines.append("Weighted RMS error total cases: %f" % self.rms_cal_all)
        lines.append("Weighted RMS error low-level cases: %f" % self.rms_cal_low)
        lines.append("Weighted RMS error medium-level cases: %f" % self.rms_cal_medium)
        lines.append("Weighted RMS error high-level cases: %f" % self.rms_cal_high)
        lines.append("")
        
        return lines


if __name__ == "__main__":
    stats = CloudTopStats()
    stats.old_interface(modes=['BASIC'], output_file_desc="cth_results_summary")
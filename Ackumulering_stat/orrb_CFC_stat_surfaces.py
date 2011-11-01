# Program orrb_CFC_stat_surfaces

# This program calculates basic statistics for the cloud amount (CFC) product for
# each month

from orrb_CFC_stat import CloudFractionStats
# -----------------------------------------------------
class CloudFractionSurfacesStats(CloudFractionStats):
    
    def printout(self):
        try:
            lines = []
            lines.append("Total number of matched scenes is: %s" % self.scenes)
            lines.append("")
            lines.append("Total number of CALIOP matched FOVs: %d" % self.samples_cal)
            lines.append("Mean CFC CALIOP: %f" % self.mean_CFC_cal)
            lines.append("Mean error: %f" % self.bias_cal_perc)
            lines.append("RMS error: %f" % self.rms_cal)
            lines.append("Mean error MODIS: %f" % self.bias_modis_perc)
            lines.append("RMS error MODIS: %f" % self.rms_modis)
            lines.append("")
        except AttributeError:
            lines = []
            lines.append("Total number of matched scenes is: %s" % self.scenes)
            lines.append("")
            lines.append("Total number of CALIOP matched FOVs: %d" % self.samples_cal)
            lines.append("Mean CFC CALIOP: %f" % self.mean_CFC_cal)
            lines.append("Mean error: %f" % self.bias_cal_perc)
            lines.append("RMS error: %f" % self.rms_cal)
            lines.append("")
        return lines


if __name__ == "__main__":
    import config
    stats = CloudFractionSurfacesStats()
    stats.old_interface(modes=config.SURFACES, output_file_desc="cfc_results_surfaces_summary")
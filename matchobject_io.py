#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, 2014 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c14526.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Read Calipso/VIIRS/AVHRR matchup data object from hdf5 file
"""

import numpy as np

class DataObject(object):
    """
    Class to handle data objects with several arrays.
    
    """
    def __getattr__(self, name):
        try:
            return self.all_arrays[name]
        except KeyError:
            raise AttributeError("%s instance has no attribute '%s'" % (self.__class__.__name__, name))
    
    def __setattr__(self, name, value):
        if name == 'all_arrays':
            object.__setattr__(self, name, value)
        else:
            self.all_arrays[name] = value

    def __add__(self, other):
        """Adding two objects together"""
        for key in self.all_arrays:
            try:
                if self.all_arrays[key].ndim != self.all_arrays[key].ndim:
                    raise ValueError("Can't concatenate arrays " + 
                                     "of different dimensions!")
            except AttributeError, e:
                #print "Don't concatenate member " + key + "... " + str(e)
                self.all_arrays[key] = other.all_arrays[key]
                continue

            try:
                if self.all_arrays[key].ndim == 1:  
                    self.all_arrays[key] = np.concatenate([self.all_arrays[key],
                                                           other.all_arrays[key]])
                elif self.all_arrays[key].ndim == 2: 
                    self.all_arrays[key] = np.concatenate([self.all_arrays[key],
                                                           other.all_arrays[key]], 1)
                        
            except ValueError, e:
                #print "Don't concatenate member " + key + "... " + str(e)
                self.all_arrays[key] = other.all_arrays[key]
        return self

    def mask_nodata(self, nodata):
        for key in self.all_arrays:
            if key in ['latitude']:
                pass
            else:
                try:
                    self.all_arrays[key] = np.ma.array(self.all_arrays[key], mask = self.all_arrays[key]<=nodata)
                except:
                    print "cloud not mask %s"%(key)
            
            
class ppsAvhrrObject(DataObject):
    def __init__(self):
        DataObject.__init__(self)                            
        self.all_arrays = {
            'longitude': None,
            'latitude': None,
            'sec_1970': None,
            'ctth_height': None,
            'ctth_pressure': None,
            'ctth_temperature': None,
            'ctth_opaque': None,  # True if opaque retrieval was applied
            'cloudtype': None,
            'cloudtype_qflag': None,
            'cloudtype_phaseflag': None,
            'cloudtype_quality': None,
            'cloudtype_conditions': None,
            'cloudtype_status': None,
            'ctth_status': None,
            'surftemp': None,
            't500': None,
            't700': None,
            't850': None,
            't950': None,
            'ttro': None,
            'ciwv': None,
            'r06micron': None,
            'r09micron': None,
            'bt37micron': None,
            'bt11micron': None,
            'bt12micron': None,
            'bt86micron': None,
            'bt22micron': None,
            'bt13micron': None,
            'r16micron': None,
            'text_r06': None,
            'text_t11': None,
            'text_t37t12': None,
            'text_t37': None,
            'thr_t11ts_inv': None,
            'thr_t11t37_inv': None,
            'thr_t37t12_inv': None,
            'thr_t11t12_inv': None,
            'thr_t85t11_inv': None,
            'thr_t11ts': None,
            'thr_t11t37': None,
            'thr_t37t12': None,
            'thr_t11t12': None,  
            'thr_t85t11': None, 
            'thr_r06': None, 
            'thr_r09': None, 
            'satz': None,
            'sunz': None,
            'azidiff': None,
            'lwp': None,
            'emis1': None,
            'emis8': None,
            'emis9': None,
            }
        
        
class CalipsoObject(DataObject):
    def __init__(self):
        DataObject.__init__(self)                            
        self.all_arrays = {
            'longitude': None,
            'latitude': None,
            'avhrr_linnum': None,
            'avhrr_pixnum': None,
            'cloud_fraction': None,
            'cloud_top_profile': None,
            'cloud_top_pressure': None,
            'cloud_base_profile': None,
            'cloud_mid_temperature': None,
            'number_of_layers_found': None,
            'igbp': None,
            'nsidc': None,
            'nsidc_texture': None,
            'elevation': None,
            'time': None,
            'utc_time': None, 
            'sec_1970': None,
            'feature_classification_flags': None,
            'day_night_flag': None,
            'optical_depth': None,
            'optical_depth_uncertainty': None,
            'single_shot_cloud_cleared_fraction': None,
            #If a combination of 5 and 1km data are used for RESOLUTION=1
            #A vector with the corresponding optical thickness for 5km data
            # is stored also for 1km data. Because of that I put the 5km in the name
            #/2013-08-17/Nina
            'optical_depth_top_layer5km': None,
            'lidar_surface_elevation': None,
            'horizontal_averaging5km': None,
            'opacity5km': None,
            'ice_water_path5km': None,
            'ice_water_path_uncertainty5km': None,
            'detection_height_5km': None,
            'total_optical_depth_5km': None
            }



class CalipsoAvhrrTrackObject:
    def __init__(self):
        self.avhrr = ppsAvhrrObject()
        self.calipso = CalipsoObject()
        self.diff_sec_1970 = None

    def make_nsidc_texture(self, kernel_sz = 51):
        """Derive the stdv of the ice dataset"""

        self.calipso.all_arrays['nsidc_texture'] = sliding_std(self.calipso.all_arrays['nsidc'], kernel_sz)
    
    def __add__(self, other):
        """Concatenating two objects together"""
        self.avhrr = self.avhrr + other.avhrr
        self.calipso = self.calipso + other.calipso
        try:
            self.diff_sec_1970 = np.concatenate([self.diff_sec_1970,
                                                 other.diff_sec_1970])
        except ValueError, e:
            #print "Don't concatenate member diff_sec_1970... " + str(e)
            self.diff_sec_1970 = other.diff_sec_1970

        return self


# ----------------------------------------
def readCaliopAvhrrMatchObj(filename):
    import h5py #@UnresolvedImport
    
    retv = CalipsoAvhrrTrackObject()
    
    h5file = h5py.File(filename, 'r')
    for group, data_obj in [(h5file['/calipso'], retv.calipso),
                            (h5file['/avhrr'], retv.avhrr)]:
        for dataset in group.keys():        
            if dataset in data_obj.all_arrays.keys():
                data_obj.all_arrays[dataset] = group[dataset].value

    retv.diff_sec_1970 = h5file['diff_sec_1970'].value

    h5file.close()

    retv.make_nsidc_texture()
    return retv

# ----------------------------------------
def writeCaliopAvhrrMatchObj(filename, ca_obj):
    """
    Write *ca_obj* to *filename*.
    
    """
    from common import write_match_objects
    groups = {'calipso': ca_obj.calipso.all_arrays,
              'avhrr': ca_obj.avhrr.all_arrays}
    write_match_objects(filename, ca_obj.diff_sec_1970, groups)    

    status = 1
    return status


def sliding_std(x, size=5):
    """derive a sliding standard deviation of a data array"""
    from scipy.ndimage.filters import uniform_filter
    c1 = uniform_filter(x.astype('float'), size=size)
    c2 = uniform_filter(x.astype('float')*x.astype('float'), size=size)
    return abs(c2 - c1*c1)**.5



# ----------------------------------------
if __name__ == "__main__":

    import os.path
    TESTDIR = ("/local_disk/laptop/NowcastingSaf/FA/cloud_week_2013may" + 
               "/atrain_matchdata/2012/10/arctic_europe_1km")
    TESTFILE = os.path.join(TESTDIR, 
                            "1km_npp_20121012_1246_04968_caliop_viirs_match.h5")
    TESTFILE2 = os.path.join(TESTDIR,
                             "1km_npp_20121004_0700_04851_caliop_viirs_match.h5")
    caObj = readCaliopAvhrrMatchObj(TESTFILE)
    caObj2 = readCaliopAvhrrMatchObj(TESTFILE2)

    caObj = caObj + caObj2

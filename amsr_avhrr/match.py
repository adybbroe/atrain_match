"""
Match AMSR and AVHRR data

"""

from __future__ import with_statement
import numpy as np
import logging
logger = logging.getLogger(__name__)


class MatchMapper(object):
    """
    Map arrays from one swath to another.
    
    """
    def __init__(self, rows, cols, pixel_mask, time_diff=None,
                 time_threshold=None):
        self._rows = rows
        self._cols = cols
        self._pixel_mask = pixel_mask
        self._time_diff = time_diff
        self.time_threshold = time_threshold
    
    def __call__(self, array):
        """
        Maps *array* to target swath.
        
        """
        return np.ma.array(array[self.rows, self.cols], mask=self.mask)
    
    @property
    def rows(self):
        return np.ma.array(self._rows, mask=self.mask, fill_value=-1,
                           hard_mask=True)
    
    @property
    def cols(self):
        return np.ma.array(self._cols, mask=self.mask, fill_value=-1,
                           hard_mask=True)
    
    @property
    def time_diff(self):
        """Time difference in seconds"""
        if self._time_diff is None:
            return None
        # Only use pixel mask
        return np.ma.array(self._time_diff, mask=self._pixel_mask,
                           fill_value=np.inf, hard_mask=True)
    
    @time_diff.setter
    def time_diff(self, value):
        self._time_diff = value
    
    @property
    def mask(self):
        if not None in (self.time_diff, self.time_threshold):
            return (self._pixel_mask +
                    (abs(self.time_diff) > self.time_threshold))
        return self._pixel_mask
    
    def write(self, filename):
        """
        Write mapper to hdf5 file *filename*.
        
        """
        import h5py
        
        with h5py.File(filename, 'w') as f:
            f.create_dataset('rows', data=self.rows.filled())
            f.create_dataset('cols', data=self.cols.filled())
            f.create_dataset('pixel_mask', data=self._pixel_mask)
            if self.time_diff is not None:
                f.create_dataset('time_diff', data=self.time_diff.filled())
            if self.time_threshold is not None:
                f.attrs['time_threshold'] = self.time_threshold
    
    @classmethod
    def from_file(cls, filename):
        """
        Create a mapper from contents of *filename*.
        
        """
        import h5py
        
        with h5py.File(filename, 'r') as f:
            rows = f['rows'][:]
            cols = f['cols'][:]
            pixel_mask = f['pixel_mask'][:]
            time_diff = None
            time_threshold = None
            try:
                time_diff = f['time_diff'][:]
            except KeyError:
                pass
            try:
                time_threshold = f.attrs['time_threshold']
            except KeyError:
                pass
        
        return cls(rows=rows, cols=cols, pixel_mask=pixel_mask,
                   time_diff=time_diff, time_threshold=time_threshold)


def match_lonlat(source, target, radius_of_influence=1e3, n_neighbours=1):
    """
    Produce a masked array of the same shape as the arrays in *target*, with
    indices of nearest neighbours in *source*. *source* and *target* should be
    tuples (lon, lat) of the source and target swaths, respectively.
    
    Note::
    
        Fastest matching is obtained when *target* has lower resolution than
        *source*.
    
    """
    from pyresample.geometry import SwathDefinition
    from pyresample.kd_tree import get_neighbour_info
    
    source_def = SwathDefinition(*source)
    target_def = SwathDefinition(*target)
    
    valid_in, valid_out, indices, distances = get_neighbour_info( #@UnusedVariable
        source_def, target_def, radius_of_influence, neighbours=n_neighbours)
    
    indices.shape = target_def.shape
    distances.shape = target_def.shape
    
    rows = indices // source_def.shape[1]
    cols = indices % source_def.shape[1]
    # Make sure all indices are valid
    rows[rows >= source_def.shape[0]] = -1
    cols[cols >= source_def.shape[1]] = -1
    mask = distances > radius_of_influence
    
    return MatchMapper(rows, cols, mask)


def match(amsr_filename, avhrr_filename, radius_of_influence=1e3,
          time_threshold=None):
    """
    Find matching indices in AVHRR array for each element in AMSR swath.
    
    Arguments:
    
        amsr_filename: string
            full path of AMSR-E HDF5 file
        avhrr_filename: string
            full path of AVHRR PPS HDF5 file
        radius_of_influence: float
            radius of influence in meters in pixel-pixel matching (default: 1000 m)
        time_threshold: float
            largest absolute time difference to include in match
    
    Returns:
    
        mapper: `MatchMapper` instance.
    
    """
    from .util import get_amsr_lonlat, get_avhrr_lonlat
    from .util import get_amsr_time, get_avhrr_time
    
    avhrr_lonlat = get_avhrr_lonlat(avhrr_filename)
    amsr_lonlat = get_amsr_lonlat(amsr_filename)
    
    mapper = match_lonlat(avhrr_lonlat, amsr_lonlat, radius_of_influence)
    
    avhrr_time = get_avhrr_time(avhrr_filename)
    amsr_time = get_amsr_time(amsr_filename)
    
    time_diff = np.abs(avhrr_time[mapper.rows] - amsr_time.reshape((amsr_time.size, 1)))
    
    mapper.time_diff = time_diff
    mapper.time_threshold = time_threshold
    
    logger.debug("Time diff (min, max): %r" % ((time_diff.min(),
                                                time_diff.max()),))
    
    return mapper


def find_amsr(avhrr_filename):
    """
    Find AMSR-E files matching *avhrr_filename*. Returns a list of file paths.
    
    """
    from file_finders import AmsrFileFinder, PpsFileFinder
    pps_finder = PpsFileFinder()
    parsed = pps_finder.parse(avhrr_filename)
    
    # Limit matching to AMSR-E files starting 45 min (duration of one half
    # orbit) before up to 20 min (duration of one EARS AVHRR swath) after the
    # start of the AVHRR swath
    amsr_finder = AmsrFileFinder(time_window=(-45 * 60, 20 * 60))
    return amsr_finder.find(parsed['datetime'])


def validate_lwp(amsr_lwp, cpp_lwp, sea, threshold=170, plotting=False):
    """
    Compare liquid water path, lwp, in *amsr_filename* and *cpp_filename* files.
    False pixels in *sea* are masked out. Only values above *threshold* (g
    m**-2) are considered.
    
    """
    amsr_masked = np.ma.array(amsr_lwp, mask=~sea + (amsr_lwp < threshold))
    cpp_masked = np.ma.array(cpp_lwp, mask=~sea)
    
    diff = amsr_masked - cpp_masked
    
    print('=' * 40)
    print("AMSR-E lwp - CPP cwp")
    print("Non-sea pixels screened out")
    print("Pixels where AMSR-E lwp < %r g m**-2 screened out" % threshold)
    print("Number of pixels in comparison: %d" % diff.compressed().size)
    print("bias:    %.4g" % diff.mean())
    print("std:     %.4g" % diff.std())
    print("rel std: %.4g %%" % abs(100. * diff.std() / diff.mean()))
    
    if plotting:
        from matplotlib import pyplot as pl
        fig = pl.figure()
        ax = fig.add_subplot(111)
        ax.hist(diff.compressed())
        return fig

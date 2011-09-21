"""
Match AMSR and AVHRR data

"""

from __future__ import with_statement
import numpy as np
import logging
logger = logging.getLogger(__name__)


#: Default threshold for lwp screening [kg m**-2]
LWP_THRESHOLD = 170


class MatchError(RuntimeError):
    """Match error occurred"""


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
            if 'time_diff' in f.keys():
                time_diff = f['time_diff'][:]
            else:
                time_diff = None
            if 'time_threshold' in f['time_diff'].attrs.keys():
                time_threshold = f['time_diff'].attrs['time_threshold']
            else:
                time_threshold = None
        
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
    
    logger.debug("Matching %d nearest neighbours" % n_neighbours)
    valid_in, valid_out, indices, distances = get_neighbour_info( #@UnusedVariable
        source_def, target_def, radius_of_influence, neighbours=n_neighbours)
    
    shape = list(target_def.shape)
    shape.append(n_neighbours)
    indices.shape = shape
    distances.shape = shape
    
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
            radius of influence in meters in pixel-pixel matching (default:
            1000 m)
        time_threshold: float
            largest absolute time difference to include in match
    
    Returns:
    
        mapper: `MatchMapper` instance.
    
    """
    from .util import get_amsr_lonlat, get_avhrr_lonlat
    from .util import get_amsr_time, get_avhrr_time
    
    avhrr_lonlat = get_avhrr_lonlat(avhrr_filename)
    amsr_lonlat = get_amsr_lonlat(amsr_filename)
    
    mapper = match_lonlat(avhrr_lonlat, amsr_lonlat, radius_of_influence,
                          n_neighbours=8)
    
    avhrr_time = get_avhrr_time(avhrr_filename)
    amsr_time = get_amsr_time(amsr_filename)
    
    time_diff = np.abs(avhrr_time[mapper.rows] -
                       amsr_time.reshape((amsr_time.size, 1, 1))).astype(np.float32)
    
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


def screen_lwp(amsr_lwp, cpp_lwp, sea, lat, threshold=LWP_THRESHOLD):
    """
    Screen lwp pixels based on *sea* mask, amsr < threshold, and cpp_lwp < 0.
    
    Returns an bool array with screened out pixels set to True, suitable for
    creating masked arrays.
    
    """
    def show_mask(mask, screened):
        return # Don't use
        
        from matplotlib import pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(111)
        im = ax.imshow(mask[..., 0])
        fig.colorbar(im)
        ax.set_title(', '.join(screened))
        fig.savefig('mask%d.png' % len(screened))
    
    mask = np.zeros(sea.shape, dtype=np.bool)
    screened = []
    
    mask |= ~sea
    screened.append('non-sea')
    show_mask(mask, screened)
    
    mask |= (amsr_lwp < threshold)
    screened.append('AMSR-E lwp < %r g m**-2' % threshold)
    show_mask(mask, screened)
    
    mask |= (cpp_lwp < 0)
    screened.append('CPP lwp < 0')
    show_mask(mask, screened)
    
    mask |= (abs(lat) > 70)
    screened.append('abs(lat) > 70 degrees')
    show_mask(mask, screened)
    
    return mask, screened


def validate_lwp(amsr_lwp, cpp_lwp, sea, lat, threshold=LWP_THRESHOLD):
    """
    Compare liquid water path, lwp, in *amsr_filename* and *cpp_filename* files.
    False pixels in *sea* are masked out. Only values above *threshold* (g
    m**-2) are considered.
    
    """
    # Screen out undesired pixels
    amsr_lwp_3d = amsr_lwp.reshape(amsr_lwp.shape[0], amsr_lwp.shape[1], 1)
    lat_3d = lat.reshape(lat.shape[0], lat.shape[1], 1)
    mask, screened = screen_lwp(amsr_lwp_3d, cpp_lwp, sea, lat_3d, threshold)
    mask_n0 = mask[..., 0] # Nearest neighbour mask
    if mask_n0.all():
        logger.warning("No matches after screening")
        raise MatchError("No matches after screening")
    amsr_masked = np.ma.array(amsr_lwp, mask=mask_n0)
    cpp_masked = np.ma.array(cpp_lwp, mask=mask)
    
    # Use average of all AVHRR pixels in AMSR footprint
    assert len(cpp_masked.shape) == 3
    cpp_masked = cpp_masked.mean(axis=-1)
    
    lwp_diff = amsr_masked - cpp_masked
    
    print('=' * 40)
    print("AMSR-E lwp - CPP cwp")
    print("Screened out pixels: %s" % ', '.join(screened))
    print("Number of pixels in comparison: %d" % lwp_diff.compressed().size)
    print("bias:    %.4g" % lwp_diff.mean())
    print("std:     %.4g" % lwp_diff.std())
    print("rel std: %.4g %%" % abs(100. * lwp_diff.std() / lwp_diff.mean()))
    
    return lwp_diff, screened

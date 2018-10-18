# -*- coding: utf-8 -*-
#
# test_match.py
"""for the match module match.py """
#
import numpy as np
import unittest
from utils.pps_prototyping_util import  (get_warmest_or_coldest_index)
from matchobject_io import CalipsoObject
def get_warmest_index_old(t11,  matched):
    from scipy.ndimage.filters import generic_filter
    row, col = np.indices(t11.shape)
    flat_index = generic_filter(t11,
                                function=np.argmax,
                                size=5,
                                mode='constant',
                                cval=-9999999999999)
    flat_index = np.array(flat_index, dtype=np.int)
    delta_row, delta_col = np.unravel_index(flat_index, (5,5))
    delta_row = delta_row - 2
    delta_col = delta_col - 2    
    new_row = row+delta_row
    new_col = col+delta_col
    new_row_matched = np.array([new_row[matched['row'][idx], matched['col'][idx]]
                       for idx in range(matched['row'].shape[0])]) 
    new_col_matched = np.array([new_col[matched['row'][idx], matched['col'][idx]]
                       for idx in range(matched['row'].shape[0])])
    return new_row_matched, new_col_matched




class test_prototyping_utils(unittest.TestCase): 

    def setUp(self):
        
        self.t11 = np.array([[1,43,3,4,5,6,7,8,9,35],
                            [ 1,2,3,4,5,6,7,8,9,10],
                            [ 1,2,3,4,25,6,7,8,9,10],
                            [ 1,2,3,4,5,6,7,8,9,101],
                             [ 11,2,3,4,5,6,7,8,9,101]])

        
        self.matched = {'row': np.array([0,0,1,1,2,2,3,3,4,4]),
                        'col': np.array([0,1,2,3, 4, 5, 6, 7,8,9])}



    def test_warmest(self):
        retv = get_warmest_or_coldest_index(self.t11, self.matched)
        out_r = retv['row']
        out_c = retv['col']
        out_r2, out_c2 = get_warmest_index_old(self.t11, self.matched)

        self.assertTrue((out_r[0:4]== [0,0,0,0]).all())
        self.assertTrue((out_c[0:4] ==[1,1,1,1]).all())
        self.assertTrue((out_r[4:7] ==[2,2,2]).all())
        self.assertTrue((out_c[4:7] ==[4,4,4]).all())
        self.assertTrue((out_c[7:10] ==[9,9,9]).all())
        self.assertTrue((out_c ==  out_c2).all())
        self.assertTrue((out_r == out_r2).all())
def suite():
    """The suite for test_utils.
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(test_prototyping_utils))
    return mysuite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())

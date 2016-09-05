import numpy as np
from pyresample import utils
from pyresample.geometry import SwathDefinition
from pyresample.kd_tree import get_neighbour_info
from pyresample.kd_tree import get_sample_from_neighbour_info
import pyresample as pr
import os
from scipy import ndimage
import matplotlib
#matplotlib.use("TkAgg")
from matchobject_io import DataObject        
class ppsMatch_Imager_CalipsoObject(DataObject):
    def __init__(self):
        DataObject.__init__(self)                            
        self.all_arrays = {
            'detected_clouds': None,
            'undetected_clouds': None,
            'false_clouds': None,
            'detected_clear': None,
            'new_detected_clouds': None,
            'new_false_clouds': None,
            'lats': None,
            'lons': None}
    def get_some_info_from_caobj(self, caObj, isGAC=True,  method='KG', DNT='All'):
        self.set_false_and_missed_cloudy_and_clear(caObj=caObj, 
                                                   isGAC=isGAC, method=method, DNT=DNT)
        self.set_r13_extratest(caObj=caObj)
        self.get_lapse_rate(caObj=caObj)
        self.get_ctth_bias_low(caObj=caObj)
        self.get_ctth_bias_low_temperature(caObj=caObj)
        self.height_bias_type={}
        self.detected_height_type={}
        for cc_type in xrange(8):
            self.get_ctth_bias_type(caObj=caObj, calipso_cloudtype=cc_type)

    def set_false_and_missed_cloudy_and_clear(self, caObj, 
                                              isGAC=True,  method='KG', DNT='All' ):
        isCloudyPPS = np.logical_and(caObj.avhrr.all_arrays['cloudtype']>4,
                                     caObj.avhrr.all_arrays['cloudtype']<21) 
        isClearPPS = np.logical_and(caObj.avhrr.all_arrays['cloudtype']>0,
                                    caObj.avhrr.all_arrays['cloudtype']<5)
        nlay =np.where(caObj.calipso.all_arrays['number_layers_found']>0,1,0)
        meancl=ndimage.filters.uniform_filter1d(nlay*1.0, size=3)
        if method == 'KG' and isGAC:
            isCalipsoCloudy = np.logical_and(
                caObj.calipso.all_arrays['cloud_fraction']>0.5,
                caObj.calipso.all_arrays['total_optical_depth_5km']>0.15)
            isCalipsoClear = np.not_equal(isCalipsoCloudy, True)
        elif method == 'Nina' and isGAC:    
            isCalipsoCloudy = np.logical_and(
                nlay > 0, 
                caObj.calipso.all_arrays['cloud_fraction']>0.5)
            isCalipsoCloudy = np.logical_and(
                isCalipsoCloudy, 
                caObj.calipso.all_arrays['total_optical_depth_5km']>0.15)
            isCalipsoClear = np.logical_and(nlay == 0, meancl<0.01)
            isCalipsoClear = np.logical_and(
                isCalipsoClear, 
                caObj.calipso.all_arrays['total_optical_depth_5km']<0)
        elif method == 'KG':
            isCalipsoCloudy = nlay>0
            isCalipsoClear = np.not_equal(isCalipsoCloudy, True)   
        elif method == 'Nina':
            isCalipsoCloudy = np.logical_or(
                caObj.calipso.all_arrays['total_optical_depth_5km']>0.15, 
                np.logical_and(caObj.calipso.all_arrays['total_optical_depth_5km']<0,
                               nlay>0))
            isCalipsoClear = np.logical_and(nlay == 0, meancl<0.01)
            isCalipsoClear = np.logical_and(
                isCalipsoClear,
                caObj.calipso.all_arrays['total_optical_depth_5km']<0)
        sunz = caObj.avhrr.all_arrays['sunz']       
        if DNT in ["day"]:
            isCloudyPPS = np.logical_and(isCloudyPPS,  sunz<=80)
            isClearPPS =  np.logical_and(isClearPPS,  sunz<=80)
        if DNT in ["night"]:
            isCloudyPPS = np.logical_and(isCloudyPPS,  sunz>=95)
            isClearPPS =  np.logical_and(isClearPPS,  sunz>=95)
        if DNT in ["twilight"]:
            isCloudyPPS = np.logical_and(isCloudyPPS,  sunz>80)
            isClearPPS =  np.logical_and(isClearPPS,  sunz>80)
            isCloudyPPS = np.logical_and(isCloudyPPS,  sunz<95)
            isClearPPS =  np.logical_and(isClearPPS,  sunz<95)                  
        if DNT in ["all"]:
            pass
        undetected_clouds = np.logical_and(isCalipsoCloudy, isClearPPS)
        false_clouds = np.logical_and(isCalipsoClear, isCloudyPPS)
        detected_clouds = np.logical_and(isCalipsoCloudy, isCloudyPPS)
        detected_clear = np.logical_and(isCalipsoClear, isClearPPS)
        use = np.logical_or(np.logical_or(detected_clouds, detected_clear),
                            np.logical_or(false_clouds, undetected_clouds))
        detected_height = np.logical_and(detected_clouds,
                                         caObj.avhrr.all_arrays['ctth_height']>-9)
        detected_height = np.logical_and(detected_height,
                                         caObj.calipso.all_arrays['layer_top_altitude'][:,0]>-1)
        detected_temperature = np.logical_and(detected_clouds,
                                       caObj.avhrr.all_arrays['ctth_temperature']>-9)

        self.false_clouds = false_clouds[use]
        self.detected_clouds = detected_clouds[use]
        self.undetected_clouds = undetected_clouds[use]
        self.detected_clear = detected_clear[use]
        self.latitude = caObj.avhrr.latitude[use]
        self.longitude = caObj.avhrr.longitude[use] 
        self.use = use
        self.detected_height = detected_height[use]
        self.detected_temperature = detected_temperature[use]

    def set_r13_extratest(self,caObj):
        if np.size(caObj.avhrr.all_arrays['r13micron'])==1 and caObj.avhrr.all_arrays['r13micron'] is None:
            self.new_false_clouds = np.zeros(self.false_clouds.shape)
            self.new_detected_clouds = np.zeros(self.false_clouds.shape)  
            return
        r13 = caObj.avhrr.all_arrays['r13micron']
        sunz =  caObj.avhrr.all_arrays['sunz']
        sunz_cos = sunz.copy()
        sunz_cos[sunz>87] =87    
        r13[sunz<90] = r13[sunz<90]/np.cos(np.radians(sunz_cos[sunz<90]))
        isCloud_r13 = np.logical_and(r13>2.0, caObj.avhrr.all_arrays['ciwv']>3)
        new_detected_clouds = np.logical_and(self.detected_clouds,
                                             isCloud_r13[self.use])
        new_false_clouds = np.logical_and(self.detected_clear,
                                          isCloud_r13[self.use])
        self.new_false_clouds = new_false_clouds
        self.new_detected_clouds = new_detected_clouds
        
    def get_lapse_rate(self, caObj):
        if np.size(caObj.avhrr.all_arrays['surftemp'])==1 and caObj.avhrr.all_arrays['surftemp'] is None:
            self.lapse_rate = np.zeros(self.false_clouds.shape)
            return
        from get_flag_info import get_calipso_low_clouds
        low_clouds = get_calipso_low_clouds(caObj)
        delta_h = caObj.calipso.all_arrays['layer_top_altitude'][:,0] - 0.001*caObj.calipso.all_arrays['elevation'][:]
        delta_t = (273.15 + caObj.calipso.all_arrays['layer_top_temperature'][:,0] - caObj.avhrr.all_arrays['surftemp'][:])
        lapse_rate = delta_t/delta_h
        lapse_rate[caObj.calipso.all_arrays['layer_top_temperature'][:,0]<-500] = 0
        lapse_rate[caObj.calipso.all_arrays['layer_top_altitude'][:,0]>35.0] = 0
        lapse_rate[low_clouds] = 0.0
        self.lapse_rate = lapse_rate[self.use]

    def get_ctth_bias_low(self, caObj):
        from get_flag_info import get_calipso_low_clouds
        low_clouds = get_calipso_low_clouds(caObj)
        detected_low = np.logical_and(self.detected_height, low_clouds[self.use])
        height_c = 1000*caObj.calipso.all_arrays['layer_top_altitude'][self.use,0] - caObj.calipso.all_arrays['elevation'][self.use]
        height_pps = caObj.avhrr.all_arrays['ctth_height'][self.use]
        delta_h = height_pps - height_c
        delta_h[~detected_low]=0
        self.height_bias_low = delta_h
        self.detected_height_low = detected_low
        try:
            temperature_pps = caObj.avhrr.all_arrays['ctth_temperature'][self.use]
            temp_diff = temperature_pps - caObj.avhrr.all_arrays['surftemp'][self.use]
            rate = -1.0/5.0 #-5K per kilometer
            self.lapse_bias_low = rate*temp_diff*1000 - height_c
        except:
            self.lapse_bias_low = 0* height_c
        self.lapse_bias_low[~detected_low]=0
        self.lapse_bias_low[temperature_pps<0]=0

    def get_ctth_bias_low_temperature(self, caObj):
        from get_flag_info import get_calipso_low_clouds
        low_clouds = get_calipso_low_clouds(caObj)
        detected_low = np.logical_and(self.detected_height, low_clouds[self.use])
        temperature_c = 273.15 + caObj.calipso.all_arrays['midlayer_temperature'][self.use,0]
        temperature_pps = caObj.avhrr.all_arrays['ctth_temperature'][self.use]
        delta_t = temperature_pps - temperature_c
        delta_t[~detected_low]=0
        delta_t[temperature_c<0]=0
        delta_t[temperature_pps<0]=0
        temperature_pps = caObj.avhrr.all_arrays['bt11micron'][self.use]
        delta_t_t11 = temperature_pps - temperature_c
        delta_t_t11[~detected_low]=0
        delta_t_t11[temperature_c<0]=0
        delta_t_t11[temperature_pps<0]=0
        self.temperature_bias_low =delta_t
        self.temperature_bias_low[~detected_low]=0
        self.temperature_bias_low_t11 = delta_t_t11

    def get_ctth_bias_type(self, caObj, calipso_cloudtype=0):
        from get_flag_info import get_calipso_clouds_of_type_i
        wanted_clouds = get_calipso_clouds_of_type_i(caObj, calipso_cloudtype=calipso_cloudtype)
        detected_typei = np.logical_and(self.detected_height, wanted_clouds[self.use])
        height_c = 1000*caObj.calipso.all_arrays['layer_top_altitude'][self.use,0] - caObj.calipso.all_arrays['elevation'][self.use]
        height_pps = caObj.avhrr.all_arrays['ctth_height'][self.use]
        delta_h = height_pps - height_c
        delta_h[~detected_typei]=0
        self.height_bias_type[calipso_cloudtype] = delta_h
        self.detected_height_type[calipso_cloudtype] = detected_typei




class ppsStatsOnFibLatticeObject(DataObject):
    def __init__(self):
        DataObject.__init__(self)                            
        self.all_arrays = {
            'definition': None,
            'lats': None,
            'lons': None,
            'N_false_clouds': None,
            'Min_lapse_rate': None,
            'N_detected_clouds': None,
            'N_new_false_clouds': None,
            'N_new_detected_clouds': None,
            'N_undetected_clouds': None,
            'N_detected_clear': None,
            'N_clear':None,
            'N_clouds':None,
            'N': None,
            'Kuipers': None}  
    def set_flattice(self, radius_km=200):
        self.radius_km = radius_km
        self.lons, self.lats =get_fibonacci_spread_points_on_earth(radius_km = radius_km)
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize = (36,18))
        ax = fig.add_subplot(111)
        plt.plot(self.lons,self.lats,'b*')
        #plt.show()
        self.Sum_ctth_bias_low = np.zeros(self.lats.shape)
        self.Sum_lapse_bias_low = np.zeros(self.lats.shape)
        self.Sum_ctth_bias_temperature_low = np.zeros(self.lats.shape)
        self.Sum_ctth_bias_temperature_low_t11 = np.zeros(self.lats.shape)
        self.Min_lapse_rate = np.zeros(self.lats.shape)
        self.N_new_false_clouds = np.zeros(self.lats.shape)
        self.N_new_detected_clouds = np.zeros(self.lats.shape)
        self.N_false_clouds = np.zeros(self.lats.shape)
        self.N_detected_clouds = np.zeros(self.lats.shape)
        self.N_undetected_clouds = np.zeros(self.lats.shape)
        self.N_detected_clear = np.zeros(self.lats.shape)
        self.N_detected_height_low = np.zeros(self.lats.shape)
        self.Sum_height_bias_type={}
        self.N_detected_height_type={}
        for cc_type in xrange(8):
            self.Sum_height_bias_type[cc_type] = 1.0*np.zeros(self.lats.shape)
            self.N_detected_height_type[cc_type] = 1.0*np.zeros(self.lats.shape)
    def np_float_array(self):
        self.Sum_ctth_bias_low = 1.0*np.array(self.Sum_ctth_bias_low)
        self.Sum_lapse_bias_low = 1.0*np.array(self.Sum_lapse_bias_low)
        self.Sum_ctth_bias_temperature_low = 1.0*np.array(self.Sum_ctth_bias_temperature_low)
        self.Sum_ctth_bias_temperature_low_t11 = 1.0*np.array(self.Sum_ctth_bias_temperature_low_t11)
        self.Min_lapse_rate = 1.0*np.array(self.Min_lapse_rate)
        self.N_detected_clouds = 1.0*np.array(self.N_detected_clouds)
        self.N_undetected_clouds = 1.0*np.array(self.N_undetected_clouds)  
        self.N_false_clouds = 1.0*np.array(self.N_false_clouds)
        self.N_detected_clear = 1.0*np.array(self.N_detected_clear)
        self.N_new_detected_clouds = 1.0*np.array(self.N_new_detected_clouds)
        self.N_new_false_clouds = 1.0*np.array(self.N_new_false_clouds)
        self.N_detected_height_low = 1.0*np.array(self.N_detected_height_low)
    def find_number_of_clouds_clear(self):
        self.np_float_array()
        self.N_clear = self.N_detected_clear+self.N_false_clouds
        self.N_clouds = self.N_detected_clouds+self.N_undetected_clouds 
        self.N = self.N_clear + self.N_clouds
    
    def _remap_a_score_on_an_area(self, plot_area_name='npole', vmin=0.0, vmax=1.0, 
                                  score='Kuipers'):
        from pyresample import image, geometry
        area_def = utils.parse_area_file(
            'reshaped_files_plotting/region_config_test.cfg',  
            plot_area_name)[0]
        data = getattr(self, score)
        data = data.copy()
        data[np.logical_and(np.equal(data.mask,False),data>vmax)]=vmax
        data[np.logical_and(np.equal(data.mask,False),data<vmin)]=vmin #do not wan't low ex hitrates set to nodata!
        #lons = np.ma.masked_array(self.lons, mask=data.mask)
        #lats = np.ma.masked_array(self.lats, mask=data.mask)
        lons = self.lons
        lats = self.lats
        swath_def = geometry.SwathDefinition(lons=lons, lats=lats)
        swath_con = image.ImageContainerNearest(
            data, swath_def, 
            radius_of_influence=self.radius_km*1000*2.5,
            epsilon=1.0)
        area_con = swath_con.resample(area_def)
        result = area_con.image_data
        #pr.plot.show_quicklook(area_def, result,
        #                      vmin=vmin, vmax=vmax, label=score)
        
        pr.plot.save_quicklook(self.PLOT_DIR_SCORE + self.figure_name + 
                               score +'_' + plot_area_name +'.png',
                               area_def, result, 
                               vmin=vmin, vmax=vmax, label=score)

    def _remap_a_score_on_an_robinson_projection(self, vmin=0.0, vmax=1.0, 
                                                 score='Kuipers', screen_out_valid=False):
        import matplotlib.pyplot as plt
        from mpl_toolkits.basemap import Basemap
        from scipy.interpolate import griddata
        lons = self.lons
        lats = self.lats
        plt.close('all')
        ma_data = getattr(self, score)
        the_mask = ma_data.mask
        data=ma_data.data
        #data[np.logical_and(data>vmax,~the_mask)] = vmax
        #data[np.logical_and(data<vmin,~the_mask)] = vmin
        #reshape data a bit
        ind = np.argsort(lats)
        lons = lons[ind]
        lats = lats[ind]
        data = data[ind]
        the_mask = the_mask[ind]
        ind = np.argsort(lons)
        lons = lons[ind]
        lats = lats[ind]
        data =data[ind]
        the_mask = the_mask[ind]
        lons =         lons.reshape(len(data),1)#*3.14/180
        lats =         lats.reshape(len(data),1)#*3.14/180
        data =         data.reshape(len(data),1)
        the_mask =     the_mask.reshape(len(data),1)

        my_proj1 = Basemap(projection='robin',lon_0=0,resolution='c')
        numcols=1000
        numrows=500
        lat_min = -83.0
        lon_min = -179.9
        lat_max = 83.0
        lon_max = 179.9
            
        fig = plt.figure(figsize = (16,9))
        ax = fig.add_subplot(111)
        import copy; 
        my_cmap=copy.copy(matplotlib.cm.coolwarm)
        if score in "Bias" and screen_out_valid:
            #This screens out values between -5 and +5% 
            vmax=25
            vmin=-25            
            my_cmap=copy.copy(matplotlib.cm.get_cmap("coolwarm", lut=100))
            cmap_vals = my_cmap(np.arange(100)) #extractvalues as an array
            cmap_vals[39:61] = [0.9, 0.9, 0.9, 1] #change the first value
            my_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
                "newwarmcool", cmap_vals) 
            print my_cmap
        if score in "RMS" and screen_out_valid:
            # This screens out values beteen 0 and 20%. 41/100=20%
            vmax=50
            vmin=0
            my_cmap=copy.copy(matplotlib.cm.get_cmap("coolwarm", lut=100))
            cmap_vals = my_cmap(np.arange(100)) #extract values as an array
            cmap_vals[0:41] = [0.9, 0.9, 0.9, 1] #change the first value
            my_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
                "newwarmcool", cmap_vals) 
            print my_cmap
        #to mask out where we lack data
        data[np.logical_and(data>vmax,~the_mask)]=vmax
        data[np.logical_and(data<vmin,~the_mask)]=vmin
        data[the_mask]=2*vmax #give no data value that will be masked white
        xi = np.linspace(lon_min, lon_max, numcols)
        yi = np.linspace(lat_min, lat_max, numrows)
        xi, yi = np.meshgrid(xi, yi)
        # interpolate
        x, y, z = (np.array(lons.ravel()), 
                   np.array(lats.ravel()), 
                   np.array(data.ravel()))
        my_cmap.set_over('w',alpha=1)
        zi = griddata((x, y), z, (xi, yi), method='nearest')
        im1 = my_proj1.pcolormesh(xi, yi, zi, cmap=my_cmap,
                           vmin=vmin, vmax=vmax, latlon=True)
        #draw som lon/lat lines
        my_proj1.drawparallels(np.arange(-90.,90.,30.))
        my_proj1.drawmeridians(np.arange(-180.,180.,60.))
        my_proj1.drawcoastlines()
        my_proj1.drawmapboundary(fill_color='0.9')
        cb = my_proj1.colorbar(im1,"right", size="5%", pad="2%")
        ax.set_title(score)
        plt.savefig(self.PLOT_DIR_SCORE + self.figure_name + 
                    'basemap_' + 
                    score +'_robinson_' +'.png')
        plt.close('all')

    def remap_and_plot_score_on_several_areas(self, vmin=0.0, vmax=1.0, 
                                              score='Kuipers', screen_out_valid=False):
        print score
        self.PLOT_DIR_SCORE = self.PLOT_DIR + "/%s/Radius_%d_km/"%(score, self.radius_km)
        if not os.path.exists(self.PLOT_DIR_SCORE):
            os.makedirs(self.PLOT_DIR_SCORE)
        for plot_area_name in [
                #'cea5km_test'
                #'euro_arctic',
                #'ease_world_test'
                'euro_arctic',
                'antarctica',
                'npole',
                'ease_nh_test',
                'ease_sh_test' ]:
            self._remap_a_score_on_an_area(plot_area_name=plot_area_name, 
                                           vmin=vmin, vmax=vmax, score=score)
        #the real robinson projection
        if "morning" not in self.figure_name:
            self._remap_a_score_on_an_robinson_projection(vmin=vmin, vmax=vmax, 
                                                          score=score, screen_out_valid=False)
    def calculate_kuipers(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        N_clear = self.N_clear
        N_clouds = self.N_clouds
        N_detected_clouds = self.N_detected_clouds
        N_detected_clear = self.N_detected_clear
        #Typically we have N_clear/N_clouds = 30/70 
        #In areas with only clouds or only clears the Kuipers will be ==0
        #Even if all clouds/clears are classified correctly!
        #Do something for these set to none or update   
        Kuipers_devider = (N_clouds)*(N_clear)
        Kuipers_devider[Kuipers_devider==0] = 1.0
        Kuipers = (N_detected_clouds*N_detected_clear - 
                   self.N_false_clouds*self.N_undetected_clouds)/Kuipers_devider
        the_mask = np.logical_or(self.N_clear<20, self.N_clouds<20)
        the_mask = np.logical_or(the_mask, self.N_clouds < 0.01*self.N_clear)
        the_mask = np.logical_or(the_mask, self.N_clear < 0.01*self.N_clouds)        
        Kuipers = np.ma.masked_array(Kuipers, mask=the_mask)
        self.Kuipers = Kuipers

    def calculate_lapse_rate(self):
        self.np_float_array()
        the_mask = self.Min_lapse_rate>-0.001
        lapse_rate = np.ma.masked_array(self.Min_lapse_rate, mask=the_mask)
        self.lapse_rate = lapse_rate
    def calculate_temperature_bias(self):
        self.np_float_array()
        the_mask = self.N_detected_height_low<1
        ctth_bias_temperature_low = self.Sum_ctth_bias_temperature_low*1.0/self.N_detected_height_low
        ctth_bias_temperature_low = np.ma.masked_array(ctth_bias_temperature_low, mask=the_mask)
        self.ctth_bias_temperature_low = ctth_bias_temperature_low
    def calculate_temperature_bias_t11(self):
        self.np_float_array()
        the_mask = self.N_detected_height_low<1
        ctth_bias_temperature_low_t11 = self.Sum_ctth_bias_temperature_low_t11*1.0/self.N_detected_height_low
        ctth_bias_temperature_low_t11 = np.ma.masked_array(ctth_bias_temperature_low_t11, mask=the_mask)
        self.ctth_bias_temperature_low_t11 = ctth_bias_temperature_low_t11
    def calculate_height_bias(self):
        self.np_float_array()
        the_mask = self.N_detected_height_low<1
        ctth_bias_low = self.Sum_ctth_bias_low*1.0/self.N_detected_height_low
        ctth_bias_low = np.ma.masked_array(ctth_bias_low, mask=the_mask)
        self.ctth_bias_low = ctth_bias_low
    def calculate_height_bias_lapse(self):
        self.np_float_array()
        the_mask = self.N_detected_height_low<1
        lapse_bias_low = self.Sum_lapse_bias_low*1.0/self.N_detected_height_low
        lapse_bias_low = np.ma.masked_array(lapse_bias_low, mask=the_mask)
        self.lapse_bias_low = lapse_bias_low
    def calculate_height_bias_type(self):
        self.np_float_array()
        for cc_type in xrange(8):
            the_mask = self.N_detected_height_type[cc_type]<1
            ctth_bias_type_i = self.Sum_height_bias_type[cc_type]*1.0/self.N_detected_height_type[cc_type]
            ctth_bias_type_i = np.ma.masked_array(ctth_bias_type_i, mask=the_mask)
            setattr(self, "ctth_bias_type_%d"%(cc_type), ctth_bias_type_i)   

    def calculate_hitrate(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        Hitrate = (self.N_detected_clouds + self.N_detected_clear)*1.0/(
            self.N_clear + self.N_clouds)
        the_mask = self.N<20
        Hitrate = np.ma.masked_array(Hitrate, mask=the_mask)
        self.Hitrate = Hitrate

    def calculate_increased_hitrate(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        Hitrate = (
            self.N_detected_clouds + self.N_detected_clear)*1.0/(
                self.N_clear + self.N_clouds)
        new_Hitrate = (
            self.N_detected_clouds + self.N_new_detected_clouds - 
            self.N_new_false_clouds+ self.N_detected_clear)*1.0/(
                self.N_clear + self.N_clouds)
        the_mask = self.N<20
        increased_Hitrate = np.ma.masked_array(new_Hitrate-Hitrate, mask=the_mask)
        self.increased_Hitrate = increased_Hitrate

    def calculate_threat_score(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        ThreatScore = (
            self.N_detected_clouds)*1.0/( self.N_clouds + self.N_false_clouds)
        the_mask = self.N_clouds<20
        ThreatScore = np.ma.masked_array(ThreatScore, mask=the_mask)
        self.Threat_Score = ThreatScore
    def calculate_threat_score_clear(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        ThreatScoreClear = (
            self.N_detected_clear)*1.0/( self.N_clear + 
                                         self.N_undetected_clouds)
        the_mask = self.N_clear<20
        ThreatScoreClear = np.ma.masked_array(ThreatScoreClear, 
                                              mask=the_mask)
        self.Threat_Score_Clear = ThreatScoreClear
    def calculate_pod_clear(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        PODclear = (
            self.N_detected_clear)*1.0/(self.N_clear)
        the_mask = self.N_clear<20
        PODclear = np.ma.masked_array(PODclear, mask=the_mask)
        self.PODclear = PODclear 
    def calculate_pod_cloudy(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        PODcloudy = (
            self.N_detected_clouds)*1.0/(self.N_clouds)
        the_mask = self.N_clouds<20
        PODcloudy = np.ma.masked_array(PODcloudy, mask=the_mask)
        self.PODcloudy = PODcloudy
    def calculate_far_clear(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        FARclear = (
            self.N_undetected_clouds)*1.0/(self.N_detected_clear +
                                           self.N_undetected_clouds)
        the_mask = self.N_clear<20
        FARclear = np.ma.masked_array(FARclear, mask=the_mask)
        self.FARclear = FARclear 
    def calculate_far_cloudy(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        FARcloudy = (
            self.N_false_clouds)*1.0/(self.N_detected_clouds+
                                      self.N_false_clouds)     
        the_mask = self.N_clouds<20
        FARcloudy = np.ma.masked_array(FARcloudy, mask=the_mask)
        self.FARcloudy = FARcloudy
    def calculate_calipso_cfc(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        calipso_cfc = 100*(
            self.N_detected_clouds + self.N_undetected_clouds)*1.0/(self.N)
        the_mask = self.N<20
        calipso_cfc = np.ma.masked_array(calipso_cfc, mask=the_mask)
        self.calipso_cfc = calipso_cfc
    def calculate_pps_cfc(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        pps_cfc = 100*(
            self.N_detected_clouds + self.N_false_clouds)*1.0/(self.N)
        the_mask = self.N<20
        pps_cfc = np.ma.masked_array(pps_cfc, mask=the_mask)
        self.pps_cfc = pps_cfc
    def calculate_bias(self):
        self.np_float_array()
        self.find_number_of_clouds_clear()
        self.calculate_calipso_cfc()
        self.calculate_pps_cfc()
        Bias = self.pps_cfc - self.calipso_cfc
        the_mask = self.N<20 
        Bias = np.ma.masked_array(Bias, mask=the_mask)
        self.Bias = Bias
    def calculate_RMS(self):
        self.np_float_array()
        self.calculate_calipso_cfc()
        self.find_number_of_clouds_clear()
        self.calculate_bias()
        RMS = np.sqrt((self.N_false_clouds*(100.0 - 0.0 - self.Bias)**2 + 
                       self.N_undetected_clouds*(0.0 - 100.0 -self.Bias)**2 + 
                       self.N_detected_clear*self.Bias**2 + 
                       self.N_detected_clouds*self.Bias**2)/(
                   self.N))
        the_mask = self.N<20 
        RMS = np.ma.masked_array(RMS, mask=the_mask)
        self.RMS = RMS


class PerformancePlottingObject:
    def __init__(self):
        self.flattice = ppsStatsOnFibLatticeObject()
    def add_detection_stats_on_fib_lattice(self, my_obj):
        #Start with the area and get lat and lon to calculate the stats:
        lats = self.flattice.lats[:]
        max_distance=self.flattice.radius_km*1000*2.5
        area_def = SwathDefinition(*(self.flattice.lons,
                                     self.flattice.lats))
        target_def = SwathDefinition(*(my_obj.longitude, 
                                       my_obj.latitude)) 
        valid_in, valid_out, indices, distances = get_neighbour_info(
            area_def, target_def, radius_of_influence=max_distance, 
            epsilon=100, neighbours=1)
        cols = get_sample_from_neighbour_info('nn', target_def.shape,
                                              np.array(xrange(0,len(lats))),
                                              valid_in, valid_out,
                                              indices)
        cols = cols[valid_out]
        detected_clouds = my_obj.detected_clouds[valid_out]
        detected_clear = my_obj.detected_clear[valid_out]
        detected_height_low = my_obj.detected_height_low[valid_out]
        false_clouds = my_obj.false_clouds[valid_out]
        undetected_clouds = my_obj.undetected_clouds[valid_out]
        new_detected_clouds = my_obj.new_detected_clouds[valid_out]
        new_false_clouds = my_obj.new_false_clouds[valid_out]
        lapse_rate = my_obj.lapse_rate[valid_out]  
        height_bias_low = my_obj.height_bias_low[valid_out] 
        temperature_bias_low = my_obj.temperature_bias_low[valid_out]
        temperature_bias_low_t11 = my_obj.temperature_bias_low_t11[valid_out]
        lapse_bias_low = my_obj.lapse_bias_low[valid_out]
        #lets make things faster, I'm tired of waiting!
        cols[distances>max_distance]=-9 #don't use pixles matched too far away!
        import time        
        tic = time.time()      
        arr, counts = np.unique(cols, return_index=False, return_counts=True)        
        for d in arr[arr>0]:
            use = cols==d
            ind = np.where(use)[0]
            #if ind.any():
            self.flattice.N_false_clouds[d] += np.sum(false_clouds[ind])
            self.flattice.N_detected_clouds[d] += np.sum(detected_clouds[ind])
            self.flattice.N_detected_clear[d] += np.sum(detected_clear[ind])
            self.flattice.N_undetected_clouds[d] += np.sum(undetected_clouds[ind])
            self.flattice.N_new_false_clouds[d] += np.sum(new_false_clouds[ind])
            self.flattice.N_new_detected_clouds[d] += np.sum(new_detected_clouds[ind])
            self.flattice.N_detected_height_low[d] += np.sum(detected_height_low[ind])
            self.flattice.Sum_ctth_bias_low[d] += np.sum(height_bias_low[ind])
            self.flattice.Sum_lapse_bias_low[d] += np.sum(lapse_bias_low[ind])
            self.flattice.Sum_ctth_bias_temperature_low[d] += np.sum(temperature_bias_low[ind])
            self.flattice.Sum_ctth_bias_temperature_low_t11[d] += np.sum(temperature_bias_low_t11[ind])
            self.flattice.Min_lapse_rate[d] = np.min([self.flattice.Min_lapse_rate[d],
                                                      np.min(lapse_rate[ind])])  
            cc_type = 0
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 1
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 2
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 3
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 4
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 5
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 6
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])
            cc_type = 7
            self.flattice.Sum_height_bias_type[cc_type][d] += np.sum(my_obj.height_bias_type[cc_type][ind])
            self.flattice.N_detected_height_type[cc_type][d] += np.sum(my_obj.detected_height_type[cc_type][ind])

        print "mapping took %1.4f seconds"%(time.time()-tic)   


def get_fibonacci_spread_points_on_earth(radius_km):
    #Earth area = 510072000km2
    #4000 point with radius~200km
    #1000 point with radium~100km
    #25000 radius 80km
    #64000 radius 5km
    EARTH_AREA = 510072000
    POINT_AREA = radius_km * radius_km * 3.14
    n = int(EARTH_AREA /POINT_AREA)
    #http://arxiv.org/pdf/0912.4540.pdf
    #Alvaro Gonzalez: Measurement of areas on sphere usig Fibonacci and latitude-longitude grid.
    #import math
    lin_space = np.array(xrange(-n/2,n/2))
    pi = 3.14
    theta = (1+np.sqrt(5))*0.5
    longitude = (lin_space % theta)*360/theta
    temp = (2.0 * lin_space) / (n)
    temp[temp>1.0]=0.999
    temp[temp<-1.0]=-0.999
    latitude = np.arcsin(temp)*180/pi
    longitude[longitude>180] = longitude[longitude>180] -360
    longitude[longitude<-180] = longitude[longitude<-180] +360
    #latitude[latitude>90]=180 - latitude[latitude>90]
    #latitude[latitude<-90]=-180 -latitude[latitude<-90]
    longitude =longitude[latitude<90]
    latitude =latitude[latitude<90]
    longitude =longitude[latitude>-90]
    latitude =latitude[latitude>-90]

    if np.isnan(np.max(latitude)):
        raise ValueError
    return longitude, latitude


    





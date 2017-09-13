# Program cloudsat_calipso_avhrr_prepare.py
# python cloudsat_calipso_avhrr_prepare.py 
import numpy as np
from config import OPTICAL_DETECTION_LIMIT, OPTICAL_LIMIT_CLOUD_TOP, NODATA

def CalipsoCloudOpticalDepth_new(calipso, min_optical_depth, use_old_method=False,
                                 limit_ctop=OPTICAL_LIMIT_CLOUD_TOP):
    new_cloud_top = np.ones(calipso.layer_top_altitude.shape)*NODATA*1.0
    new_cloud_base = np.ones(calipso.layer_base_altitude.shape)*NODATA*1.0
    distance_down_in_cloud_we_see = np.ones(calipso.layer_base_altitude.shape)*NODATA*1.0
    new_cloud_fraction = np.zeros(calipso.cloud_fraction.shape)
    new_fcf = np.ones(calipso.feature_classification_flags.shape).astype(calipso.feature_classification_flags.dtype)
    depthsum = 0.0*new_cloud_fraction.copy()
    already_detected = depthsum > 99999 #None from the start! All False
    already_detected[calipso.layer_top_altitude[:,0]<0] = True # don't bother with clear pixels
    #to_thin_to_see_at_all = calipso.total_optical_depth_5km < min_optical_depth
    N10 = new_cloud_top.shape[1]
    for layer_j in xrange(N10):
        #Filter OPTICAL_LIMIT_CLOUD_TOP down in EACH layer
        #Notice even if top of layer i is always above layer i-1,
        #it is NOT the case that base of layer i is always above layer i-1!
        # We could have the situation:
        # layer 0 base at 2km top at 0km optical thickness 0.1
        # layer 1 base at 8km top at 9km optical thickness 10
        # Or the situation:
        # layer 0 base at 2km top at 0km optical thickness 0.5
        # layer 1 base at 8km top at 9km optical thickness 0.5
        this_layer_optical_depth = calipso.feature_optical_depth_532[:, layer_j].ravel()
        cloud_base = calipso.layer_base_altitude[:,layer_j]
        cloud_top = calipso.layer_top_altitude[:,layer_j]
        geometrical_distance_cloud = cloud_top-cloud_base
        geometrical_distance_cloud[cloud_base<0] = 0
        geometrical_distance_cloud[cloud_top<0] = 0                                         
        fraction_into_cloud = (limit_ctop*1.0)/this_layer_optical_depth
        fraction_into_cloud[fraction_into_cloud<0] = 0
        fraction_into_cloud[fraction_into_cloud>1.0] = 1.0
        if use_old_method:
            fraction_into_cloud = 0.5
        #For KGs method set fraction_into_cloud = 0.5 always
        distance_down_in_cloud_we_see[:,layer_j] = geometrical_distance_cloud*fraction_into_cloud 

    for layer_j in xrange(N10):
        total_optical_depth_layers_above = depthsum.copy()
        this_layer_optical_depth = calipso.feature_optical_depth_532[:, layer_j].ravel()
        depthsum += this_layer_optical_depth 
        #this_is_the_top_most_layer_we_detect
        update = np.logical_and(
            depthsum >= min_optical_depth,
            np.equal(already_detected,False))
        new_cloud_top[update, 0:(N10-layer_j)] = (calipso.layer_top_altitude[update, layer_j:] -
                                                  distance_down_in_cloud_we_see[update, layer_j:])
        new_cloud_base[update, 0:(N10-layer_j)] = calipso.layer_base_altitude[update, layer_j:]
        new_fcf[update, 0:(N10-layer_j)] = calipso.feature_classification_flags[update, layer_j:]
        new_cloud_fraction[update] = calipso.cloud_fraction[update]
        already_detected[update] = True
    if use_old_method:
        pass
    else:    
        for layer_j in xrange(N10):
            filtered_to_low = new_cloud_top[:,0]< new_cloud_top[:,layer_j]
            new_cloud_top[filtered_to_low,0] = new_cloud_top[filtered_to_low,layer_j]
        
    new_validation_height = new_cloud_top[:,0].copy()
    new_validation_height[new_validation_height>=0] = new_validation_height[new_validation_height>=0]*1000
    new_validation_height[new_validation_height<0] = -9
    return new_cloud_top, new_cloud_base, new_cloud_fraction, new_fcf, new_validation_height


def CalipsoCloudOpticalDepth(cloud_top, cloud_base, optical_depth, cloud_fraction, fcf, min_optical_depth):
    # DEPRICATED! #20170913
    # Use CalipsoCloudOpticalDepth_new(calipso, min_optical_depth, use_old_method=True,
    #                             limit_ctop=OPTICAL_LIMIT_CLOUD_TOP)
    # ... if the old method is wanted!
    # I will keep the code for a while to be able to compare with unit test that it does the same thing

    from config import MIN_OPTICAL_DEPTH

    new_cloud_top = np.ones(cloud_top.shape,'d')*np.min(cloud_top)
    new_cloud_base = np.ones(cloud_base.shape,'d')*np.min(cloud_base)
    new_cloud_fraction = np.zeros(cloud_fraction.shape,'d')
    new_fcf = np.ones(fcf.shape).astype(fcf.dtype)
    
    for pixel_i in range(optical_depth.shape[0]):

        depthsum = 0 #Used to sum the optical_depth
        for layer_j in range(optical_depth.shape[1]):
            # Just stops the for loop when there are no more valid value 
            if optical_depth[pixel_i, layer_j] < 0:
                break
            else:
                depthsum = depthsum + optical_depth[pixel_i, layer_j]
            
                # Removes the cloud values for all pixels that have a optical depth (integrated from the top) below MIN_OPTICAL_DEPTH and moves the first valid value to the first column and so on.
                #if depthsum >= MIN_OPTICAL_DEPTh:
                if depthsum >= min_optical_depth:
                    new_cloud_top[pixel_i, 0:(optical_depth.shape[1]-layer_j)] = cloud_top[pixel_i, layer_j:]
                    new_cloud_base[pixel_i, 0:(optical_depth.shape[1]-layer_j)] = cloud_base[pixel_i, layer_j:]
                    # new_cloud_fraction[pixel_i] = 1
                    new_cloud_fraction[pixel_i] = cloud_fraction[pixel_i] # Let's still trust in what is seen in 1 km data/KG
                    new_fcf[pixel_i, 0:(fcf.shape[1]-layer_j)] = fcf[pixel_i, layer_j:]
                    #extrra to get a cloud top that corresponds better to avhrr
                    for k in range(new_cloud_top.shape[1]):
                        if new_cloud_top[pixel_i, k] < 0:
                            break
                        else:
                            new_cloud_top[pixel_i, k] = new_cloud_base[pixel_i, k] + \
                            ((new_cloud_top[pixel_i, k] - new_cloud_base[pixel_i, k]) * 1/2.)
                    break
    new_validation_height = new_cloud_top[:,0].copy()
    new_validation_height[new_validation_height>=0] *= 1000
    new_validation_height[new_validation_height<0] = -9
    return new_cloud_top, new_cloud_base, new_cloud_fraction, new_fcf, new_validation_height

def check_total_optical_depth_and_warn(caObj):
    obj = caObj.calipso
    if  (obj.total_optical_depth_5km is not None and 
         (obj.total_optical_depth_5km < obj.feature_optical_depth_532_top_layer_5km).any()):
        badPix=np.less(obj.total_optical_depth_5km+0.001, 
                       obj.feature_optical_depth_532_top_layer_5km)
        diff=obj.total_optical_depth_5km- obj.feature_optical_depth_532_top_layer_5km
        print "warning", len(obj.total_optical_depth_5km)  
        print len(obj.total_optical_depth_5km[badPix])
        print obj.total_optical_depth_5km[badPix]
        print obj.feature_optical_depth_532_top_layer_5km[badPix] 
        print diff[badPix]
        print obj.number_layers_found[badPix]
        if obj.detection_height_5km is not None:
            print obj.detection_height_5km[badPix] 
        print np.where(badPix)
        print obj.layer_top_altitude[0,badPix]
        print obj.layer_base_altitude[0,badPix]

def CalipsoOpticalDepthHeightFiltering1km(CaObj):
    #Should all layers be updated???
    new_cloud_tops = np.where(
        CaObj.calipso.layer_top_altitude[:,0]*1000 > CaObj.calipso.detection_height_5km,
        CaObj.calipso.detection_height_5km,
        CaObj.calipso.layer_top_altitude[:,0]*1000)
    new_cloud_tops = np.where(
        CaObj.calipso.layer_base_altitude[:,0]*1000 > CaObj.calipso.detection_height_5km,
        CaObj.calipso.layer_base_altitude[:,0]*1000,
        new_cloud_tops)
    clouds_to_update = np.logical_and(
        CaObj.calipso.layer_top_altitude[:,0]*1000>CaObj.calipso.detection_height_5km,
        np.not_equal(CaObj.calipso.detection_height_5km, -9))
    CaObj.calipso.validation_height = np.where(
        clouds_to_update,
        new_cloud_tops,
        CaObj.calipso.validation_height)
    return CaObj


def detection_height_from_5km_data(Obj1, Obj5, limit_ctop=OPTICAL_LIMIT_CLOUD_TOP):
    if (Obj5.profile_utc_time[:,1] == Obj1.profile_utc_time[2::5]).sum() != Obj5.profile_utc_time.shape[0]:
        logger.warning("length mismatch")
    cloud_top5km, dummy, dummy, dummy, detection_height = CalipsoCloudOpticalDepth_new(Obj5, 0.0, 
                                                                                       limit_ctop=limit_ctop)
    #cloud_base1km = Obj1.layer_base_altitude[:,0]
    #cloud_top5km = np.repeat(cloud_top5km[:,0], 5, axis=0) 
    detection_height1km = np.repeat(detection_height, 5, axis=0) 
    #detection_height1km[cloud_top5km<cloud_base1km] = -9
    Obj1.detection_height_5km = detection_height1km
    return Obj1    

def CalipsoOpticalDepthSetThinToClearFiltering1km(CaObj):
    isThin_clouds = np.logical_and(CaObj.calipso.total_optical_depth_5km < OPTICAL_DETECTION_LIMIT,
                                   np.not_equal(CaObj.calipso.total_optical_depth_5km,-9))
    #>0.0 important. Some clouds are missing in 5km data set but present in 1km data set!
    set_to_clear = np.logical_and(
        CaObj.calipso.number_layers_found>0,
        isThin_clouds)
    CaObj.calipso.cloud_fraction[set_to_clear] = 0.00001
    CaObj.calipso.validation_height[set_to_clear] = -9
    return CaObj
 























































# -*- coding: utf-8 -*-
"""
Title: Prominence Calculator

Purpose: Calculate Prominence of local Maxima in Raster Data

By: Ryan McKeon - Dartmouth College, Geography Department, ryan.e.mckeon@dartmouth.edu

Date: January 12, 2017

Description:
    
This script calcuates the prominence of local maxima within a gridded dataset.
To conceptualize what is going on, it is easiest to think of topography and 
topographic maps. Picture a ridge with several summits along it and a volcano
standing isolated above land surface it is built apon.  The volcano stands 
"prominently" above the surrounding area, whereas, the summits along the ridge
may be high in elevation, but are not particularly distinct from one another.  
The volcano peak (defined as a point) would sit alone within many contour lines 
(here defined as polygons) descending from the summit, thus resulting in a 
high prominence.  By contrast, the summits along the ridge (also defined as 
points) will only have one or two contour polygons to themselves before 
multiple peaks are contained within a single contour polygon, meaning the
peaks have low prominence. 

Inputs/Outputs:
    


Known Issues and Limitaitons:    
Current known issue: Duplicate peaks are removed based solely on elevation.
Thus only one of two or more peaks with same elevation will be used in this 
calculation. 

This could probably be solved by finding the duplicates and then dropping all 
but one that are contained in the nearest polygon. (i.e. the containing polygon
with the smallest area.) 


"""


import geopandas as gpd
import pandas as pd
import numpy as np

# load data

print('')
print('Loading data...  may be slow for large files')

peaks = gpd.read_file('pop_peaks_no_zeros.shp')
contours = gpd.read_file('population_density_contours.shp')

print('')
print('Data Loaded Successfully')
print('')

#-------------------------------------------
# Section 1: Prepare Input Data for Analysis
# 
# The goal here is identify and remove duplicate peaks based on elevation and 
# proximity (not currently implemented), where multiple peaks of the same 
# elevation are removed if they fall within a proximity threshold.  Next, the 
# contours are searched to identify how many peaks fall within them, then 
# contours containing no peaks are removed to speed up the analysis as these 
# contours will not impact the prominence calculation.

# Find and remove duplicate peaks
peaks = peaks.drop_duplicates(['GRID_CODE'], keep = 'first')  # use elevation to find duplicates and keep the first value of a specific elevation
peaks.index = range(0, len(peaks))  # reset the index of peaks

# Find and remove duplicate contour polygons
contours = contours.drop_duplicates(['Shape_leng'], keep = 'last') # search for duplicates using Shape length, keep the last value for the lower elevation contour
contours.index = range(0, len(contours))  # reset the index

# make a working copy of input data
pts = peaks.copy()
polys = contours.copy()

# create new columns to catch in or out info
peaks['prom'] = pd.Series(0, index=peaks.index)  # create the new column
peaks['contain'] = pd.Series(False, index=peaks.index)  # create the new column
peaks['dup_peak'] = pd.Series(False, index=peaks.index)
peaks['containing_contour_ORIG_FID'] = pd.Series(0, index=peaks.index)
#peaks['j_val'] = pd.Series(0, index=peaks.index)
polys['contain'] = pd.Series(False, index=polys.index) 

print('Now checking the number of points in each contour polygon...')
print('This can be a slow process.') 
print('')

polys.contain = polys.intersects(peaks.unary_union)  # for each polygon, ask if contains any peaks
polys = polys[polys.contain != False]  # remove the contour polygons that DO NOT contain any peaks


print('Removing contour polygons that contain no peaks.')
print('')

# now sort the remaining polygons by contour elevation from high to low and save a shapefile       
polys = polys.sort_values(by=('CONTOUR'),ascending=False)  # sort the dataframe
polys.index = range(1, len(polys) + 1)  # asign a new index based on the resort
contours_out = polys.drop(polys.columns[[8]], axis=1)  # remove the 'contain' column so the SHAPEFILE CAN BE OUTPUT!!
contours_out.to_file('contours_for_calc_OUT.shp')  # save a shapefile of the contours used to calculate prominence.

print('')
print('Now starting the big loop.')
print('Calculating Prominence one peak at a time.')
print('')

#----------------
#Section 2 -- The business of calculating Prominence 
 
#Select a single peak at a time, find the polygons that contain that peak, 
#then loop through each of the containing polygons to see if there is a 
# higher peak within it.  Repeat for all peaks.


# Loop through each peak

for i in range(0,len(peaks.index+1)):
    
    current_peak = peaks[i:i+1]  # make a new dataframe of just 1 peak
    current_ELEV = current_peak.loc[i,'GRID_CODE']  # store the elevation of that peak
    polys['contain']= polys.intersects(current_peak.unary_union) # find the polygons contain the current peak
    polys_containing = polys[polys.contain != False]  #keep only those polygons that contain the peak
    polys_containing = polys_containing.reset_index(drop=True)  # reset the index after dropping rows
    
    # Loop through polys to find peaks and compare elevation with current_ELEV
    higher_peak_found = False
    test_ELEV = 0
    j = 0
    while higher_peak_found == False:
        
        # trap out the possibility that no polygons contain a peak point
        if len(polys_containing) == 0:
            # do nothing, fill prominence with dummy value of -99
            higher_peak_found = True 
            peaks.set_value(i,'prom', -99)
        
        # trap out the possibility that no peak is higher than the current peak in this set of contour polygons
        elif j == len(polys_containing):
            current_poly = polys_containing[j-1:j]  # make a new dataframe with only one poly
            contour_elev = current_poly.loc[j-1,'CONTOUR']  # get the contour elevation
            contour_ID = current_poly.loc[j-1,'ORIG_FID']  # get the contour ORIG ID
            higher_peak_found = True
            prominence = current_ELEV - contour_elev
            peaks.set_value(i,'prom', prominence)
            peaks.set_value(i,'containing_contour_ORIG_FID', contour_ID)
            #peaks.set_value(i,'j_val', j)
        else:
            current_poly = polys_containing[j:j+1]  # make a new dataframe with only one poly
            contour_elev = current_poly.loc[j,'CONTOUR']  # get the contour elevation
            peaks['contain']= peaks.intersects(current_poly.unary_union)  # find peaks contained within the currnet polygon
            peaks_contained = peaks[peaks.contain != False]  # keep only the peaks contained in the current polygon
            max_peak = peaks_contained.loc[peaks_contained['GRID_CODE'].idxmax()]  # find the highest peak of all the peaks contained in the polygon
            test_ELEV = max_peak.GRID_CODE  # store the elevation in test_ELEV
            if test_ELEV > current_ELEV:  # JUST REMOVED >=
                contour_ID = current_poly.loc[j,'ORIG_FID']  # get the contour ORIG ID
                higher_peak_found = True
                prominence = current_ELEV - contour_elev
                peaks.set_value(i,'prom', prominence)
                peaks.set_value(i,'containing_contour_ORIG_FID', contour_ID)
                #peaks.set_value(i,'j_val', j)
            else:
                higher_peak_found = False
            peaks.loc[peaks['contain'], 'contain'] = False  # reset peaks['contain'] to False
            
        j = j+1  # iterate the loop counter
            
            

    polys.loc[polys['contain'], 'contain'] = False  # reset polys['contain'] to False      
    
    # print updates on progress to console
    if i%100 == 0:
        print(str(i)+' Peaks Analyzed')
    elif i%10 == 0:
        print(i)
        
#------------------------------------------------------
# Section 3:  Prepare Output

# remove peaks not contained in a polygon
peaks = peaks[peaks.prom != -99]  # remove peaks with a prominence of -99 --> i.e. the peak is not contained in a polygon

# Remove Boolean fields from peaks geodataframe and convert prominence to basic "int" data type
peaks_out = peaks.drop(peaks.columns[[4,5]], axis=1)  # remove the 'contain' and 'dup_peak' columns so the SHAPEFILE CAN BE OUTPUT!!
peaks_out['prom'] = peaks_out[['prom']].astype(int) # convert 'prom' from numpy int64 to int       

# save new peaks shapefile with prominence data
peaks_out.to_file('peaks_with_prominence.shp')

# let the user know the program finished successfully
max_prom = max(peaks.prom)
median_prom = np.median(peaks.prom)

print('')
print('SUCCESS!!')
print('')
print('The maximum prominence is '+str(max_prom)) #+', and the median is '+str(median_prom)'.')






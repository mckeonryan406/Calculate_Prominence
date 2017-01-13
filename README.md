# Calculate Prominence

##Purpose:  
These codes calculate the prominence of "peaks" in raster data sets.

##Description:
Prominence is a measure of how a peak in a continuous data set measures up to others surrounding it.
The concept is most easily thought of in the context of a topographic map, where peaks are points
and they are contained within polygons of contour lines representing equal elevation.  Prominence 
measures how far a peak stands above a contour line that it shares with a peak of greater height.
Thus the most prominent peak within an area of interest will always be the tallest, but the next
most prominent peak may not necessarily be the second highest peak because it has to do with 
isolation and elevation.

##Codes:
This calculation is currently two step process where the user has a input raster file and 
uses an ArcGIS geoprocessing model to generate two shapefiles, one containing defined peaks 
and the other containing contour polygons.  These are then fed into a python script that
uses the geopandas library to clean the input data and calculate the prominence of peaks.

Scripts here fit into basic categories:
	- "L0" scripts, to help you check your raw InSAR data downloaded from Sentinel covers the right timeframe and spatial location.
	- "Visualize XXX" scripts, which plot basic InSAR data. These scripts also provide a blueprint for case-specific maps you may want to create. (Those case-specific scripts should go in the relevant case study folder)
	- General utility scripts, eg "downsacle_DEM.sh".
	- postprocessing.py, a python script which contains all you ever need for manipulating data. This covers all steps after making unwrapped interferograms on drummer. 
	- "python_subroutines" contains Python scripts which may bring together several of the functions in postprocessing.py, or which are too specific to need their own function/class in postprocessing.py.
	- "InSAR_postSBAS.py" is a big script containing codes/functions for manipulating processed InSAR time series, which can be imported from large .csv files and manipulated to eg. extract data from a specific point/polygon, average data, compare with GPS, and other tasks.

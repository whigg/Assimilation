# utility modules
import glob
import os
import sys
import re
import requests
import numpy as np
import pandas as pd
from itertools import compress

def file_meta(fname):
    """
    Derive metadata from filename
    Input:
        fname: ATL06 file name
    Output:
        rgt
        ftime: format (yyyy-mm-dd)
        cycle
    """
    file_re=re.compile('ATL06_(?P<date>\d+)_(?P<rgt>\d\d\d\d)(?P<cycle>\d\d)(?P<region>\d\d)_(?P<release>\d\d\d)_(?P<version>\d\d).h5')
    temp=file_re.search(fname)
    rgt = temp['rgt'].strip("0")
    cycle = temp['cycle'].strip("0")
    f_date = temp['date']
    ftime = f_date[:4] + '-' + f_date[4:6] + '-' + f_date[6:8]
    
    return rgt, ftime, cycle

def OA_request (base_url,Date,bbox,trackId,beamlist,cycle,product = 'atl06'):
    """
    Request data from OpenAltimetry based on API
    Inputs:
        base_url: 'https://openaltimetry.org/data/api/icesat2/level3a'
        Date: acquisition date of ICESat-2 product
        bbox: bounding box [minx,miny,maxx,maxy]
        trackId: RGT number
        beamlist: list of beam number
        cycle: cycle number
        product: ICESat-2 product
    Output:
        track_df: dataframe for all beams of one RGT
    """
    points = [] # store all beam data for one RGT
    
    # iterate all six beams 
    for beam in beamlist:
        # Generate API
        payload =  {'product':product,
                    'startDate': Date,
                    'minx':str(bbox[0]),
                    'miny':str(bbox[1]),
                    'maxx':str(bbox[2]),
                    'maxy':str(bbox[3]),
                    'trackId': trackId,
                    'beamName': beam,
                    'outputFormat':'json'}
        
        # request OpenAltimetry
        r = requests.get(base_url, params=payload)
        
        # get elevation data
        elevation_data = r.json()
        
        # length of file list
        file_len = len(elevation_data['data'])
        
        # file index satifies aqusition time from data file
        idx = [elevation_data['data'][i]['date'] == Date for i in np.arange(file_len)]
        
        # get data we need
        beam_data = list(compress(elevation_data['data'], idx)) 
        
        if not beam_data:
            continue
        
        # elevation array
        beam_elev = beam_data[0]['beams'][0]['lat_lon_elev']

        if not beam_elev: # check if no data 
            continue # continue to next beam  

        for p in beam_elev:
            points.append({
                'lat': p[0],
                'lon': p[1],
                'h': p[2],
                'beam': beam,
                'cycle': cycle,
                'time' : Date}
            )
    
    track_df = pd.DataFrame.from_dict(points)
    
    return track_df
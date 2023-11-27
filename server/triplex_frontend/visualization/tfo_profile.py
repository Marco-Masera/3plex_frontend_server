#!/bin/env python
#import pandas as pd
#import numpy as np
#from scipy.sparse import dok_matrix
from collections import defaultdict
import msgpack
import sys
import os 
from datetime import datetime
import numpy as np


# stdin has 3 columns:
#
#  1       TFO_start
#  2       TFO_end
#  3       Stability
#
# without header
#
# assume data sorted on desending Stability
#
# output is a dictionary, keys are stability levels, values are the profiles of tfo counts


def get_TFO_profile_allSparse(tpx_file):
    # assume data sorted on desending Stability
    #data = [begin, end, stability]
    profiles = {}
    profile_current = defaultdict(lambda: 0)
    stability_pre=None
    best_stability = {}
    max_len = 0
    
    for line in tpx_file:
        b, e, stability = line
        b=int(b)
        e=int(e)
        if stability != stability_pre:
            if stability_pre is not None:
                profiles[stability_pre]=dict(profile_current)
            stability_pre=stability

        for i in range(b,e):
            profile_current[i]+=1
            if (i not in best_stability):
                best_stability[i] = stability
            if (e > max_len):
                max_len = e

    if stability_pre is not None:
        profiles[stability_pre]=dict(profile_current)
                
    return {"profiles": profiles, "best_stability": best_stability}, max_len

class Ranges:
    container=[]
    def reset_container(self):
        self.container = []

    def add_range(self,b,e,count, i=0):
        if e<b:
            raise ValueError("invalid range %d-%d, count: %d, i: %d" % (b,e,count,i))
        if (b!=e):
            l = [count, (b + ((e-b)/2)), e-b+1]
        else:
            l = [count, b]
        self.container.append(l)

def profile2ranges(profiles):    
    profiles_range={}
    
    for stability in profiles.keys():
        profile = profiles[stability]
        profile_range = Ranges()
        profile_range.reset_container()
        
        range_b=None
        range_count=None
        i_pre = None
        keys = list(profile.keys())
        keys.sort(key=int)
        for i in keys:
            count = profile[i]
            i = int(i)
            count = int(count)
            if range_b is None:
                range_b = i
                i_pre = i
                range_count=count

            if count != range_count or i > i_pre + 1:
                profile_range.add_range(range_b, i_pre, range_count)
                range_b = i
                range_count = count
            i_pre = i
        
        profile_range.add_range(range_b,i_pre,range_count)
        profiles_range[stability]= profile_range.container

    return(profiles_range)            

def best_stability_to_array(best_stability, length):
    array = np.zeros(length)
    for key in best_stability.keys():
        #key to integer
        index = int(key)
        array[index] = best_stability[key]
    return list(array)


def compute_profile_from_tpx(tpx):
    data, length = get_TFO_profile_allSparse(tpx)
    profiles = profile2ranges(data["profiles"])
    best_stability = best_stability_to_array(data["best_stability"], length)
    to_export = {"profiles": profiles, "best_stability": best_stability}
    return msgpack.packb(to_export, use_bin_type=True)



def compute_profile_for_genome_browser(tpx_file, chr):
    TIME = datetime.now()
    profile_current = defaultdict(lambda: 0)
    max_len = 0
    for line in tpx_file:
        b, e, stability = line
        b=int(b)
        e=int(e)
        for i in range(b,e):
            profile_current[i]+=1
            if (e > max_len):
                max_len = e
    #Convert into list of intervals
    intervals = []
    previous_start = 0
    previous_count = None
    TIME = datetime.now()
    positions = [int(x) for x in profile_current.keys()]
    positions.sort()
    min_ = positions[0]
    for i in positions:
        count = profile_current[i]
        if (previous_count != count):
            if (previous_count is not None):
                intervals.append(f"{chr} {previous_start} {i-1} {previous_count}\n")
            if (previous_count is not None or count != 0):
                previous_count = count
                previous_start = i
    intervals.append(f"{chr} {previous_start} {max_len-1} {previous_count}\n")
    return intervals, min_, max_len
from datastructure import Place, Location
from utilities import *
import os
import logging
import csv

# Small data-structure handling the caching of locations, the computation of GPS locations notably requiring an API request
# The state of the cache on the disk and of the mapping in memory is kept consistent to make sure stuff is cached even if the analysis crashes in the middle

# NOTE: Currently, we only store fully computed locations, and assume that all stored locations are such.
# NOTE: We do not cache the computation of 

class Cache:

    def __init__(self,GLOB):

        # Checks if a cache already exists. If not, creates an empty one
        exists_cache = os.path.isfile(GLOB.cache)
        if not exists_cache:
            logging.info("No location cache, initializing one at {}".format(GLOB.cache))

            with open(GLOB.cache,'w',newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['city','state','country', 'country_iso','continent','GPS', 'airport'])


        # Parses the cache and loads it as a mapping from [Place]s to [Location]s
        with open(GLOB.cache,'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            # Skip the header
            next(reader)
            self.cache = {}
            for row in reader:
                row = get_args(row,[str,str,str,str,str,str,str])
                key = Place(*[row[i] for i in range(3)])
                if not key in self.cache:
                    self.cache[key] = Location(*([key] + [row[i].rstrip() for i in range(3,len(row))]))

    # Given a place, computes its full location and caches the result
    def cache_new_loc(self,GLOB,place):
        loc = Location(place)

        # Computes and set all location fields
        gps = loc.get_GPS()
        loc.set_GPS(gps)
        iso = loc.get_iso()
        loc.set_iso(iso)
        continent = loc.get_continent(iso)
        loc.set_continent(continent)
        airport = loc.get_airport(GLOB,iso,gps)
        loc.set_airport(airport)

        # Updates the dynamic cache
        self.cache[place] = loc

        # Updates the static cache
        with open(GLOB.cache,'a') as csv_file:
            appender = csv.writer(csv_file,delimiter=',',quoting=csv.QUOTE_MINIMAL)
            loc.write_csv_row(appender)

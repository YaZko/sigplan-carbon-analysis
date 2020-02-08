import copy
import unidecode
import os
import logging
import csv

from datastructure import Place, Location

from utilities import *

# Small data-structure handling the caching of locations, the computation of GPS locations notably requiring an API request
# The state of the cache on the disk and of the mapping in memory is kept consistent to make sure stuff is cached even if the analysis crashes in the middle

# NOTE: Currently, we only store fully computed locations, and assume that all stored locations are such.


class Cache:
    def __init__(self, GLOB):

        # Checks if a cache already exists. If not, creates an empty one
        exists_cache = os.path.isfile(GLOB.cache)
        if not exists_cache:
            logging.info("No location cache, initializing one at {}".format(GLOB.cache))

            with open(GLOB.cache, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(
                    ['city', 'state', 'country', 'country_iso', 'continent', 'GPS', 'airport'])

        # Parses the cache and loads it as a mapping from [Place]s to [Location]s
        with open(GLOB.cache, 'r') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            # Skip the header
            next(reader)
            self.cache = {}
            for row in reader:
                row = get_args(row, [str, str, str, str, str, str, str])
                key = Place(*[row[i] for i in range(3)])
                if not key in self.cache:
                    self.cache[key] = Location(*([key] +
                                                 [row[i].rstrip() for i in range(3, len(row))]))

    # Given a place, computes its full location and caches the result
    def cache_new_loc(self, GLOB, place):

        loc = Location(place)

        # Computes and set all location fields
        gps = loc.get_GPS()
        loc.set_GPS(gps)
        # print ("GPS done")
        iso = loc.get_iso()
        loc.set_iso(iso)
        # print ("ISO done")
        continent = loc.get_continent(iso)
        loc.set_continent(continent)
        airport = loc.get_airport(GLOB, iso, gps)
        loc.set_airport(airport)

        # Assuming all data has been found, we update the caches:
        if not (gps is None or iso is None or continent is None):
            # Updates the dynamic cache
            self.cache[place] = loc

            # Updates the static cache
            with open(GLOB.cache, 'a') as csv_file:
                appender = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                loc.write_csv_row(appender)
        else:
            raise (KeyError)
            # print("Location {} appears to be incorrect, giving up on it".format(loc))

    def check_cache_loc(self, GLOB, place):
        nplace = self.normalize_loc(place)
        if nplace not in self.cache:
            self.cache_new_loc(GLOB, nplace)

    def set_loc(self, GLOB, loc):
        cached_loc = self.cache[self.normalize_loc(loc.place)]
        loc.set_GPS(cached_loc.GPS)
        loc.set_iso(cached_loc.country_iso)
        loc.set_continent(cached_loc.continent)
        loc.set_airport(cached_loc.airport)

    @staticmethod
    def normalize_loc(place):
        city = unidecode.unidecode_expect_ascii(place.city).lower()
        country = unidecode.unidecode_expect_ascii(place.country).lower()
        place = copy.deepcopy(place)
        place.city = city
        place.coutry = country
        return place

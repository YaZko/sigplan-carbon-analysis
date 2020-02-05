from functools import reduce
from itertools import combinations
from statistics import mean
from time import sleep

import os
import json
import csv
import logging

from geopy import geocoders
from geopy import distance

from pycountry import countries
from pycountry_convert import country_alpha2_to_continent_code

from utilities import *

class Place:
    def __init__(self,city,state,country):
        self.city = city
        self.state = state
        self.country = country

    def csv(self):
        return "{},{},{}".format(self.city,self.state,self.country)

    def __repr__(self):
        return "Place: ({},{},{})".format(self.city,self.state,self.country)

    def __str__(self):
        if self.state is None:
            return "({},{})".format(self.city,self.country)
        else:
            return "({},{},{})".format(self.city,self.state,self.country)

    def __hash__(self):
        return hash((self.city, self.state, self.country))

    def __eq__(self,other):
        if self.state is None and other.state is None:
            return (self.city, self.country) == (other.city, other.country)
        else:
            return (self.city, self.state, self.country) == (other.city, other.state, other.country)


class Location:

    def __init__(self,place,iso = None,continent = None,GPS = None,airport = None):
        self.place = place
        self.continent = continent
        self.country_iso = iso
        if GPS is None:
            self.GPS = None
        elif type(GPS) == str:
            self.GPS = string_to_double(GPS)
        else:
            self.GPS = GPS
        self.airport = airport

    def csv(self):
        return "{},{},{},{},{},{}".format(self.place.city,self.place.state,self.place.country,self.country_iso,self.continent,self.GPS,self.airport)

    def __repr__(self):
        return "Location: ({},{},{},{},{},{})".format(self.place.city,self.place.state,self.place.country,self.country_iso,self.continent,self.GPS,self.airport)

    def __str__(self):
        return self.place.__str__()

    def set_GPS(self, coord):
        self.GPS = coord

    # TODO: rewrite this to handle with a shred of decency connection issues
    def get_GPS(self):
        gn = geocoders.GeoNames(username='acm_climate')
        query = self.place.city
        print ("Looking for GPS coordinates of {}".format(query))
        if self.place.country in ['USA','Canada'] and self.place.state is not None:
            query = query + ',' + self.place.state
        if self.place.country is not None:
            query = query + ',' + self.place.country
        while True:
            try:
                gps = gn.geocode(query,exactly_one = True)[1]
                break
            except Exception as e:
                if str(e) == 'Service timed out':
                    print('time out, retrying')
                    sleep(0.1)
                    continue
                else:
                    raise(e)
        return gps

    # Return the GPS coordinates of the location
    # If it is not set yet, retrieve it from the cache, else only computes it and updates the cache
    # Set it in either cases
    def get_and_set_GPS(self, GLOB, cache):
        if self.GPS is None:
            if not self.place in cache.cache:
                cache.cache_new_loc(GLOB,self.place)
            coord = cache.cache[self.place].GPS
            self.set_GPS(coord)
            return coord
        else:
            return self.GPS

    # Computes the distance between two locations
    def get_distance(self, GLOB, cache, start):
        c1 = start.get_and_set_GPS(GLOB, cache)
        c2 = self.get_and_set_GPS(GLOB, cache)
        return distance.distance(c1,c2).km

    def set_iso(self,iso):
        self.country_iso = iso

    # Computes the ISO norm of the countries for use by the country library
    # The error cases are hand-crafted disparities observed between the apis
    def get_iso(self):
        try:
            name = countries.get(name = self.place.country).alpha_2
        except KeyError:
            try:
                name = countries.get(common_name = self.place.country).alpha_2
            except KeyError:
                try:
                    name = countries.get(official_name = self.place.country).alpha_2
                except KeyError:
                    if self.place.country == 'USA':
                        name = 'US'
                    elif self.place.country == 'UK':
                        name = 'GB'
                    elif self.place.country == 'South Korea':
                        name = 'KR'
                    elif self.place.country == 'Russia':
                        name = 'RU'
                    elif self.place.country == 'Iran':
                        name = 'IR'
                    else:
                        name = self.place.country
        return name

    def get_and_set_iso(self,GLOB,cache):
        if self.country_iso is None:
            if not self.place in cache.cache:
                cache.cache_new_loc(GLOB,self.place)
            iso = cache.cache[self.place].country_iso
            self.set_iso(iso)
            return iso
        else:
            return self.country_iso

    def set_continent(self,continent):
        self.continent = continent

    def get_continent(self,iso):
        country = iso
        try:
            return country_alpha2_to_continent_code(country)
        except KeyError as e:
            print("Failed to find the continent associated to country {}".format(str(e).split(':')[1].strip()))
            return None

    def get_and_set_continent(self,GLOB,cache):
        if self.continent is None:
            if not self.place in cache.cache:
                cache.cache_new_loc(GLOB,self.place)
            continent = cache.cache[self.place].continent
            self.set_continent(continent)
            return continent
        else:
            return self.continent

    def set_airport(self,airport):
        self.airport = airport

    def get_airport(self,GLOB,iso,gps):
        name = iso
        start = gps

        data = json.loads(open(GLOB.airports).read())
        closest = None
        best_dist = None
        for d in data:
            if d['type'] in ['medium_airport','large_airport'] and d['country'] == name:
                try:
                    dist = distance.distance(start,(float(d['latitude']),float(d['longitude'])))
                except:
                    pass
                else:
                    if closest is None or best_dist > dist:
                        closest = d['ident']
                        best_dist = dist

        if best_dist is None:
            print('Warning: no airport found for {}'.format(self))
        elif best_dist > 1000:
            print('Warning: airport found for {} is at {}'.format(self,best_dist))

        return closest

    def get_and_set_airport(self,GLOB,cache):
        if self.airport is None:
            if not self.place in cache.cache:
                cache.cache_new_loc(GLOB,self.place)
            airport = cache.cache[self.place].airport
            self.set_airport(airport)
            return airport
        else:
            return self.airport

    def write_csv_row(self,writer):
        writer.writerow([self.place.city,
                         self.place.state,
                         self.place.country,
                         self.country_iso,
                         self.continent,
                         self.GPS,
                         self.airport
        ])


# The data-structure representing an entry in our database. Contains the information describing the participation of an individual to a conference

class RawData:

    def __init__(self,
                 id, city, state, country,
                 conference, year,
                 iso = None, continent = None, footprint = None, GPS = None, airport = None):
        self.id = id
        self.location = Location(Place(city,state,country),iso,continent,GPS,airport)
        self.conference = conference
        self.year = year
        self.footprint = None if footprint == None else round(footprint,4)
        if GPS is None:
            self.location.GPS = None
        elif type(GPS) == str:
            self.location.GPS = string_to_double(GPS)
        else:
            self.location.GPS = GPS
        self.location.airport = airport

    # TODO: define some getters maybe...
    def csv(self):
        return "{},{},{},{},{},{}".format(self.id,self.location.place.city,self.location.place.state,self.location.place.country,self.conference,self.year)

    def __repr__(self):
        return "Data: ({},{},{},{},{},{})".format(self.id,self.location.place.city,self.location.place.state,self.location.place.country,self.conference,self.year)

    def __str__(self):
        return "Data: ({},{},{},{},{},{})".format(self.id,self.location.place.city,self.location.place.state,self.location.place.country,self.conference,self.year)

    def set_footprint(self, cost):
        self.footprint = cost

    def get_cost_acm(self, GLOB, cache, destination):
        logging.debug('Estimating acm cost (radiative forcing included) from {} to {}'.format(self.location,destination))
        dist = self.location.get_distance(GLOB, cache, destination)
        if dist < 785:
            emission_factor = 0.14735
        elif dist < 3700:
            emission_factor = 0.08728
        else:
            emission_factor = 0.077610
        cost = round(dist * emission_factor * GLOB.radiative_factor_index * 2,4)
        return cost

    def get_and_set_cost_acm(self, GLOB, cache, destination):
        if self.footprint is None:
            cost = self.get_cost_acm(GLOB, cache, destination)
            self.set_footprint(cost)
            return cost
        else:
            return self.footprint

    def get_cost_CoolEffect(self, GLOB, cache, destination):
        logging.debug("Estimating carbon footprint according to CoolEffect's methodology from {} to {}".format(self.location,destination))
        dist = self.location.get_distance(GLOB, cache, destination)
        if dist < 482:
            emission_factor = 0.14106
        elif dist < 3700:
            emission_factor = 0.08513
        else:
            emission_factor = 0.10439
        cost = round(dist * emission_factor * GLOB.radiative_factor_index * 2,4)
        return cost

    def get_and_set_cost_CoolEffect(self, GLOB, cache, destination):
        if self.footprint is None:
            cost = self.get_cost_CoolEffect(GLOB, cache, destination)
            self.set_footprint(cost)
            return cost
        else:
            return self.footprint

    # Model used by thegoodtraveler, a non-profit funded by airports.
    # See: https://thegoodtraveler.org/what-is-offsetting/faqs/
    # The model is weirdly simplistic without being absurdly wrong
    def get_thegoodtraveler(self, GLOB, cache, destination):
        logging.debug("Estimating carbon footprint according to thegoodtraveler's methodology from {} to {}".format(self.location,destination))
        dist = self.location.get_distance(GLOB, cache, destination)
        cost = round(dist * 0.0975,4)
        return cost

    def get_and_set_cost_thegoodtraveler(self, GLOB, cache, destination):
        if self.footprint is None:
            cost = self.get_cost_thegoodtraveler(GLOB, cache, destination)
            self.set_footprint(cost)
            return cost
        else:
            return self.footprint

    def get_footprint(self, GLOB, cache, destination):
        if GLOB.model == 'acm':
            return self.get_cost_acm(GLOB, cache, destination)
        elif GLOB.modol == 'cool':
            return self.get_cost_CoolEffect(GLOB, cache, destination)
        else:
            raise("Model not recognize in global environment: {}".format(GLOB.model))

    def get_and_set_footprint(self,GLOB,cache,destination):
        if GLOB.model == 'acm':
            return self.get_and_set_cost_acm(GLOB, cache, destination)
        elif GLOB.model == 'cool':
            return self.get_and_set_cost_CoolEffect(GLOB, cache, destination)
        else:
            raise("Model not recognize in global environment: {}".format(GLOB.model))



    # Write the part of the data that is deemed relevant for human concern
    def write_csv_row(self,writer):
        writer.writerow([self.id,
                         self.location.place.city,
                         self.location.place.state,
                         self.location.place.country,
                         self.location.continent,
                         self.conference,
                         self.year,
                         self.footprint
        ])


    # BEGIN DEPRECATED
    def get_cost_brighter(self, destination):
        print('Estimating brighter cost from {} to {}'.format(self.location,destination))
        airport_source = self.location.get_and_set_airport()
        airport_destination = destination.get_and_set_airport()
        try:
            calculator = CO2_calc(airport_source, airport_destination)
            cost = calculator.get_carbon_cost()
        except:
            print('Warning: failed to estimate cost from {} to {}'.format(self.location,destination))
            cost = None
        return cost

    def set_cost_brighter(self,cost):
        self.cost_brighter = cost

    def get_and_set_cost_brighter(self, destination):
        if self.cost_brighter is None:
            cost = self.get_cost_brighter(destination)
            self.set_cost_brighter(cost)
            return cost
        else:
            return self.cost_brighter

    # END DEPRECATED


from functools import reduce
from itertools import combinations
from statistics import mean
from time import sleep

import json
import csv

from geopy import geocoders
from geopy import distance

from pycountry import countries
from pycountry_convert import country_alpha2_to_continent_code

from utilities import *

class Location:

    def __init__(self,city,state,country, iso = None,continent = None,GPS = None,airport = None):
        self.city = city
        self.state = state
        self.country = country
        self.continent = continent
        self.country_iso = iso
        self.GPS = GPS
        self.airport = airport

    def csv(self):
        return "{},{},{},{},{},{}".format(self.city,self.state,self.country,self.country_iso,self.continent,self.GPS,self.airport)

    def __repr__(self):
        return "Location: ({},{},{},{},{},{})".format(self.city,self.state,self.country,self.country_iso,self.continent,self.GPS,self.airport)

    def __str__(self):
        if self.state is None:
            return "({},{})".format(self.city,self.country)
        else:
            return "({},{},{})".format(self.city,self.state,self.country)

    def set_GPS(self, coord):
        self.GPS = coord

    def get_GPS(self):
        gn = geocoders.GeoNames(username='acm_climate')
        query = self.city
        if self.country in ['USA','Canada'] and self.state is not None:
            query = query + ',' + self.state
        if self.country is not None:
            query = query + ',' + self.country
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

    def get_and_set_GPS(self):
        if self.GPS is None:
            coord = self.get_GPS()
            self.set_GPS(coord)
            return coord
        else:
            return self.GPS

    def get_distance(self,start):
        c1 = start.get_and_set_GPS()
        c2 = self.get_and_set_GPS()
        return distance.distance(c1,c2).km

    def set_iso(self,iso):
        self.country_iso = iso

    def get_iso(self):
        try:
            name = countries.get(name = self.country).alpha_2
        except KeyError:
            try:
                name = countries.get(common_name = self.country).alpha_2
            except KeyError:
                try:
                    name = countries.get(official_name = self.country).alpha_2
                except KeyError:
                    if self.country == 'USA':
                        name = 'US'
                    elif self.country == 'UK':
                        name = 'GB'
                    elif self.country == 'South Korea':
                        name = 'KR'
                    elif self.country == 'Russia':
                        name = 'RU'
                    elif self.country == 'Iran':
                        name = 'IR'
                    else:
                        name = self.country
        return name

    def get_and_set_iso(self):
        if self.country_iso is None:
            iso = self.get_iso()
            self.set_iso(iso)
            return iso
        else:
            return self.country_iso

    def set_continent(self,continent):
        self.continent = continent

    def get_continent(self):
        country = self.get_and_set_iso()
        return country_alpha2_to_continent_code(country)

    def get_and_set_continent(self):
        if self.continent is None:
            continent = self.get_continent()
            self.set_continent(continent)
            return continent
        else:
            return self.continent

    def set_airport(self,airport):
        self.airport = airport

    def get_and_set_airport(self):
        if not self.airport is None:
            return self.airport

        name = self.get_and_set_iso()
        start = self.get_and_set_GPS()

        data = json.loads(open('../data/airports.json').read())
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
            print('Warning: airport found for {} is at {}km'.format(self,best_dist))

        self.set_airport(closest)
        return closest

# The data-structure representing an entry in our database. Contains the information describing the participation of an individual to a conference

class RawData:

    def __init__(self, id, city, state, country,
                 conference, year,
                 iso = None, continent = None, cost_acm = None, cost_brighter = None,
                 GPS = None,
                 airport = None):
        self.id = id
        self.location = Location(city,state,country,iso,continent,GPS,airport)
        self.conference = conference
        self.year = year
        self.cost_acm = None if cost_acm == None else round(cost_acm,4)
        self.cost_brighter = cost_brighter
        if not GPS is None:
            x,y = GPS.split(',')
            x,y = float(x.split('(')[1].strip()), float(y.split(')')[0].strip())
            self.location.GPS = x,y
        else:
            self.location.GPS = None
        self.airport = airport

    def csv(self):
        return "{},{},{},{},{},{}".format(self.id,self.location.city,self.location.state,self.location.country,self.conference,self.year)

    def __repr__(self):
        return "Data: ({},{},{},{},{},{})".format(self.id,self.location.city,self.location.state,self.location.country,self.conference,self.year)

    def __str__(self):
        return "Data: ({},{},{},{},{},{})".format(self.id,self.location.city,self.location.state,self.location.country,self.conference,self.year)

    def set_iso(self,iso):
        self.location.set_iso(iso)

    def set_airport(self,airport):
        self.location.airport = airport

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

    def get_cost_acm(self, destination):
        # print('Estimating acm cost (radiative forcing included) from {} to {}'.format(self.location,destination))
        dist = self.location.get_distance(destination)
        if dist < 785:
            emission_factor = 0.14735
        elif dist < 3700:
            emission_factor = 0.08728
        else:
            emission_factor = 0.077610
        radiative_factor = 1.891
        cost = round(dist * emission_factor * radiative_factor * 2,4)
        return cost

    def get_cost_CoolEffect(self, destination):
        # print('Estimating carbon footprint according to CoolEffect's methodology from {} to {}'.format(self.location,destination))
        dist = self.location.get_distance(destination)
        if dist < 482:
            emission_factor = 0.14106
        elif dist < 3700:
            emission_factor = 0.08513
        else:
            emission_factor = 0.10439
        radiative_factor = 1
        cost = round(dist * emission_factor * radiative_factor * 2,4)
        return cost

    def set_cost_acm(self,cost):
        self.cost_acm = cost

    def get_and_set_cost_acm(self, destination):
        if self.cost_acm is None:
            cost = self.get_cost_acm(destination)
            self.set_cost_acm(cost)
            return cost
        else:
            return self.cost_acm

    def write_data(self,writer):
        writer.writerow([self.id,
                         self.location.city,
                         self.location.state,
                         self.location.country,
                         self.conference,
                         self.year,
                         self.location.country_iso,
                         self.location.continent,
                         self.cost_acm,
                         self.cost_brighter,
                         self.location.GPS,
                         self.location.airport
        ])


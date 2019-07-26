from functools import reduce
from itertools import combinations
from statistics import mean
from time import sleep

import json
import csv
import logging

from geopy import geocoders
from geopy import distance

from pycountry import countries
from pycountry_convert import country_alpha2_to_continent_code

from utilities import *

from datastructure import *

# The data-structure storing in memory all the entries we have, as well as the locations of the conferences.
# Requests are built upon this data-structure and are parameterized by a function mapping carbon costs to a pair of locations.

class DB:

    # A Database contains a list of RawData 'data', a mapping (conf -> year -> Location) 'confs'
    def __init__(self, data, confs):
        self.data = data
        self.confs = confs

    def get_participants_conf(self,conf):
        return [d for d in self.data if d.conference == conf]

    def get_participants_conf_year(self,conf,year):
        return [d for d in self.data if d.conference == conf and d.year == year]

    def preprocess_confs(self,GLOB,cache):
        logging.info("Starting the preprocessing of the locations of the events")
        for name,conf in self.confs.items():
            for year,loc in conf.items():
                coord = loc.get_and_set_GPS(GLOB,cache)
                iso = loc.get_and_set_iso(GLOB,cache)
                continent = loc.get_and_set_continent(GLOB,cache)
                airport = loc.get_and_set_airport(GLOB,cache)

    def preprocess_users(self,GLOB,cache):
        logging.info("Starting the preprocessing of the participation database")
        confs = self.confs
        for name,conf in confs.items():
            for year,conf_loc in conf.items():
                participants = self.get_participants_conf_year(name,year)
                for d in participants:
                    loc = d.location
                    coord = loc.get_and_set_GPS(GLOB,cache)
                    iso = loc.get_and_set_iso(GLOB,cache)
                    continent = loc.get_and_set_continent(GLOB,cache)
                    airport = loc.get_and_set_airport(GLOB,cache)

                    if GLOB.model == 'acm':
                        footprint = d.get_and_set_cost_acm(GLOB, cache, conf_loc)
                    elif GLOB.model == 'cool':
                        cost_brighter = d.get_and_set_cost_CoolEffect(GLOB, cache, conf_loc)
                    else:
                        raise("Model not recognize in global environment: {}".format(GLOB.model))

    def preprocess(self,GLOB,cache):
        self.preprocess_confs(GLOB,cache)
        self.preprocess_users(GLOB,cache)
        self.print_user_db(GLOB)

    def print_user_db(self, GLOB):
        logging.info("Writing the raw emission data at {}".format(GLOB.output_raw))
        with open(GLOB.output_raw,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['id','city','state','country','continent',
                             'conference','year',
                             'footprint'])
            for d in self.data:
                d.write_csv_row(writer)

    def analysis(self,output_file):
        with open(output_file,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conf','year','location',
                             'number of participants',
                             'acm total cost', 'acm average cost',
                             'brighter total cost', 'brighter average cost'])
            for name,conf in self.confs.items():
                for year,conf_loc in conf.items():
                    select_data = [d for d in self.data if d.conference == name and d.year == year]
                    nb = len(select_data)
                    if nb > 0:
                        total_acm = round(reduce(lambda x,y: x + y.cost_acm, select_data, 0)/1000,2)
                        average_acm = round(total_acm/nb,2)
                        total_brighter = round(reduce(lambda x,y: x + y.cost_brighter, select_data, 0)/1000,2)
                        average_brighter = round(total_brighter/nb,2)
                        writer.writerow([name, year, conf_loc.city, nb,
                                         total_acm, average_acm,
                                         total_brighter,average_brighter])


    def analysis_demographic(self,output_file):
        output = output_file.split(".csv")[0]
        output_file_main = output + '.csv'
        output_file_conf = output + '-per-conf.csv'
        output_file_delta = output + '-delta.csv'

        continents = ['EU','NA','AS','SA','AF','OC']

        init_distrib = {'EU':0, 'NA':0, 'AS':0, 'SA':0, 'AF':0, 'OC':0, 'SAME':0}

        # Global distribution of origin
        distrib_total = init_distrib.copy()
        total_attendance = 0
        # Distribution for each origin of the conf
        distrib_per_loc = {'EU':init_distrib.copy(), 'NA':init_distrib.copy(), 'AS':init_distrib.copy(), 'SA':init_distrib.copy(), 'AF':init_distrib.copy(), 'OC':init_distrib.copy()}
        total_attendance_per_loc = init_distrib.copy()

        with open(output_file_main,'w',newline='') as csvfile_main:
            with open(output_file_conf,'w',newline='') as csvfile_conf:

                writer_main = csv.writer(csvfile_main, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer_conf = csv.writer(csvfile_conf, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer_main.writerow(['conf','year','continent'] + continents + ['SAME'])
                writer_conf.writerow(['conf'] + continents + ['SAME'])

                # For each conference
                for name,conf in self.confs.items():

                    # Distribution for the conference 'name'
                    distrib_conf = init_distrib.copy()
                    total_attendance_conf = 0

                    # For each instance of the conference 'name'
                    for year,conf_loc in conf.items():

                        # List of participants to 'name[year]'
                        select_data = [d for d in self.data if d.conference == name and d.year == year]
                        attendance = len(select_data)

                        # If we actually have data for this instance
                        if attendance > 0:
                            # Distribution of this instance
                            nb_loc = {}

                            total_attendance = total_attendance + attendance
                            total_attendance_per_loc[conf_loc.continent] = total_attendance_per_loc[conf_loc.continent] + attendance
                            total_attendance_conf = total_attendance_conf + attendance

                            for l in continents:
                                nb_loc[l] = len([d for d in select_data if d.location.continent == l])

                                distrib_total[l] = distrib_total[l] + nb_loc[l]
                                distrib_per_loc[conf_loc.continent][l] = distrib_per_loc[conf_loc.continent][l] + nb_loc[l]
                                distrib_conf[l] = distrib_conf[l] + nb_loc[l]

                            nb_same = len([d for d in select_data if d.location.continent == conf_loc.continent])
                            distrib_total['SAME'] = distrib_total['SAME'] + nb_same
                            distrib_per_loc[conf_loc.continent]['SAME'] = distrib_per_loc[conf_loc.continent]['SAME'] + nb_same
                            distrib_conf['SAME'] = distrib_conf['SAME'] + nb_same

                            main_row = [norm_perc(nb_loc[x],attendance) for x in continents]
                            writer_main.writerow(
                                [name, year, conf_loc.continent] +
                                main_row +
                                [norm_perc(nb_same,attendance)]
                            )

                    conf_row = [norm_perc(distrib_conf[x],total_attendance_conf) for x in continents]
                    writer_conf.writerow([name] + conf_row + [norm_perc(distrib_conf['SAME'],total_attendance_conf)])

        with open(output_file_delta,'w',newline='') as csvfile_delta:
            writer = csv.writer(csvfile_delta,delimiter=',',quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Conf Loc'] + continents + ['SAME'])

            writer.writerow(['Any'] + [norm_perc(distrib_total[x],total_attendance) for x in continents] + [normalize(distrib_total['SAME'],total_attendance)])
            for c in continents:
                if not total_attendance_per_loc[c] is 0:
                    writer.writerow([c] + [norm_perc(distrib_per_loc[c][x],total_attendance_per_loc[c]) for x in continents] + [normalize(distrib_per_loc[c]['SAME'],total_attendance_per_loc[c])])


    # Assuming the participants would not have changed, speculate the carbon cost of a conference assuming it had taken place in a different location
    def speculate_cost_at_loc(self,name,year,loc):
        select_data = [d for d in self.data if d.conference == name and d.year == year]
        nb = len(select_data)

        if nb > 0:
            costs = [d.get_cost_acm(loc) for d in select_data]
            total_cost = round(reduce(lambda x,y: x + y, costs, 0)/1000,2)
            average_cost = round(total_cost/len(select_data),2)

            print("{} {} would have cost {} per participant if organized in {}".format(name,year,average_cost,loc))
            return average_cost

    # Assuming the participants would not have changed, speculate the carbon cost of a conference assuming it was colocated between its actual location and another one of choice
    def speculate_cost_split(self,name,year,loc):
        select_data = [d for d in self.data if d.conference == name and d.year == year]
        nb = len(select_data)
        loc1,loc2 = self.confs[name][year], loc

        if nb > 0:
            costs = [min(d.get_cost_acm(loc1),d.get_cost_acm(loc2)) for d in select_data]
            total_cost = round(reduce(lambda x,y: x + y, costs, 0)/1000,2)
            average_cost = round(total_cost/len(select_data),2)

            print("{} {} would have cost {} per participant if colocated between {} and {}".format(name,year,average_cost,loc1,loc2))
            return average_cost

    # Overlap of participation, in percentage, between two instances of two conferences
    def participation_overlap_single(self,name1,year1,name2,year2):

        participants1 = [d.id for d in self.data if d.conference == name1 and d.year == year1]
        participants2 = [d.id for d in self.data if d.conference == name2 and d.year == year2]

        if len(participants1) > 0 and len(participants2) > 0:
            intersection = list(set(participants1) & set(participants2))
            return round(len(intersection) * 2 * 100 / (len(participants1) + len(participants2) ),2)
        else:
            return None

    # Overlap of participation, in percentage, between any two instances of a given conference
    def participation_overlap_conf(self,output_file,name,years):

        output_file = fill_hole_string(output_file, '_' + name)

        with open(output_file,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['year1','year2','overlap'])
            for pair in combinations(years,2):
                overlap = self.participation_overlap_single(name,pair[0],name,pair[1])
                if not overlap is None:
                    writer.writerow([pair[0],pair[1],overlap])

    def participation_overlap_conf_generate_all(self,output_file,confs,years):
        for c in confs:
            self.participation_overlap_conf(output_file,c,years)

    # Overlap of participation, in percentage, between two given conferences for each year
    def participation_overlap_year(self,output_file,name1,name2,years):

        output_file = fill_hole_string(output_file, '_' + name1 + '_' + name2)

        with open(output_file,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['year','overlap'])
            for year in years:
                overlap = self.participation_overlap_single(name1,year,name2,year)
                if not overlap is None:
                    writer.writerow([year,overlap])

    def participation_overlap_year_generate_all(self,output_file,confs,years):
        for pair in combinations(confs,2):
            self.participation_overlap_year(output_file,pair[0],pair[1],years)

    def get_number_of_participations(self, output_file, confs):

        with open(output_file,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conference','avrg nb of participations','at least 2','at least 3','at least 4','at least 5'])

            res = {x:{} for x in confs}
            for d in self.data:
                if d.conference in confs:
                    if d.id in res[d.conference]:
                        res[d.conference][d.id] = res[d.conference][d.id] + 1
                    else:
                        res[d.conference][d.id] = 1

            # We forget about the idea, each conf maps to a list of number of participations
            for x in confs:
                print(len(res[x]))
            res = {k:list(res[k].values()) for k in res}
            aggregated = [x for v in res.values() for x in v]

            print(len(aggregated))

            # Overall
            average = round(sum(aggregated)/len(aggregated),2)
            row = [norm_perc(len([v for v in aggregated if v > i]),len(aggregated)) for i in range(1,5)]
            writer.writerow(['ALL',average] + row)

            for c in confs:
                average = round(sum(res[c])/len(res[c]),2)
                row = [norm_perc(len([v for v in res[c] if v > i]),len(res[c])) for i in range(1,5)]
                writer.writerow([c,average] + row)


    def get_old_timers(self,output_file,confs,years):

        for conf in confs:

            output_file_conf = fill_hole_string(output_file, conf)

            with open(output_file_conf,'w',newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)

                writer.writerow(['year','old timers'])

                for year in years:
                    select_data = [d.id for d in self.data if d.conference == conf and d.year == year]
                    if len(select_data) > 0:
                        select_old_data = [d.id for d in self.data if d.conference == conf and d.year < year]
                        old_timers      = [c for c in select_data if c in select_old_data]

                        res = norm_perc(len(old_timers),len(select_data))
                        writer.writerow([year,res])

    def pick_optimal(self,conf,year,candidates):
        print("Picking optimal for {} {}".format(conf,year))
        select_data = [d for d in self.data if d.conference == conf and d.year == year]
        nb = len(select_data)
        if nb > 0:
            base_total = round(reduce(lambda x,y: x + y.cost_acm, select_data, 0)/1000,2)
            base_average = round(base_total/nb,2)
            best_average = base_average
            best_loc = "SAME"

            for loc in candidates:
                loc = Location(*loc)
                costs = [d.get_cost_acm(loc) for d in select_data]
                total = round(reduce(lambda x,y: x + y, costs, 0)/1000,2)
                average = round(total/nb,2)
                if best_average > average:
                    best_average = average
                    best_loc = loc

            return (base_average,best_average,best_loc)

        else:
            return None


    def pick_optimals(self,output_file,confs,years,candidates):

        with open(output_file,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conf','year','orig. loc.','orig. cost', 'best loc.', 'best cost', 'saved'])
            for conf in confs:
                for year in years:
                    x = self.pick_optimal(conf,year,candidates)
                    if not x is None:
                        (base,best,best_loc) = x
                        best_loc = best_loc if best_loc == 'SAME' else best_loc.city
                        writer.writerow([conf,year,self.confs[conf][year].city,base,best_loc,best,norm(base-best)])



############# BEGIN DEPRECATED ############

    # Compute the average carbone cost per participant of a conference 'conf' during year 'year'
    def get_average_cost_conf_year(self,conf,year):
        conf_loc = self.confs[conf][year]
        select_data = [d for d in self.data if d.conference == conf and d.year == year]
        if len(select_data) is 0:
            print('Missing data for conference {} during year {}'.format(conf,year))
            return 0
        else:
            get_costs = [self.CO2_estimator(d.location,conf_loc) for d in select_data]
            get_costs = [d for d in get_costs if d is not None]
            return mean(get_costs)

    # Compute the average carbone cost per participant of a conference 'conf' for all years available
    def get_average_cost_conf(self,conf):
        editions = self.confs[conf]
        means = [self.get_average_cost_conf_year(conf,year) for year in editions]
        return mean(means)

    # Compute the average carbone cost per participant over all available data
    def get_average_cost_confs(self):
        confs = self.confs
        means = [self.get_average_cost_conf(conf) for conf in confs]
        return mean(means)

    # Compute the carbone cost of a conference 'conf' during year 'year' assuming that the conference
    # were to have taken place at location 'loc', with the same participants
    def get_cost_conf_year_at_loc(self,conf,year,loc):
        conf_loc = loc
        select_data = [d for d in self.data if d.conference == conf and d.year == year]
        if len(select_data) is 0:
            print('Missing data for conference {} during year {}'.format(conf,year))
            return 0
        else:
            get_costs = [self.CO2_estimator(d.location,conf_loc) for d in select_data]
            return reduce(lambda x,y: x + y,get_costs,0)

    # Compute the carbone cost of a conference 'conf' during year 'year'
    def get_cost_conf_year(self,conf,year):
        return self.get_cost_conf_year_at_loc(conf,year,self.confs[conf][year])

    # Compute the carbone cost of a conference 'conf' for all years available
    def get_cost_conf(self,conf):
        editions = self.confs[conf]
        return reduce(lambda x,y: x + y, [self.get_cost_conf_year(conf,year) for year in editions],0)


### Rendered deprecated by the introduction of the caching mechanism
    def print_conf_db(self,file):
        print("Caching conf db")
        with open(file,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conference','year','city','state','country','country_iso','continent','GPS','airport'])
            for name,conf in self.confs.items():
                for year,c in conf.items():
                    writer.writerow([name,
                                     year,
                                     c.city,
                                     c.state,
                                     c.country,
                                     c.country_iso,
                                     c.continent,
                                     c.GPS,
                                     c.airport
                    ])

############# END DEPRECATED ############


from functools import reduce
from itertools import combinations, permutations
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

    # This routine checks for each location of each conference that the data for this location are already cached.
    # If not, it tries to compute them and cache them.
    # If it fails, it reports the likely to be erroneous data entry, and removes it from the conferences of consideration
    def preprocess_confs(self,GLOB,cache):
        logging.info("Starting the preprocessing of the locations of the events")
        buggy_inputs = []
        for name,conf in self.confs.items():
            for year,loc in conf.items():
                # print('Processing {} {}'.format(name,year))
                try:
                    cache.check_cache_loc(GLOB,loc.place)
                    cache.set_loc(GLOB,loc)
                except:
                    buggy_inputs.append((name,year))
                    print('WARNING: in the list of conference, entry {} {} at {} cannot be processed and has been ignored\n'.format(name,year,loc))
        for name,year in buggy_inputs:
            self.confs[name].pop(year)

    def preprocess_users(self,GLOB,cache):
        logging.info("Starting the preprocessing of the participation database")
        confs = self.confs
        buggy_inputs = []
        for name,conf in confs.items():
            for year,conf_loc in conf.items():
                # print('Processing conference {} {}\n'.format(name,year))
                participants = self.get_participants_conf_year(name,year)
                for d in participants:
                    loc = d.location
                    try:
                        cache.check_cache_loc(GLOB,loc.place)
                        cache.set_loc(GLOB,loc)
                        footprint = d.get_and_set_footprint(GLOB, cache, conf_loc)
                        if footprint is None:
                            print(conf_loc)
                            raise KeyError
                    except:
                        print('WARNING: in the list of participants, entry {} cannot be processed and has been ignored\n'.format(d))
                        buggy_inputs.append(d)
        for d in buggy_inputs:
            self.data.remove(d)

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

    def footprint_per_conf(self, GLOB):
        with open(GLOB.footprint_confs,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conf','year','location','nb participants',
                             'total cost', 'average cost'])
            for name,conf in self.confs.items():
                for year,conf_loc in conf.items():
                    select_data = [d for d in self.data if d.conference == name and d.year == year]
                    for d in select_data:
                        if d.footprint is None:
                            print(d)
                            raise KeyError
                    nb = len(select_data)
                    if nb > 0:
                        total_footprint = round(reduce(lambda x,y: x + y.footprint, select_data, 0)/1000,2)
                        average_footprint = round(total_footprint/nb,2)
                        writer.writerow([name, year, conf_loc.place.city, nb,
                                         total_footprint, average_footprint])

    def analysis_demographic(self,GLOB):
        output_file_main  = fill_hole_string(GLOB.output_demographic,'')
        output_file_conf  = fill_hole_string(GLOB.output_demographic,'_per_conf')
        output_file_delta = fill_hole_string(GLOB.output_demographic,'_delta')

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
                writer_main.writerow(['Conference','Year','Continent'] + continents + ['Local'])
                writer_conf.writerow(['Conference'] + continents + ['Local'])

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

                writer_conf.writerow(['Any'] + [norm_perc(distrib_total[x],total_attendance) for x in continents] + [norm_perc(distrib_total['SAME'],total_attendance)])

        with open(output_file_delta,'w',newline='') as csvfile_delta:
            writer = csv.writer(csvfile_delta,delimiter=',',quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Location'] + continents + ['Local'])

            for c in continents:
                if not total_attendance_per_loc[c] is 0:
                    writer.writerow([c] + [norm_perc(distrib_per_loc[c][x],total_attendance_per_loc[c]) for x in continents] + [norm_perc(distrib_per_loc[c]['SAME'],total_attendance_per_loc[c])])
            writer.writerow(['Any'] + [norm_perc(distrib_total[x],total_attendance) for x in continents] + [norm_perc(distrib_total['SAME'],total_attendance)])

    # Overlap of participation, in percentage, between two instances of two conferences
    def participation_overlap_single(self,name1,year1,name2,year2):

        participants1 = set([d.id for d in self.data if d.conference == name1 and d.year == year1])
        participants2 = set([d.id for d in self.data if d.conference == name2 and d.year == year2])

        if len(participants1) > 0 and len(participants2) > 0:
            intersection = participants1 & participants2
            return norm(len(intersection) * 2 * 100 / (len(participants1) + len(participants2)))
        else:
            return None

    # Overlap of participation, in percentage, between any two instances of a given conference
    def participation_overlap_intra_conf(self,GLOB,name):

        output_file = fill_hole_string(GLOB.output_overlap_intra_conf, '_' + name)

        with open(output_file,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Year1','Year2','Overlap'])
            for pair in combinations(GLOB.years_processed,2):
                overlap = self.participation_overlap_single(name,pair[0],name,pair[1])
                if not overlap is None:
                    writer.writerow([pair[0],pair[1],overlap])

    def participation_overlap_intra_conf_generate_all(self,GLOB):
        for c in GLOB.confs_processed:
            self.participation_overlap_intra_conf(GLOB,c)

    # Overlap of participation, in percentage, between two given conferences for each year
    def participation_overlap_cross_conf(self,GLOB,conf1,conf2):

        output_file = fill_hole_string(GLOB.output_overlap_cross_conf, '_' + conf1 + '_' + conf2)

        with open(output_file,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Year','Overlap'])
            for year in GLOB.years_processed:
                overlap = self.participation_overlap_single(conf1,year,conf2,year)
                if not overlap is None:
                    writer.writerow([year,overlap])

            # Aggregated overlap: percentage of participants having been at least once at both conferences
            # Note: the percentage is computed with respect to the mean of the number of unique participants
            # to both conferences
            participants1 = set([d.id for d in self.data if d.conference == conf1])
            participants2 = set([d.id for d in self.data if d.conference == conf2])

            if len(participants1) > 0 and len(participants2) > 0:
                intersection = participants1 & participants2
                agg = norm(len(intersection) * 2 * 100 / (len(participants1) + len(participants2)))
                writer.writerow(["Any",agg])

    def participation_overlap_cross_conf_generate_all(self,GLOB):
        for pair in combinations(GLOB.confs_processed,2):
            self.participation_overlap_cross_conf(GLOB,pair[0],pair[1])

    def get_number_of_participations(self, GLOB):

        with open(GLOB.output_number_of_participations,'w',newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Conference','Avrg nb of participations','>= 2','>= 3','>= 4','>= 5'])

            # res: conf |-> id_participant |-> number of participations to conf specifically
            res = {x:{} for x in GLOB.confs_processed}
            for d in self.data:
                if d.conference in GLOB.confs_processed:
                    if d.id in res[d.conference]:
                        res[d.conference][d.id] = res[d.conference][d.id] + 1
                    else:
                        res[d.conference][d.id] = 1

            # We forget about the id, each conf maps to a list of number of participations
            res = {k:list(res[k].values()) for k in res}
            aggregated = [x for v in res.values() for x in v]

            # Overall
            average = norm(sum(aggregated)/len(aggregated))
            row = [norm_perc(len([v for v in aggregated if v > i]),len(aggregated)) for i in range(1,5)]
            writer.writerow(['ALL',average] + row)

            for c in GLOB.confs_processed:
                average = round(sum(res[c])/len(res[c]),2)
                row = [norm_perc(len([v for v in res[c] if v > i]),len(res[c])) for i in range(1,5)]
                writer.writerow([c,average] + row)


    def get_old_timers(self,GLOB):

        for conf in GLOB.confs_processed:

            output_file_conf = fill_hole_string(GLOB.output_old_timer, conf)

            with open(output_file_conf,'w',newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)

                writer.writerow(['year','old timers'])

                for year in GLOB.years_processed:
                    select_data = [d.id for d in self.data if d.conference == conf and d.year == year]
                    if len(select_data) > 0:
                        select_old_data = [d.id for d in self.data if d.conference == conf and d.year < year]
                        old_timers      = [c for c in select_data if c in select_old_data]

                        res = norm_perc(len(old_timers),len(select_data))
                        writer.writerow([year,res])

    def pick_optimal_list(self,GLOB, cache, conf, year, count):
        logging.debug("Picking optimal for {} {}".format(conf,year))
        select_data = [d for d in self.data if d.conference == conf and d.year == year]
        nb = len(select_data)
        if nb > 0:
            base_total = round(reduce(lambda x,y: x + y.footprint, select_data, 0)/1000,2)
            base_average = round(base_total/nb,2)
            best_average = base_average
            base_loc = self.confs[conf][year]
            best_locs = [base_loc] * count

            for locs in combinations(GLOB.city_candidates, count):
                    locs = [Location(Place(*loc)) for loc in locs]
                    costs = [min([d.get_footprint(GLOB, cache, loc) for loc in locs])
                                for d in select_data]
                    total = round(sum(costs / 1000, 2))
                    average = round(total/nb,2)
                    if best_average > average:
                        best_average = average
                        best_locs = locs

            return (base_average,base_loc,best_average,best_locs)

        else:
            return None

    def pick_optimal_lists(self, GLOB, cache, count):

        with open(GLOB.output_optimals,'w',newline='') as csvfile:

            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['conf','year','orig. loc.','orig. cost', 'best loc.', 'best cost', 'saved'])
            for conf in GLOB.confs_processed:
                for year in GLOB.years_processed:
                    x = self.pick_optimal_list(GLOB, cache, conf, year, count)
                    if not x is None:
                        (base,base_loc,best,best_locs) = x
                        best_loc = ','.join([loc.place.city for loc in best_locs])
                        writer.writerow([conf,year,self.confs[conf][year].place.city,base,best_loc,best,norm(base-best)])

    # Slightly ad-hoc function computing the average total overlap that occurs when a list of conference using the same location over sliding years (see Jens' request)

    def mythical_hotel_aux(self,year,confs):

        years = [year + k for k in range(len(confs))]
        pairs = list(zip(confs,years))
        datas = [[d.id for d in self.data if d.conference == p[0] and d.year == p[1]] for p in pairs]

        if all(len(x) > 0 for x in datas):

            # Computes the number of people that went to at least two of these events
            d = {}
            for data in datas:
                for id in data:
                    if id in d:
                        d[id] = d[id] + 1
                    else:
                        d[id] = 1
            recurrent = len([x for x in d if d[x] > 1])
            recurrent2 = sum([d[x] - 1 for x in d if d[x] > 1])
            # print("From year {}: {} recurrent".format(year,recurrent))

            # Computes the size of the union of the intersection of all combinations of events
            pairs = combinations(datas,2)
            intersections = [len(set(x[0]) & set(x[1])) for x in pairs]
            total = sum(intersections)
            # print("From year {}: {} overlaps".format(year,total))
            return recurrent,recurrent2,total
        else:
            return None

    def mythical_hotel(self,GLOB):

        # Let's simply pick a year and an order and count what this overlap would have been for various historical years
        total_rec = 0
        total_rec2 = 0
        total_all = 0
        counter = 0
        for confs in permutations(GLOB.confs_processed):
            # print("Given the permutation {}, the overlap has been:".format(confs))
            local_total_rec = 0
            local_total_rec2 = 0
            local_total_all = 0
            local_counter = 0
            for year in GLOB.years_processed[:-3]:
                overlap = self.mythical_hotel_aux(year,confs)
                if not overlap is None:
                    recurrent,recurrent2,overlap = overlap
                    counter = counter + 1
                    local_counter = local_counter + 1
                    total_rec = total_rec + recurrent
                    total_rec2 = total_rec2 + recurrent2
                    total_all = total_all + overlap
                    local_total_rec = local_total_rec + recurrent
                    local_total_rec2 = local_total_rec2 + recurrent2
                    local_total_all = local_total_all + overlap
            # print("For permutation {}, the average amount of recurrent participants has been {}:".format(confs,norm(local_total_rec/local_counter)))
            # print("For permutation {}, the average overlap has been {}:".format(confs,norm(local_total_all/local_counter)))
        res_rec = norm(total_rec/counter)
        res_rec2 = norm(total_rec2/counter)
        res_all = norm(total_all/counter)
        print("On average overall, the amount of recurrent participants has been: {}".format(res_rec))
        print("On average overall, the amount of recurrent participants accounting for more than two has been: {}".format(res_rec2))
        print("On average overall, the overlap has been: {}".format(res_all))
        return res_rec,res_rec2,res_all

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
                        total_acm = round(reduce(lambda x,y: x + y.footprint, select_data, 0)/1000,2)
                        average_acm = round(total_acm/nb,2)
                        total_brighter = round(reduce(lambda x,y: x + y.cost_brighter, select_data, 0)/1000,2)
                        average_brighter = round(total_brighter/nb,2)
                        writer.writerow([name, year, conf_loc.city, nb,
                                         total_acm, average_acm,
                                         total_brighter,average_brighter])

    # Assuming the participants would not have changed, speculate the carbon cost of a conference assuming it had taken place in a different location
    def speculate_cost_at_loc(self,name,year,loc):
        select_data = [d for d in self.data if d.conference == name and d.year == year]
        nb = len(select_data)

        if nb > 0:
            costs = [d.get_footprint(GLOB, cache, loc) for d in select_data]
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
            costs = [min(d.get_cost_acm(loc1),d.get_footprint(GLOB, cache, loc2)) for d in select_data]
            total_cost = round(reduce(lambda x,y: x + y, costs, 0)/1000,2)
            average_cost = round(total_cost/len(select_data),2)

            print("{} {} would have cost {} per participant if colocated between {} and {}".format(name,year,average_cost,loc1,loc2))
            return average_cost

############# END DEPRECATED ############


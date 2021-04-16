import math
from collections import Counter
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

    def get_participants_conf(self, conf):
        return [d for d in self.data if d.conference == conf]

    def get_participants_conf_year(self, conf, year):
        return [d for d in self.data if d.conference == conf and d.year == year]

    # This routine checks for each location of each conference that the data for this location are already cached.
    # If not, it tries to compute them and cache them.
    # If it fails, it reports the likely to be erroneous data entry, and removes it from the conferences of consideration
    def preprocess_confs(self, GLOB, cache):
        logging.info("Starting the preprocessing of the locations of the events")
        buggy_inputs = []
        for name, conf in self.confs.items():
            for year, loc in conf.items():
                # print('Processing {} {}'.format(name,year))
                try:
                    cache.check_cache_loc(GLOB, loc.place)
                    cache.set_loc(GLOB, loc)
                except:
                    buggy_inputs.append((name, year))
                    print(
                        "WARNING: in the list of conference, entry {} {} at {} cannot be processed and has been ignored\n".format(
                            name, year, loc
                        )
                    )
        for name, year in buggy_inputs:
            self.confs[name].pop(year)

    def preprocess_users(self, GLOB, cache):
        logging.info("Starting the preprocessing of the participation database")
        confs = self.confs
        buggy_inputs = []
        for name, conf in confs.items():
            for year, conf_loc in conf.items():
                # print('Processing conference {} {}\n'.format(name,year))
                participants = self.get_participants_conf_year(name, year)
                for d in participants:
                    loc = d.location
                    try:
                        cache.check_cache_loc(GLOB, loc.place)
                        cache.set_loc(GLOB, loc)
                        footprint = d.get_and_set_footprint(GLOB, cache, conf_loc)
                        if footprint is None:
                            print(conf_loc)
                            raise KeyError
                    except Exception as e:
                        print(e)
                        print(
                            "WARNING: in the list of participants, entry {} cannot be processed and has been ignored\n".format(
                                d
                            )
                        )
                        buggy_inputs.append(d)
        for d in buggy_inputs:
            self.data.remove(d)

    def preprocess(self, GLOB, cache):
        self.preprocess_confs(GLOB, cache)
        self.preprocess_users(GLOB, cache)
        self.print_user_db(GLOB)

    def print_user_db(self, GLOB):
        logging.info("Writing the raw emission data at {}".format(GLOB.output_raw))
        with open(GLOB.output_raw, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "id",
                    "city",
                    "state",
                    "country",
                    "continent",
                    "conference",
                    "year",
                    "footprint",
                ]
            )
            for d in self.data:
                d.write_csv_row(writer)

    def footprint_per_conf(self, GLOB):
        with open(GLOB.footprint_confs, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "conf",
                    "year",
                    "location",
                    "nb participants",
                    "total footprint",
                    "average footprint",
                ]
            )
            for name, conf in self.confs.items():
                for year, conf_loc in conf.items():
                    select_data = [
                        d for d in self.data if d.conference == name and d.year == year
                    ]
                    for d in select_data:
                        if d.footprint is None:
                            print(d)
                            raise KeyError
                    nb = len(select_data)
                    if nb > 0:
                        total_footprint = round(
                            reduce(lambda x, y: x + y.footprint, select_data, 0) / 1000,
                            2,
                        )
                        average_footprint = round(total_footprint / nb, 2)
                        writer.writerow(
                            [
                                name,
                                year,
                                conf_loc.place.city,
                                nb,
                                total_footprint,
                                average_footprint,
                            ]
                        )

    def analysis_demographic(self, GLOB):
        output_file_main = fill_hole_string(GLOB.output_demographic, "")
        output_file_conf = fill_hole_string(GLOB.output_demographic, "_per_conf")
        output_file_delta = fill_hole_string(GLOB.output_demographic, "_delta")
        output_ParticipantsOrigin = GLOB.ParticipantsOrigin

        continents = GLOB.continents()

        init_distrib = Counter({c: 0 for c in continents + ["SAME"]})

        # Global distribution of origin
        distrib_total = init_distrib.copy()
        total_attendance = 0
        # Distribution for each origin of the conf
        distrib_per_loc = {c: init_distrib.copy() for c in continents}
        total_attendance_per_loc = init_distrib.copy()

        with open(output_file_main, "w", newline="") as csvfile_main:
            with open(output_file_conf, "w", newline="") as csvfile_conf:
                with open(output_ParticipantsOrigin, "w", newline="") as csvfile_PO:

                    writer_main = csv.writer(
                        csvfile_main, delimiter=",", quoting=csv.QUOTE_MINIMAL
                    )
                    writer_conf = csv.writer(
                        csvfile_conf, delimiter=",", quoting=csv.QUOTE_MINIMAL
                    )
                    writer_PO = csv.writer(
                        csvfile_PO, delimiter=",", quoting=csv.QUOTE_MINIMAL
                    )
                    writer_main.writerow(
                        ["Conference", "Year", "Continent"] + continents + ["Local"]
                    )
                    writer_conf.writerow(["Conference"] + continents + ["Local"])
                    writer_PO.writerow(["Conference"] + continents)

                    # For each conference
                    for name, conf in self.confs.items():
                        # Distribution for the conference 'name'
                        distrib_conf = init_distrib.copy()
                        total_attendance_conf = 0

                        output_POC = fill_hole_string(GLOB.ParticipantsOriginC, name)
                        with open(output_POC, "w", newline="") as csvfile_POC:
                            writer_POC = csv.writer(
                                csvfile_POC, delimiter=",", quoting=csv.QUOTE_MINIMAL
                            )
                            writer_POC.writerow(["Year", "Location"] + continents)
 
                            # For each instance of the conference 'name'
                            for year, conf_loc in conf.items():

                                # List of participants to 'name[year]'
                                select_data = [
                                    d
                                    for d in self.data
                                    if d.conference == name and d.year == year
                                ]
                                attendance = len(select_data)

                                # If we actually have data for this instance
                                if attendance > 0:
                                    # Distribution of this instance
                                    nb_loc = {}
                                
                                    total_attendance += attendance
                                    total_attendance_per_loc[conf_loc.continent] += attendance
                                    total_attendance_conf += attendance
                                    
                                    nb_loc = {
                                        l: len(
                                            [
                                                d
                                                for d in select_data
                                                if d.location.continent == l
                                            ]
                                        )
                                        for l in continents
                                    }
                                    nb_loc["SAME"] = len(
                                        [
                                            d
                                            for d in select_data
                                            if d.location.continent == conf_loc.continent
                                        ]
                                    )

                                    distrib_total += nb_loc
                                    distrib_per_loc[conf_loc.continent] += nb_loc
                                    distrib_conf += nb_loc

                                    main_row = [
                                        norm_perc(nb_loc[x], attendance) for x in continents
                                    ]
                                    writer_main.writerow(
                                        [name, year, conf_loc.continent]
                                        + main_row
                                        + [norm_perc(nb_loc["SAME"], attendance)]
                                    )
                                    
                                    main_row = [nb_loc[x] for x in continents]
                                    writer_POC.writerow([name+str(year), conf_loc.continent] + main_row)


                        conf_row = [
                            norm_perc(distrib_conf[x], total_attendance_conf)
                            for x in continents
                        ]
                        writer_conf.writerow(
                            [name]
                            + conf_row
                            + [norm_perc(distrib_conf["SAME"], total_attendance_conf)]
                        )
                        conf_row = [distrib_conf[x] for x in continents]
                        writer_PO.writerow(
                            [name]
                            + conf_row
                        )


                    # print("total_attendance : {}".format(total_attendance))
                    # for x in continents:
                    #     print("{} has {}".format(x,norm_perc(distrib_total[x], total_attendance)))
                       
                    writer_conf.writerow(
                        ["Any"]
                        + [
                            norm_perc(distrib_total[x], total_attendance)
                            for x in continents
                        ]
                        + [norm_perc(distrib_total["SAME"], total_attendance)]
                    )
                    writer_PO.writerow(
                        ["All"]
                        + [distrib_total[x] for x in continents]
                    )

        with open(output_file_delta, "w", newline="") as csvfile_delta:
            writer = csv.writer(csvfile_delta, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Location"] + continents + ["Local"])

            for c in continents:
                if total_attendance_per_loc[c] != 0:
                    writer.writerow(
                        [c]
                        + [
                            norm_perc(
                                distrib_per_loc[c][x], total_attendance_per_loc[c]
                            )
                            for x in continents
                        ]
                        + [
                            norm_perc(
                                distrib_per_loc[c]["SAME"], total_attendance_per_loc[c]
                            )
                        ]
                    )
            writer.writerow(
                ["Any"]
                + [norm_perc(distrib_total[x], total_attendance) for x in continents]
                + [norm_perc(distrib_total["SAME"], total_attendance)]
            )

    # Overlap of participation, in percentage, between two instances of two conferences
    def participation_overlap_single(self, name1, year1, name2, year2):

        participants1 = set(
            [d.id for d in self.data if d.conference == name1 and d.year == year1]
        )
        participants2 = set(
            [d.id for d in self.data if d.conference == name2 and d.year == year2]
        )

        if len(participants1) > 0 and len(participants2) > 0:
            intersection = participants1 & participants2
            return [len (intersection), len(participants1), len(participants2)]
            # return norm(
                # len(intersection) * 2 * 100 / (len(participants1) + len(participants2))
            # )
        else:
            return None

    # Overlap of participation, in percentage, between any two instances of a given conference
    def participation_overlap_intra_conf(self, GLOB, name):

        output_file = fill_hole_string(GLOB.output_overlap_intra_conf, "_" + name)

        with open(output_file, "w", newline="") as csvfile:

            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Year1", "Year2", "Overlap"])
            for pair in combinations(GLOB.years_processed, 2):
                overlap = self.participation_overlap_single(
                    name, pair[0], name, pair[1]
                )
                if overlap is not None:
                    writer.writerow([pair[0], pair[1]] + overlap)

    def participation_overlap_intra_conf_generate_all(self, GLOB):
        for c in GLOB.confs_processed:
            self.participation_overlap_intra_conf(GLOB, c)

    # Overlap of participation, in percentage, between two given conferences for each year
    def participation_overlap_cross_conf(self, GLOB, conf1, conf2):

        output_file = fill_hole_string(
            GLOB.output_overlap_cross_conf, "_" + conf1 + "_" + conf2
        )

        with open(output_file, "w", newline="") as csvfile:

            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Year", "Overlap", "Total1", "Total2"])
            overlap_acc = 0
            part1_acc = 0
            part2_acc = 0
            for year in GLOB.years_processed:
                overlap = self.participation_overlap_single(conf1, year, conf2, year)
                if overlap is not None:
                    overlap_acc += overlap[0]
                    part1_acc += overlap[1]
                    part2_acc += overlap[2]
                    writer.writerow([year] + overlap)

            writer.writerow(["All", overlap_acc, part1_acc, part2_acc])

    def participation_overlap_cross_conf_generate_all(self, GLOB):
        for pair in combinations(GLOB.confs_processed, 2):
            self.participation_overlap_cross_conf(GLOB, pair[0], pair[1])

    def get_number_of_participations(self, GLOB):

        with open(GLOB.output_number_of_participations, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "Conference",
                    "Avrg nb of participations",
                    "Avrg non one timer",
                    ">= 2",
                    ">= 2 per",
                    ">= 3",
                    ">= 3 per",
                    ">= 4",
                    ">= 4 per",
                    ">= 5",
                    ">= 5 per",
                ]
            )

            # res: conf |-> id_participant |-> number of participations to conf specifically
            res = {x: {} for x in GLOB.confs_processed}
            for d in self.data:
                if d.conference in GLOB.confs_processed:
                    if d.id in res[d.conference]:
                        res[d.conference][d.id] = res[d.conference][d.id] + 1
                    else:
                        res[d.conference][d.id] = 1

            aggregated = {}
            for x in res.values():
                for i,v in x.items():
                    aggregated[i] = v if not i in aggregated else v + aggregated[i]

            # We forget about the id, each conf maps to a list of number of participations
            res = {k: list(res[k].values()) for k in res}
            aggregated = [x for x in aggregated.values()]
            # print("res: {}\naggregated: {}\n".format(res,aggregated))

            # res2: conf |-> nat |-> number of unique individual having participated to nat instances of conf
            res2 = {x: {} for x in GLOB.confs_processed}
            for k in res2:
                count = 0
                i = 1
                x = res[k]
                total = len(x)
                while count < total:
                    ci = len([v for v in x if v == i])
                    count += ci
                    res2[k][i] = ci
                    i += 1

            # agg2: nat |-> number of unique individual having participated to nat instances 
            agg2 = {}
            count = 0
            i = 1
            total = len(aggregated)
            while count < total:
                ci = len([v for v in aggregated if v == i])
                count += ci
                agg2[i] = ci
                i += 1

            for c in GLOB.confs_processed:
                average = round(sum(res[c]) / len(res[c]), 2)
                res_no_one_timers = [x for x in res[c] if x > 1]
                average2 = round(sum(res_no_one_timers) / len(res_no_one_timers), 2)
                row = []
                for i in range(1, 5):
                    row = row + [len([v for v in res[c] if v > i]), norm_perc(len([v for v in res[c] if v > i]), len(res[c]))]
                
                writer.writerow([c, average, average2] + row)

            # Overall
            average = norm(sum(aggregated) / len(aggregated))
            average2 = norm(sum([x for x in aggregated if x > 1]) / len([x for x in aggregated if x > 1]))
            row = []
            for i in range(1, 5):
                row = row + [len([v for v in aggregated if v > i]), norm_perc(len([v for v in aggregated if v > i]), len(aggregated))]

            writer.writerow(["All", average, average2] + row)


        for conf in GLOB.confs_processed:

            output_file_conf = fill_hole_string(GLOB.output_number_per_conf, conf)
            with open(output_file_conf, "w", newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
                nmax = max(res2[conf])
                writer.writerow(['']+[str(i) for i in range(1,nmax + 1)])
                writer.writerow(['']+[0 if not i in res2[conf] else res2[conf][i] for i in range(1,nmax + 1)])
                        
        output_file_conf = fill_hole_string(GLOB.output_number_per_conf, "total")
        with open(output_file_conf, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            nmax = max(agg2)
            writer.writerow(['']+[str(i) for i in range(1,nmax + 1)])
            writer.writerow(['']+[0 if not i in agg2 else agg2[i] for i in range(1,nmax + 1)])

    def get_number_of_participations_per_year(self, GLOB):

        with open(GLOB.output_number_of_participations_per_year, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "Year",
                    "Avrg nb of participations",
                    "Avrg non one timer",
                    ">= 2",
                    ">= 2 per",
                    ">= 3",
                    ">= 3 per",
                    "= 4",
                    "= 4 per"
                ]
            )

            # res: year |-> id_participant |-> number of participations during year specifically
            res = {x: {} for x in GLOB.years_processed}
            for d in self.data:
                if d.year in GLOB.years_processed:
                    if d.id in res[d.year]:
                        res[d.year][d.id] = res[d.year][d.id] + 1
                    else:
                        res[d.year][d.id] = 1
            # print(res)

            aggregated = {}
            for x in res.values():
                for i,v in x.items():
                    aggregated[i] = v if not i in aggregated else v + aggregated[i]
            # print(aggregated)

            # We forget about the id, each year maps to a list of number of participations
            res = {k: list(res[k].values()) for k in res}
            aggregated = [x for x in aggregated.values()]
            # print("res: {}\naggregated: {}\n".format(res,aggregated))

            # res2: conf |-> nat |-> number of unique individual having participated to nat instances of conf
            res2 = {x: {} for x in GLOB.years_processed}
            for k in res2:
                count = 0
                i = 1
                x = res[k]
                total = len(x)
                while count < total:
                    ci = len([v for v in x if v == i])
                    count += ci
                    res2[k][i] = ci
                    i += 1

            # agg2: nat |-> number of unique individual having participated to nat instances 
            agg2 = {}
            count = 0
            i = 1
            total = len(aggregated)
            while count < total:
                ci = len([v for v in aggregated if v == i])
                count += ci
                agg2[i] = ci
                i += 1

            for c in GLOB.years_processed:
                average = round(sum(res[c]) / len(res[c]), 2)
                res_no_one_timers = [x for x in res[c] if x > 1]
                average2 = round(sum(res_no_one_timers) / len(res_no_one_timers), 2)
                row = []
                for i in range(1,4):
                    row = row + [len([v for v in res[c] if v > i]), norm_perc(len([v for v in res[c] if v > i]), len(res[c]))]
                writer.writerow([c, average, average2] + row)

            # Overall
            average = norm(sum(aggregated) / len(aggregated))
            average2 = norm(sum([x for x in aggregated if x > 1]) / len([x for x in aggregated if x > 1]))
            row = []
            for i in range(1, 4):
                row = row + [len([v for v in aggregated if v > i]), norm_perc(len([v for v in aggregated if v > i]), len(aggregated))]

            writer.writerow(["All", average, average2] + row)

    def get_old_timers(self, GLOB):

        for conf in GLOB.confs_processed:

            output_file_conf = fill_hole_string(GLOB.output_old_timer, conf)

            with open(output_file_conf, "w", newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)

                writer.writerow(["year", "old timers", "old timers per"])

                for year in GLOB.years_processed:
                    select_data = [
                        d.id
                        for d in self.data
                        if d.conference == conf and d.year == year
                    ]
                    if len(select_data) > 0:
                        select_old_data = [
                            d.id
                            for d in self.data
                            if d.conference == conf and d.year < year
                        ]
                        old_timers = [c for c in select_data if c in select_old_data]

                        res = norm_perc(len(old_timers), len(select_data))
                        writer.writerow([year, len(old_timers), res])

    def pick_optimal_list(self, GLOB, cache, count, pred):
        select_data = [d for d in self.data if pred(d.conference, d.year)]
        nb = len(select_data)
        if nb > 0:
            base_total = round(
                reduce(lambda x, y: x + y.footprint, select_data, 0) / 1000, 2
            )
            base_average = round(base_total / nb, 2)
            best_average = math.inf
            base_loc = None
            best_locs = None

            for locs in combinations(GLOB.city_candidates, count):
                locs = [Location(Place(*loc)) for loc in locs]
                costs = [
                    min([d.get_footprint(GLOB, cache, loc) for loc in locs]) / 1000
                    for d in select_data
                ]
                total = round(sum(costs, 2))
                average = round(total / nb, 2)
                if best_average > average:
                    best_average = average
                    best_locs = locs

            return base_average, base_loc, best_average, best_locs

        else:
            return None

    def pick_optimal_lists(self, GLOB, cache, count, output):
        with open(output, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [
                    "conf",
                    "year",
                    "orig. loc.",
                    "orig. footprint",
                    "best loc.",
                    "best footprint",
                    "saved",
                ]
            )
            for conf in GLOB.confs_processed:
                for year in GLOB.years_processed:
                    print("Picking optimal for {} {}".format(conf, year))
                    x = self.pick_optimal_list(
                        GLOB, cache, count, lambda c, y: y == year and c == conf
                    )
                    if x is not None:
                        (base, base_loc, best, best_locs) = x
                        best_loc = ";".join([loc.place.city for loc in best_locs])
                        writer.writerow(
                            [
                                conf,
                                year,
                                self.confs[conf][year].place.city,
                                base,
                                best_loc,
                                best,
                                norm(base - best),
                            ]
                        )

    def pick_optimal_for_set(self, GLOB, cache, count, output, confs, confs_name):
        with open(output, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["conf", "best loc.", "best footprint"])
            logging.debug(f"Picking optimal for the set {confs}")
            x = self.pick_optimal_list(GLOB, cache, count, lambda c, y: (c, y) in confs)
            if x is not None:
                (base, base_loc, best, best_locs) = x
                best_loc = ";".join([loc.place.city for loc in best_locs])
                writer.writerow([confs_name, best_loc, best])

    def pick_optimal_loc(self, GLOB, cache):
        self.pick_optimal_lists(GLOB, cache, 1, GLOB.output_optimal_loc)

    def pick_optimal_biloc(self, GLOB, cache):
        self.pick_optimal_lists(GLOB, cache, 2, GLOB.output_optimal_biloc)

    def pick_optimal_triloc(self, GLOB, cache):
        self.pick_optimal_lists(GLOB, cache, 3, GLOB.output_optimal_triloc)

    # Slightly ad-hoc function computing the average total overlap that occurs when a list of conference using the same location over sliding years (see Jens' request)

    def mythical_hotel_aux(self, year, confs):

        years = [year + k for k in range(len(confs))]
        pairs = list(zip(confs, years))
        datas = [
            [d.id for d in self.data if d.conference == p[0] and d.year == p[1]]
            for p in pairs
        ]

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

            # Computes the size of the union of the intersection of all combinations of events
            pairs = combinations(datas, 2)
            intersections = [len(set(x[0]) & set(x[1])) for x in pairs]
            total = sum(intersections)
            # print("From year {}: {} overlaps".format(year,total))
            return recurrent, recurrent2, total
        else:
            return None

    def mythical_hotel(self, GLOB):

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
                overlap = self.mythical_hotel_aux(year, confs)
                if overlap is not None:
                    recurrent, recurrent2, overlap = overlap
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
        res_rec = norm(total_rec / counter)
        res_rec2 = norm(total_rec2 / counter)
        res_all = norm(total_all / counter)
        print(
            "On average overall, the amount of recurrent participants has been: {}".format(
                res_rec
            )
        )
        print(
            "On average overall, the amount of recurrent participants accounting for more than two has been: {}".format(
                res_rec2
            )
        )
        print("On average overall, the overlap has been: {}".format(res_all))
        return res_rec, res_rec2, res_all

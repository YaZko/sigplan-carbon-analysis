from datastructure import RawData, Location, Place
from caching import Cache
from utilities import *
import csv
import logging


# Function to parse a csv file containing data about conferences of interest and their location
# The optional argument _confs_processed_ allows to restrict the set of conferences considered.
# ASSUMPTION: the names of the conferences meant to be parsed are assumed to be described by the conf_names argument
# ASSUMPTION: the layout of the file is assumed to be correctly described by the _types_ argument
def parse_confs(f_confs, types, confs_processed):
    logging.info("Parsing conference input")
    with open(f_confs) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        confs = {}
        # Skip the header. Be wary that a line will miss if columns are not named in the csv file
        next(csv_reader)
        for row in csv_reader:
            name = row[0].rstrip()
            if name in confs_processed:
                loc = get_args(row, types)
                if name in confs:
                    confs[name][int(row[1])] = Location(Place(*loc[2:]))
                else:
                    confs[name] = {int(row[1]): Location(Place(*loc[2:]))}
    return confs


# Function to parse a csv file containing data about participants of conferences
# ASSUMPTION: the csv file is assumed to contain a header.
# ASSUMPTION: the layout of the file is assumed to be correctly described by the _types_ argument
def parse_participants(file, types):
    logging.info("Parsing user data")
    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        # Skip the header. Be wary that a line will miss if columns are not named in the csv file
        next(csv_reader)
        data = [get_args(r, types) for r in csv_reader]
        # Convert the data to the RawData datastructure
        data = [RawData(*r) for r in data]
    return data


# Utility function parsing both data bases, removing buggy entries and returning the internal datastructures
def parse(GLOB):
    logging.info("Starting parsing phase")
    # Compute a dictionary that maps conferences to maps from years to locations
    data = parse_participants(GLOB.participants_path, GLOB.participants_types)
    # We dismiss entries that did not provide a city.
    # TODO: keep track of the number of such buggy data
    data = [d for d in data if not d.location.place.city is None]
    confs = parse_confs(GLOB.confs_path, GLOB.confs_types, GLOB.confs_processed)
    return data, confs

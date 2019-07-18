from datastructure import RawData, Location
import csv

def type_nil(t,s):
    if s is "":
        return None
    elif t == str:
        return s.strip()
    else:
        return t(s)

def get_args(row,types):
    return [type_nil(types[i],row[i]) for i in range(min(len(row),len(types))) if types[i] is not None]

# Function to parse a csv file containing data about conferences of interest and their location
# ASSUMPTION: the names of the conferences meant to be parsed are assumed to be described by the conf_names argument
# ASSUMPTION: the layout of the file is assumed to be correctly described by the _types_ argument
def parse_confs(f_confs,conf_names,types):
    print("Parsing conference data")
    with open(f_confs) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        confs = {}
        for row in csv_reader:
            name = row[0].rstrip()
            if name in conf_names:
                loc = get_args(row[1:],types)
                if name in confs:
                    confs[name][int(row[1])] = Location(*loc[1:])
                else:
                    confs[name] = {int(row[1]):Location(*loc[1:])}
    return confs

# Function to parse a csv file containing data about participants of conferences
# ASSUMPTION: the csv file is assumed to contain a header.
# ASSUMPTION: the layout of the file is assumed to be correctly described by the _types_ argument
def parse_users(f_users,types):
    print("Parsing user data")
    with open(f_users) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        # Skip the header. Be wary that a line will miss if columns are not named in the csv file
        next(csv_reader)
        data = [get_args(r,types) for r in csv_reader]
        # Convert the data to the RawData datastructure
        data = [RawData(*r) for r in data]
    return data

# Utility function parsing both data bases, removing buggy entries and returning the internal datastructures
def parse(f_users,user_types,f_confs,conf_names,conf_types):
    # Compute a dictionary that maps conferences to maps from years to locations
    data = parse_users(f_users,user_types)
    # We dismiss entries that did not provide a city.
    # TODO: keep track of the number of such buggy data
    data = [d for d in data if not d.location.city is None]
    confs = parse_confs(f_confs,conf_names,conf_types)
    return data,confs


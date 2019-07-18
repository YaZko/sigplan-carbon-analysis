import parser
from datastructure import *
from data_processing import *
from co2_cost import CO2_calc
import os
from parameters import *

# Check if the chosen target files for the databases exists.
# If not, parses the raw source and output them with the right format in the target files.
def initialize_user_db(raw_users_path, raw_user_types, users_path, user_types,
                       raw_confs_path, confs_path, conf_names, raw_conf_types):
    print("Checking for existing db")
    exists_db_users = os.path.isfile(users_path)
    exists_db_confs = os.path.isfile(confs_path)
    if not exists_db_users or not exists_db_confs:
        print("Found no db, initializing")
        users,confs = parser.parse(raw_users_path, raw_user_types,
                                   raw_confs_path, conf_names, raw_conf_types)
        db = DB(users,confs)
        if not exists_db_users:
            print('Initialized the user database.')
            db.print_user_db(users_path)
        if not exists_db_confs:
            print('Initialized the conference database.')
            db.print_conf_db(confs_path)
    else:
        print("Found existing db, skipping initialization")

initialize_user_db(raw_users_path, raw_user_types, users_path, raw_user_types,
                   raw_confs_path, confs_path, conf_names, raw_conf_types)

data,confs = parser.parse(users_path, user_types, confs_path, conf_names, conf_types)
db = DB(data,confs)
db.preprocess(users_path,confs_path)
# db.analysis_demographic(output_demographic)

# db.get_number_of_participations(output_number_of_participations,conf_names)
# db.get_old_timers(output_old_timer,conf_names,conf_years)
db.pick_optimals(output_optimals,conf_names,conf_years,city_candidates)

# print(db.speculate_cost_at_loc("POPL",18,Location("Anchorage","AK","USA")))
# print(db.speculate_cost_at_loc("POPL",18,Location("Los Angeles","CA","USA")))

# db.participation_overlap_conf_generate_all(output_overlap_cross_conf,conf_names,conf_years)
# db.participation_overlap_year_generate_all(output_overlap_cross_year,conf_names,conf_years)

# db.participation_overlap_conf("POPL", )

# dest = Location("Paris",None,"France")
# for i in range(9,19):
#     db.speculate_cost_at_loc("POPL",i,dest)
#     db.speculate_cost_split("POPL",i,dest)

# db.analysis(output_path)


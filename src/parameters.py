## This file should contains all global parameters manipulated by the analysis
## They should only be used in `main.py`, all methods being parameterized by these arguments

#1 Range of years to be considered
conf_years = range(9,19)
## List of names of the conferences to be considered
conf_names = ['ICFP','POPL','PLDI','SPLASH']

city_candidates = [("Paris",None,"France"),
                   ("Edinburgh",None,"UK"),
                   ("Boston","MA","USA"),
                   ("Los Angeles","CA","USA"),
                   ("Vancouver","BC","Canada"),
                   ("Tokyo",None,"Japan"),
                   ("Beijing",None,"China"),
                   ("Mumbai",None,"India")]

## Nature of the fields of interest in the csv files intended to be read
## Used to guide the parser when building the internal data structures
## Use `None` to ignore a field
raw_user_types = [int,str,str,str,str,int,None,None]
user_types = [int,str,str,str,str,int,str,str,float,float,str,str]
raw_conf_types = [int,str,str,str]
conf_types = [int,str,str,str,str,str,str,str]


## (Relative) Paths to the (read only) raw data provided by the ACM
# For attendees
raw_users_path = '../data/SIGPLANcarbonAnon25Oct.csv'
# For conferences
raw_confs_path = '../data/SIGPLAN.CarbonDataMap.csv'

## (Relative) Paths to the databases, i.e. the raw data preprocessed with all
## secondary attributes for the DB class
# For attendees
users_path     = '../data/data_preprocessed.csv'
# For conferences
confs_path     = '../data/confs_preprocessed.csv'

## (Relative) Paths to the aggregated data resulting from the analyses
## conducted over the preprocessed database
# Mean emission
output_path             = '../output/output.csv'
# Demographic per edition
output_demographic      = '../output/demographic.csv'
# Overlap in attendance
output_overlap_cross_conf = '../output/overlap_cross_conf#.csv'
output_overlap_cross_year = '../output/overlap_cross_year#.csv'
output_old_timer = '../output/old_timer_#.csv'
output_number_of_participations = '../output/number_of_participations.csv'
output_optimals = '../output/optimals.csv'


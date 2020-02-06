## This file should contains all global parameters manipulated by the analysis
## They should only be used in `main.py`, all methods being parameterized by these arguments

class Globals:

    def __init__(self,input_events,input_participants,output_folder):

        ## Nature of the fields of interest in the csv files intended to be read
        ## Used to guide the parser when building the internal data structures
        self.participants_types = [int,str,str,str,str,int]
        self.confs_types = [str,int,str,str,str]

        ### Relative paths to the various input and output files

        ## Input files
        # Read only input data for events/conferences
        self.confs_path = '../input/' + input_events + '.csv'
        # Read only input data for attendees
        self.participants_path = '../input/' + input_participants + '.csv'

        # TODO: get those from the input by default, with option to pick a subset
        # self.confs_processed = ['GECCO']
        self.confs_processed = ['ICFP','POPL','PLDI','SPLASH']

        # TODO: get those from the input by default, with option to pick as subset
        # Range of years to be considered
        self.years_processed = range(9,19)
        # self.years_processed = range(2007,2020)

        # Cache for locations
        self.cache = '../input/.location_cache.csv'

        # Database of airports
        self.airports = '../input/airports.json'

        ## Output files
        self.output_prefix                   = '../output/' + output_folder + '/'
        # Raw emissions per participant
        self.output_raw                      = self.output_prefix + 'emission_raw.csv'
        # Footprint per conference
        self.footprint_confs                 = self.output_prefix + 'footprint_confs.csv'
         # Demographic per edition
        self.output_demographic              = self.output_prefix + 'demographic#.csv'
        # Overlap in attendance
        self.output_overlap_intra_conf       = self.output_prefix + 'overlap_intra_conf#.csv'
        self.output_overlap_cross_conf       = self.output_prefix + 'overlap_cross_conf#.csv'
        self.output_number_of_participations = self.output_prefix + 'number_of_participations.csv'
        self.output_old_timer                = self.output_prefix + 'old_timer_#.csv'
        self.output_optimal_loc              = self.output_prefix + 'optimal_loc.csv'
        self.output_optimal_biloc            = self.output_prefix + 'optimal_biloc.csv'
        self.output_optimal_triloc           = self.output_prefix + 'optimal_triloc.csv'

        # Default model to compute the footprint of travels
        self.model = 'acm'

        # Greenhouse gases have various impact depending on the altitude there are released at.
        # The radiative factor index account for this effect in the case of avionic.
        # The value can be changed to k with the '--radiative k' option, and deactivated (i.e. set to 1)
        # with the '--no-radiative' option
        self.radiative_factor_index = 1.891

        # Flag to set whether participants are uniquely identified, and hence if participation overlap can be computed
        self.unique_id = True

        ## List of names of the conferences to be considered when looking for a rough retroactive optimal
        self.city_candidates = [("Paris",None,"France"),
                                ("Edinburgh",None,"UK"),
                                ("Philadelphia","PA","USA"),
                                ("Boston","MA","USA"),
                                ("Los Angeles","CA","USA"),
                                ("Vancouver","BC","Canada"),
                                ("Tokyo",None,"Japan"),
                                ("Beijing",None,"China"),
                                ("Mumbai",None,"India")]


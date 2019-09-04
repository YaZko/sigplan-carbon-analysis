DEPENDENCIES:
  This script runs with Python 3.
  It relies on the following dependencies: `pycountry`, `pycountry-convert`, and `geopy`.
  The deprecated but functional `co2_cost` module depends additionally on `request`.
  All dependencies are available on pip.

NOTE TODO:
     * Despite having facilities to compute the closest airport to a location,
       we actually compute the carbon cost based on the distance between both
       original locations rather than the locations of both airports.
       This may be arguable.
     * Migration toward logging facilities should be completed.
     * The set of years and conferences analyzed should be computed from source,
       it's currently hard-wired in 'parameters.py'

Note: When describing classes, fields annotated as _Primary_ are assumed to be
      provided explicitely t othe constructor while fields annotated as _Secondary_
      are computed by internal methods.

main:
  Entry point of the script.

datastructure:
  Contains the main datastructures manipulated by the analysis:
  - Place: Data caracterizing a location as provided by the user. Contains the following fields:
    * City (Primary)
    * State (Primary, optional)
    * Country (Primary)
  - Location: Data caracterizing a fully specified location. Contains the following fields:
    * Place (Primary)
    * Country iso (Secondary)
    * Continent (Secondary)
    * gps location (Secondary)
    * closest airport (Secondary)
  - RawData: Data associated to a single participation at a single conference.
    Contains the following fields:
    * Unique hash id of the participant (Primary)
    * Location of the participant (Primary)
    * Conference (Primary)
    * Year (Primary)
    * Carbon cost based on the selected methodology (Secondary)

data_processing:
  Contains a structure of the internal representation of the dataset being analyzed:
  DB: Data containing both a mapping conferences to locations and a list of RawData.
  Contains the following fields
    * data (Primary)
    * confs (Primary)
  All analyzes are defined as methods over DB and write their output in the '../output/' folder 

parser:
  Functions to parse the current databases, stored as csv files.
  The layout of the database is assumed to be provided through typing arguments.

parameters:
  Global parameters used by the analysis.
  Those are setup during the initialization phase of the main, and are read-only from then on.

caching:
  Computing information such as the GPS of a location are time consuming since
  it relies on online APIs.
  The Cache class therefore handles the caching of those results.

co2_cost:
  Estimation of the carbon cost of a flight based on the brighterplanet api.
  DEPRECATED 


DEPENDENCIES:
  This script runs with Python 3. It relies on the following dependencies: `pycountry`, `pycountry-convert`, and `geopy`. The deprecated but functional `co2_cost` modul depends additionally on `request`.
  All dependencies are available on pip.

NOTE TODO:
     Just realized I compute the carbon cost based on the distance between both locations rather than the location of both airports. To be fixed.

Note: When describing classes, fields annotated as _Primary_ are assumed to be
      provided explicitely t othe constructor while fields annotated as _Secondary_
      are computed by internal methods.

main:
  Entry point of the script.

datastructure:
  Contain the core of the analysis. In particular defines two classes:
  - Location: Data caracterizing a location. Contains the following fields:
    * City (Primary)
    * State (Primary, optional)
    * Country (Primary)
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
    * Carbon cost based on the acm methodology (Secondary)
    * Carbon cost based on the brightierplanet api (Secondary, deprecated)
  - DB: Data containing both a mapping conferences to locations and a list of RawData
    Contains the following fields
    * data (Primary)
    * confs (Primary)
 
parser:
  Functions to parse the current databases, stored as csv files.
  The layout of the database is assumed to be provided through typing arguments.

parameter:
  Global parameters used by the analysis.

co2_cost:
  Estimation of the carbon cost of a flight based on the brighterplanet api.
  Functional, but deprecated at the moment.


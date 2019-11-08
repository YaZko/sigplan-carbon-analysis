This project aims to:
1) estimate the carbon cost induced by travel to conferences;
2) perform a sequence of analyses related to the geographical distribution of
the participants and other patterns of participation to help organizers to take
this issue into account.

We applied in particular the tool to the SIGPLAN set of conferences (POPL, PLDI, ICFP, SPLASH)
and describes this experiment and its conclusions in an ongoing draft.

The Python script used to perform the analysis is however meant to be as general as possible.
We would love to see other groups perform similar analyses.
As such, we welcome all feature requests, issues and pull requests. 
A brief overview of the script can be found in [Readme_script](./src/Readme.txt).
A fairly detailed step by step use of the script can be found in [tutorial](./documentation/tutorial.org).
More documentation to come.

############### Dependencies ###############

This project uses Python3. It relies on the `pycountry`, `pycontry-convert`, `request` and `geopy`
libraries, all available through pip.

############### Structure ###############

## input
   Contains the cached db and locations as well as the db of airports.
   The data to be analyzed must be stored there as well.

## output
   Contains all computed data to be exploited in folders per analysis ran.

## src
   Source code of the Python script.

## paper
   TeX source for the paper describing the analysis of the SIGPLAN conferences.


import datastructure
import requests
import json

# Requests to the http://impact.brighterplanet.com API
# Takes airports as input, we need another db to map cities to airports


class CO2_calc:
    def __init__(self, origin_airport, destination_airport):
        self.verb = 'POST'
        self.url = 'impact.brighterplanet.com/'
        self.model = 'flights'
        self.ext = 'json'
        self.payload = {
            'key': 'cc0e0342-a6ff-4833-98ce-bbac42dcace1',
            'trips': 2,
            'origin_airport': origin_airport,
            'destination_airport': destination_airport
        }

    def build_url(self):
        return 'http://' + self.url + self.model + '.' + self.ext

    def request(self):
        return requests.post(self.build_url(), data=self.payload).json()

    def get_carbon_cost(self):
        r = self.request()
        c = r['decisions']['carbon']['description'].split(' ')[0]
        return float(c)

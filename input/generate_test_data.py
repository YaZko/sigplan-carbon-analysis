import random

cities = [
    "Paris,,France",
    "Boston,MA,USA",
    "Tokyo,,Japan",
    "Philadelphia, PA, USA",
    "Seattle, WA, USA",
    "Oxford,,United Kingdom",
    "Rome,, Italy",
    "Sydney,,Australia",
    "Aarhus,,Denmark",
]


def generate_people():
    with open("participants.csv", "w") as f:
        print("participant,city,state,country,year", file=f)
        for i in range(1, 2500):
            for y in range(9, 18):
                for conf in ["POPL", "ICFP", "PLDI", "SPLASH"]:
                    if random.random() > 0.8:
                        loc = random.choice(cities)
                        print(f"{i}, {loc},{conf},{y}", file=f)


def generate_confs():
    with open("conferences.csv", "w") as f:
        print("conference,year,city,state,country", file=f)
        i = 0
        for y in range(9, 18):
            for conf in ["POPL", "ICFP", "PLDI", "SPLASH"]:
                loc = random.choice(cities)
                print(f"{conf}, {y}, {loc}", file=f)


generate_people()
generate_confs()

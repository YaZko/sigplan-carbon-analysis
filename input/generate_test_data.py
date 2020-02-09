def generate_people():
    with open("participants.csv", "w") as f:
        print("headers...", file=f)
        for i in range(1, 500):
            for y in range(9, 18):
                for conf in ["POPL", "ICFP", "PLDI", "SPLASH"]:
                    if i % 3 == 0:
                        loc = "Paris,,France"
                    elif i % 3 == 1:
                        loc = "Boston,MA,USA"
                    else:
                        loc = "Tokyo,,Japan"
                    print(f"{i}, {loc},{conf},{y}", file=f)


def generate_confs():
    with open("conferences.csv", "w") as f:
        print("headers...", file=f)
        i = 0
        for y in range(9, 18):
            for conf in ["POPL", "ICFP", "PLDI", "SPLASH"]:
                i += 1
                if i % 3 == 0:
                    loc = "Paris,,France"
                elif i % 3 == 1:
                    loc = "Boston,MA,USA"
                else:
                    loc = "Tokyo,,Japan"
                print(f"{conf}, {y}, {loc}", file=f)


generate_people()
generate_confs()

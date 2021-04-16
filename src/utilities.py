# Utility to generate names of files Assuming that `name` is a string
# containing a hole encoded as a '#' caracter, fill the hole with the string `arg`
def fill_hole_string(name, arg):
    ctx = name.split("#")
    if len(ctx) < 2:
        raise Exception("{} contains no hole".format(name))
    elif len(ctx) > 2:
        raise Exception("{} contains more than one hole".format(name))
    else:
        return ctx[0] + arg + ctx[1]


def norm(v):
    return round(v, 2)


def norm_perc(v, tot):
    return round(v / tot * 100, 1)

def norm_perc_int(v, tot):
    return round(v / tot * 100)

def type_nil(t, s):
    if s == "":
        return None
    elif t == str:
        return s.strip()
    else:
        return t(s)


def get_args(row, types):
    return [
        type_nil(types[i], row[i])
        for i in range(min(len(row), len(types)))
        if types[i] is not None
    ]


def string_to_double(s):
    x, y = s.split(",")
    return float(x.split("(")[1].strip()), float(y.split(")")[0].strip())


# def export_to_tex(path):

#     head1 = """
# \begin{figure}
# \begin{tabular}{|l|l|c|c|c|}
#   \hline%
# """
#   \bfseries event & \bfseries location & \bfseries nb. participants & \bfseries total cost & \bfseries average cost

# """
# \csvreader[head to column names]{../output/output.csv}{}%
# {\\\conf\ \year & \location & \csvcoliv & \csvcolv & \csvcolvi}%
# \\\hline
# \end{tabular}
# \caption{For each \event: location, number of participants and carbon cost, total and average per participant, in \gazunitbis,}
# \label{fig:RawData}
# \end{figure}
# """

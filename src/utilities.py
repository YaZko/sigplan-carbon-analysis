# Utility to generate names of files Assuming that `name` is a string
# containing a hole encoded as a '#' caracter, fill the hole with the string `arg`
def fill_hole_string(name,arg):
    ctx = name.split("#")
    if len(ctx) < 2:
        raise Exception('{} contains no hole'.format(name))
    elif len(ctx) > 2:
        raise Exception('{} contains more than one hole'.format(name))
    else:
        return ctx[0] + arg + ctx[1]

def norm(v):
    return round(v,2)
def norm_perc(v,tot):
    return round(v/tot*100,2)

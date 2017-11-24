from pprint import pprint


def disp(x):
    if hasattr(x, '__dict__'):
        x = vars(x)
    pprint(x)

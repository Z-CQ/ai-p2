
asciis = {
    "red": "\33[0;31m",
    "yellow": "\33[0;33m",
    "green": "\33[0;32m",
    "blue": "\33[0;34m",
    "reset": "\33[0m"
}

def warn_print(msg, last="\n"):
    print("{0}[WARNING]{1}".format(asciis["yellow"], asciis["reset"]), msg, end=last)

def err_print(msg, last="\n"):
    print("{0}[ERR]{1}".format(asciis["red"], asciis["reset"]), msg, end=last)

def ok_print(msg, last="\n"):
    print("{0}[OK]{1}".format(asciis["green"], asciis["reset"]), msg, end=last)

def get_input(msg) -> str:
    return input("{0}[INPUT]{1} {2}".format(asciis["blue"], asciis["reset"], msg))
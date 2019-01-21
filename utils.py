import datetime as dt
import time

from config import TIMESTAMP_FORMAT, API_HOSTNAME


def convert_env_format(env):
    res = []
    for var, value in env.items():
        res.append("{}={}".format(var, value))
    return res


def get_time():
    return dt.datetime.fromtimestamp(time.time()).strftime(TIMESTAMP_FORMAT)


def get_url(endpoint):
    return "https://{}{}".format(API_HOSTNAME, endpoint)


def print_usage():
    print("Wrong number of arguments provided. Usage:\n\tpython grader.py <cluster token>")

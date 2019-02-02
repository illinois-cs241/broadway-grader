import asyncio
import logging
import os
import signal
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from logging.handlers import TimedRotatingFileHandler

import requests
from chainlink import Chainlink

import api_keys as api_key
from config import *

import argparse

# globals
worker_id = None
worker_thread = None
heartbeat_running = True
worker_running = True
event_loop = asyncio.new_event_loop()

api_host = None
api_port = None
use_https = False

# setting up logger
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    handlers=[
        TimedRotatingFileHandler('{}/log'.format(LOGS_DIR), when='midnight', backupCount=7),
        logging.StreamHandler()
    ],
    level=logging.INFO
)
logger = logging.getLogger()


def get_url(endpoint):
    return "{}://{}:{}{}".format("https" if use_https else "http", api_host, api_port, endpoint)


def signal_handler(sig, frame):
    global worker_running
    worker_running = False


def heartbeat_routine():
    while heartbeat_running:
        response = requests.post(get_url("{}/{}".format(HEARTBEAT_ENDPOINT, worker_id)), headers=header, data='')
        if response.status_code != SUCCESS_CODE:
            logger.critical("Heartbeat failed!\nError: {}".format(response.text))
            return

        time.sleep(HEARTBEAT_INTERVAL)


def worker_routine():
    asyncio.set_event_loop(event_loop)

    while worker_running:
        # poll from queue
        response = requests.get(get_url("{}/{}".format(GRADING_JOB_ENDPOINT, worker_id)), headers=header)

        # if the queue is empty then sleep for a while
        if response.status_code == QUEUE_EMPTY_CODE:
            time.sleep(JOB_POLL_INTERVAL)
            continue

        if response.status_code != SUCCESS_CODE:
            logger.critical("Bad server response while trying to poll job.\nError: {}".format(response.text))
            return

        # we successfully polled a job
        job = response.json()["data"]
        job_id = job.get(api_key.GRADING_JOB_ID)
        logger.info("Starting job {}".format(job_id))

        # execute job
        try:
            chain = Chainlink(job[api_key.STAGES], workdir="/tmp")
            job_results = chain.run({})
        except Exception as ex:
            logger.critical("Grading job failed with exception:\n{}", ex)
            job_results = [
                {"logs": {"stdout": b"The container crashed", "stderr": bytes(str(ex), "utf-8")}, "success": False}
            ]

        job_stdout = "\n".join([r["logs"]["stdout"].decode("utf-8") for r in job_results])
        job_stderr = "\n".join([r["logs"]["stderr"].decode("utf-8") for r in job_results])

        # remove logs from result array because logs can be bulky we will store then separately
        for r in job_results:
            del r["logs"]

        logger.info("Finished job {}".format(job_id))
        if VERBOSE:
            logger.info("Job stdout:\n" + job_stdout)
            logger.info("Job stderr:\n" + job_stderr)

        grading_job_result = {api_key.RESULTS: job_results, api_key.SUCCESS: job_results[-1]["success"],
                              api_key.LOGS: {'stdout': job_stdout, 'stderr': job_stderr},
                              api_key.GRADING_JOB_ID: job_id}

        logger.info("Sending job results")
        response = requests.post(get_url("{}/{}".format(GRADING_JOB_ENDPOINT, worker_id)), json=grading_job_result,
                                 headers=header)
        if response.status_code != SUCCESS_CODE:
            logger.critical("Bad server response while updating about job status.\nError: {}".format(response.text))
            return


def register_node():
    global worker_id
    global worker_running
    global heartbeat_running

    response = requests.get(get_url("{}/{}".format(GRADER_REGISTER_ENDPOINT, socket.gethostname())), headers=header)
    if response.status_code != SUCCESS_CODE:
        logger.critical("Registration failed!\nError: {}".format(response.text))
        worker_running = False
        heartbeat_running = False
        exit(-1)

    logger.info("Registered to server")
    server_response = response.json()["data"]
    # read worker id
    if api_key.WORKER_ID in server_response:
        worker_id = server_response.get(api_key.WORKER_ID)
    else:
        logger.critical("Bad server response on registration. Missing argument \'{}\'.".format(api_key.WORKER_ID))
        worker_running = False
        heartbeat_running = False
        exit(-1)


def print_usage():
    print("Wrong number of arguments provided. Usage:\n\tpython grader.py <api host> <api port> <cluster token>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Broadway grader")

    parser.add_argument("api_host", help="API node host")
    parser.add_argument("api_port", help="API node port")
    parser.add_argument("token", help="Cluster token")

    parser.add_argument("--use-https", action="store_const", const=True, default=False, help="Use https")

    args = parser.parse_args()

    api_host = args.api_host
    api_port = args.api_port
    token = args.token
    use_https = args.use_https

    signal.signal(signal.SIGINT, signal_handler)

    # register node to server
    header = {api_key.AUTH: "Bearer {}".format(token)}
    register_node()

    # run the grader on two separate threads. If any of the routines fail, the grader shuts down
    executor = ThreadPoolExecutor(max_workers=2)
    futures = [executor.submit(heartbeat_routine), executor.submit(worker_routine)]
    wait(futures, return_when=FIRST_COMPLETED)
    worker_running = False
    heartbeat_running = False
    executor.shutdown()

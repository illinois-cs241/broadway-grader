import os
import json
import socket
import asyncio
import logging
import argparse
import websockets

from jsonschema import validate
from chainlink import Chainlink

import grader.api_keys as api_keys

from config import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

grading_job_def = {
    "type": "object",
    "properties": {
        api_keys.GRADING_JOB_ID: {"type": "string"},
        api_keys.STAGES: {"type": "array"},
    },
    "required": [api_keys.GRADING_JOB_ID, api_keys.STAGES],
    "additionalProperties": False,
}


async def run(token, worker_id):
    url = "{}://{}:{}{}{}/{}".format(
        "wss" if USE_SSL else "ws",
        API_HOSTNAME, API_PORT,
        API_PROXY, WORKER_WS_ENDPOINT,
        worker_id,
    )

    headers = {api_keys.AUTH: "Bearer {}".format(token)}
    hostname = socket.gethostname()

    async with websockets.connect(url, extra_headers=headers) as ws:
        await ws.send(json.dumps({
            "type": "register",
            "args": {"hostname": hostname},
        }))

        # poll job
        try:
            while True:
                job = json.loads(await ws.recv())

                validate(instance=job, schema=grading_job_def)

                job_id = job[api_keys.GRADING_JOB_ID]
                stages = job[api_keys.STAGES]

                logger.info("starting job {}".format(job_id))

                # execute job
                try:
                    chain = Chainlink(stages, workdir=os.getcwd())
                    job_results = await chain.run({})
                except Exception as ex:
                    logger.critical("grading job failed with exception:\n{}", ex)
                    job_results = [
                        {
                            "logs": {
                                "stdout": b"the container crashed",
                                "stderr": bytes(str(ex), "utf-8"),
                            },
                            "success": False,
                        }
                    ]

                job_stdout = "\n".join(
                    [r["logs"]["stdout"].decode("utf-8") for r in job_results]
                )
                job_stderr = "\n".join(
                    [r["logs"]["stderr"].decode("utf-8") for r in job_results]
                )

                for r in job_results:
                    del r["logs"]

                logger.info("finished job {}".format(job_id))

                logger.info("job stdout:\n" + job_stdout)
                logger.info("job stderr:\n" + job_stderr)

                job_result = {
                    api_keys.RESULTS: job_results,
                    api_keys.SUCCESS: job_results[-1]["success"],
                    api_keys.LOGS: {"stdout": job_stdout, "stderr": job_stderr},
                    api_keys.GRADING_JOB_ID: job_id,
                }

                await ws.send(json.dumps({
                    "type": "job_result",
                    "args": job_result,
                }))

        except websockets.ConnectionClosed as e:
            logger.critical("connection closed", e.code, e.reason)

        except Exception as e:
            logger.critical("failed to pull job: {}".format(repr(e)))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="Broadway cluster token")
    parser.add_argument("worker_id", metavar="worker-id", help="Unique worker id for registration")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.get_event_loop().run_until_complete(run(args.token, args.worker_id))

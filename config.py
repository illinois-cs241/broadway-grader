# Either IP Address or Hostname of the api to connect to
API_HOSTNAME = "127.0.0.1"

# Port of the running api
API_PORT = 1470

# TODO: Describe proxy
API_PROXY = ""

# Directory where logs are stored
LOGS_DIR = "logs"

# Enables additional logging out
VERBOSE = True

# Format of the timestamp in the logs
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# HTTP Success code for below endpoints
SUCCESS_CODE = 200

# HTTP Code signfying the queue of jobs is empty
QUEUE_EMPTY_CODE = 498

# Number of seconds in between each heartbeat
HEARTBEAT_INTERVAL = 10

# Number of seqonds to way before checking for a new job
JOB_POLL_INTERVAL = 5

# API endpoints
HEARTBEAT_ENDPOINT = "/api/v1/heartbeat"
GRADING_JOB_ENDPOINT = "/api/v1/grading_job"
GRADER_REGISTER_ENDPOINT = "/api/v1/worker_register"


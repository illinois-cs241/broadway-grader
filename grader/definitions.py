import grader.api_keys as api_keys

GRADING_JOB_DEF = {
    "type": "object",
    "properties": {
        api_keys.GRADING_JOB_ID: {"type": "string"},
        api_keys.STAGES: {"type": "array"},
    },
    "required": [api_keys.GRADING_JOB_ID, api_keys.STAGES],
    "additionalProperties": False,
}

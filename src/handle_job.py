import docker
import logging
import json
import os
import tempfile

def validate_envs(job_config):
    # Filter all invalid global envs
    global_env = job_config.get('env', [])
    name_to_env = dict()
    for env in global_env:
        if env.count('=') != 2:
            logging.info("Rejecting {}".format(env))
        else:
            logging.info("Adding {}".format(env))
            global_env.append(env_process)
            name = env.split('=')[0]
            name_to_env[name] = env
    return name_to_env


def run_pipeline(client, tmpdirname, job_config):
    name_to_env = validate_envs(job_config)

    if 'students' in job_config:
        with open(os.path.join(tmpdirname, 'roster.json')) as f:
            f.write(json.dumps(job_config['students']))

    results = []
    for stage in job_config['stages']:
        stage_env = []
        for raw_stage_env in stage.get('env', []):
            components = raw_stage_env.split('=')
            if len(components) == 1 and components[0] in name_to_env:
                global_resolve = name_to_env[components[0]]
                logging.info("Resolving to global '{}'".format(global_resolve))
                stage_env.append(global_resolve)
            elif len(components) == 2:
                logging.info("Using stage specific variable '{}'".format(raw_stage_env))
                stage_env.append(raw_stage_env)

        opts = dict(
        )
        stage_results = run_container(client, stage, opts)
        results.append(stage_results)
    return results


def run_container(client, stage, opts):
    return client.containers.run(stage['image'], **opts)


def run_job(job_config):
    client = docker.from_env()
    images = map(job_config, lambda stage: stage['image'])
    for image in images:
        logging.info('Pulling image {}'.format(image))
        client.images.pull(images)

    with tempfile.TemporaryDirectory() as tmpdirname:
        logging.info("Running in temporary directory {}".format(tmpdirname))
        run_pipeline(client, tmpdirname, job_config)

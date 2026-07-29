#! /usr/bin/python3
"""
# RUM Administration Tool

# Disclaimer:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.
    This script is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY.

# Copyright:
    2026 Massimo Fares, INGV - Italy <massimo.fares@ingv.it>; EIDA Italia Team, INGV - Italy  <adaisacd.ont@ingv.it>

# License:
    GPLv3

# Platform:
    Linux

# Author:
    Massimo Fares, INGV - Italy <massimo.fares@ingv.it>
"""
"""
RUM Administration Tool

This utility orchestrates administrative operations on a RUM cluster.

Responsibilities:

- configure the execution Context
- manage worker containers
- execute operational workflows (e.g. insert, update)

"""

import os
import shutil
import subprocess
import argparse
import yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DISTRIBUTOR = BASE_DIR / "sds_distributor" / "distributor.py"

WORKFLOW_OPERATIONS = frozenset({
    "insert",
    "update",
})

#
# Parse arguments
#
parser = argparse.ArgumentParser(
    description="RUM Administration Tool"
)

parser.add_argument("--cmd", default=None)
parser.add_argument("--workers", default="2")
parser.add_argument("--prefix", default="rum-curation")
parser.add_argument("--context", default="default")
parser.add_argument("--operation", default=None)

args = parser.parse_args()

cmd = args.cmd
operation = args.operation
context = args.context
prefix = args.prefix
coworkers_number = int(args.workers) + 1

#
# At least one action is required
#
if cmd is None and operation is None:
    parser.error("Specify either --cmd or --operation.")

#
# Administrative operations own their workflow
#
if operation in WORKFLOW_OPERATIONS:

    cmd = "docker restart"

    if context == "default":
        raise Exception(
            f"Operation '{operation}' requires an explicit execution Context."
        )

#
# Default prefixes
#
docker_prefix = prefix + "-" if prefix else ""

# environment
# log_location = '/opt/gitwork/curation/rum_framework/log/'
# checkin_location = '/data/test-archive/checkin/'
compose_location = '/opt/gitwork/curation/curation_project/compose-dir/'
context_location = "/opt/gitwork/curation/curation_project/contexts/"

current_context = (
    os.path.join(context_location, "context-default.yaml")
    if context == "default"
    else os.path.join(context_location, f"context-{context}.yaml")
)


this_context = None
this_config = None
CONFIGURATOR = None

if operation in WORKFLOW_OPERATIONS:

    if not os.path.isfile(current_context):
        raise FileNotFoundError(current_context)

    CONFIGURATOR = (
        BASE_DIR /
        "sds_distributor" /
        f"config-{operation}.yaml"
    )

    if not CONFIGURATOR.is_file():
        raise FileNotFoundError(CONFIGURATOR)

    with open(current_context) as fp:
        this_context = yaml.safe_load(fp)

    with open(CONFIGURATOR) as fp:
        this_config = yaml.safe_load(fp)

    #
    # distributor decides worker prefix
    #
    prefix = this_config["workers"]["container_prefix"]
    docker_prefix = prefix + "-" if prefix else ""

    shutil.copy(
        current_context,
        os.path.join(context_location, "context.yaml")
    )

    print(f"Execution Context : {current_context}")
    print(f"Distributor Config: {CONFIGURATOR}")

# repeater (n coworker)
for i in range(1,coworkers_number):
    print(i)

    # clean logs
    #bashCommand = "echo -n \"\" > "+log_location+str(i)+"/rum_checkin.log"

    # clean checkin - not used
    # bashCommand = "rm -v '"+checkin_location+str(i)+"/*'"

    # start all containers
    if cmd == 'docker start':
        bashCommand = "docker start " + docker_prefix + str(i)

    # restart all containers
    elif cmd == 'docker restart':
        bashCommand = "docker restart "+docker_prefix+str(i)

    # stop all containers
    elif cmd == 'docker stop':
        bashCommand = "docker stop "+docker_prefix+str(i)

    # remove all containers
    elif cmd == 'docker rm':
        bashCommand = "docker rm "+docker_prefix+str(i)

    # compose up all containers
    elif cmd == 'compose up':
        bashCommand = "docker-compose -p "+prefix+""+str(i)+"  -f "+compose_location+"docker-compose."+str(i)+".yaml up -d"
        
    # compose down all containers
    elif cmd == 'compose down':
        bashCommand = "docker-compose -p "+prefix+""+str(i)+"  -f "+compose_location+"docker-compose."+str(i)+".yaml down"
        
    print(bashCommand)

    # optional way (only few cases)
    # process = subprocess.Popen(bashCommand.split(), shell=True, stdout=subprocess.PIPE)
    
    process = subprocess.run(bashCommand.split(), check=True)

    print("Workers setting Done. \n")

##
# Administrative Operations
#
if operation is not None and operation not in WORKFLOW_OPERATIONS:
    parser.error(
        f"Unknown operation '{operation}'. "
        f"Valid operations: {', '.join(sorted(WORKFLOW_OPERATIONS))}"
    )

elif operation in WORKFLOW_OPERATIONS:

    print("Launching SDS Distributor...")

    command = [
        "python3",
        str(DISTRIBUTOR),
        "--year", "all",
        "--jday", "all",
        "--sds-root", this_context["REQUEST"]["SDS_ROOT"],
        "--config", str(CONFIGURATOR)
    ]

    print(f"Operation : {operation}")
    print(f"Context   : {current_context}")
    print(f"Config    : {CONFIGURATOR}")
    print("Executing:", " ".join(command))

    subprocess.run(
        command,
        check=True
    )

print("Operation Done. \n")

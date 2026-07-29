#!/usr/bin/env python3
"""
policy-explain.py

RUM Policy Explain Utility

Reads a Policy, follows the referenced Rules and Action
Configurations and produces a human-readable description
of the effective execution model.

Version 0.1
"""

import os
import argparse
import yaml
from copy import deepcopy


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POLICY_DIR = os.path.join(ROOT, "project", "policies")
RULE_DIR = os.path.join(ROOT, "project", "rules")
CONFIG_DIR = os.path.join(ROOT, "project", "config")


# ---------------------------------------------------------
# YAML Loader
# ---------------------------------------------------------

def load_yaml(filename):

    if not os.path.isfile(filename):
        raise Exception(f"File not found:\n{filename}")

    with open(filename, "r") as fp:
        return yaml.safe_load(fp)


# ---------------------------------------------------------
# Flatten nested dictionaries
#
# Example
#
# MONGO:
#     DB_HOST: localhost
#
# becomes
#
# MONGO.DB_HOST
#
# ---------------------------------------------------------

def flatten_dict(data, prefix=""):

    result = {}

    for key, value in data.items():

        name = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):

            result.update(
                flatten_dict(value, name)
            )

        else:

            result[name] = value

    return result


# ---------------------------------------------------------
# Restore nested dictionary
#
# (useful in future markdown/json output)
# ---------------------------------------------------------

def unflatten_dict(flat):

    result = {}

    for key, value in flat.items():

        current = result

        parts = key.split(".")

        for p in parts[:-1]:

            current = current.setdefault(p, {})

        current[parts[-1]] = value

    return result


# ---------------------------------------------------------
# Load Policy
# ---------------------------------------------------------

def load_policy(policy_name):

    if policy_name.endswith(".yaml"):

        filename = os.path.join(
            POLICY_DIR,
            policy_name
        )

    else:

        filename = os.path.join(
            POLICY_DIR,
            f"policy-{policy_name}.yaml"
        )

    policy = load_yaml(filename)

    return policy


# ---------------------------------------------------------
# Load Rule
# ---------------------------------------------------------

def load_rule(rule_name):

    filename = os.path.join(
        RULE_DIR,
        f"rule-{rule_name}.yaml"
    )

    return load_yaml(filename)


# ---------------------------------------------------------
# Load Action Configuration
# ---------------------------------------------------------

def load_action(action_name):

    filename = os.path.join(
        CONFIG_DIR,
        f"config-{action_name}.yaml"
    )

    cfg = load_yaml(filename)

    return cfg["CONFIG"]


# ---------------------------------------------------------
# Merge configuration
#
# returns
#
# parameter
#     default value
#     override value
#     overridden True/False
#
# ---------------------------------------------------------

def merge_configuration(default_cfg,
                        override_cfg):

    base = flatten_dict(default_cfg)

    override = flatten_dict(override_cfg)

    merged = {}

    #
    # default parameters
    #
    for key, value in base.items():

        merged[key] = {
            "default": value,
            "value": value,
            "override": False
        }

    #
    # apply overrides
    #
    for key, value in override.items():

        if key in merged:

            merged[key]["value"] = value
            merged[key]["override"] = True

        else:

            #
            # parameter introduced only by Rule
            #
            merged[key] = {
                "default": None,
                "value": value,
                "override": True
            }

    return merged


# ---------------------------------------------------------
# Pretty printing helpers
# ---------------------------------------------------------

def line():

    print("-" * 72)


def title(text):

    line()
    print(text)
    line()



# ---------------------------------------------------------
# Explain one Action
# ---------------------------------------------------------

def explain_action(action_alias,
                   action_name,
                   rule):

    print(f"        Action : {action_alias}")
    print(f"            implementation : {action_name}")

    #
    # load default Action configuration
    #
    action_cfg = load_action(action_name)

    #
    # Rule override (if present)
    #
    override_cfg = {}

    if "ACTION_RULE_CONFIG" in rule:
        override_cfg = rule["ACTION_RULE_CONFIG"].get(
            action_name,
            {}
        )

    merged = merge_configuration(
        action_cfg,
        override_cfg
    )

    #
    # for now...
    # simply print merged dictionary
    #
    for parameter in sorted(merged.keys()):

        info = merged[parameter]

        if info["override"]:

            print(
                f"            * {parameter} = {info['value']}  [OVERRIDE]"
            )

        else:

            print(
                f"            - {parameter} = {info['value']}"
            )

    print()


# ---------------------------------------------------------
# Explain one Rule
# ---------------------------------------------------------

def explain_rule(rule_name):

    print()

    print(f"    Rule : {rule_name}")

    rule = load_rule(rule_name)

    actions = rule["ACTIONS_SEQUENCE"]

    action_map = rule["ACTION_MAP"]

    #
    # preserve execution order
    #
    for step in sorted(actions.keys(),
                       key=int):

        alias = actions[step]

        action = action_map[alias]

        explain_action(
            alias,
            action,
            rule
        )


# ---------------------------------------------------------
# Explain Policy
# ---------------------------------------------------------

def explain_policy(policy):

    title(
        f"Policy : {policy['POLICY_NAME']}"
    )

    print(
        policy["POLICY_DESCRIPTION"]
    )

    print()

    print("Rules")
    print("=====")

    sequence = policy["RULES_SEQUENCE"]

    for step in sorted(sequence.keys(),
                       key=int):

        explain_rule(
            sequence[step]
        )




# ---------------------------------------------------------
# main
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Explain a RUM Policy"
    )

    parser.add_argument(
        "policy",
        help="Policy name (checkin) or policy YAML file"
    )

    args = parser.parse_args()

    policy = load_policy(args.policy)

    explain_policy(policy)


if __name__ == "__main__":

    main()
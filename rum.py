#! /usr/bin/env python
"""
============
# LEGAL-INFO
============
# Disclaimer:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.
    This script is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY.

# Copyright:
    2024 Massimo Fares, INGV - Italy <massimo.fares@ingv.it>; EIDA Italia Team, INGV - Italy  <adaisacd.ont@ingv.it>

# License:
    GPLv3

# Platform:
    Linux

# Author:
    Massimo Fares, INGV - Italy <massimo.fares@ingv.it>

#
#  adaisacd.ont@ingv.it
#
#  ingv-ont RUM :
#  Simple and lightweight [RU]le [M]anager to apply policies/rules on data files
#
"""

import os
import yaml
import datetime
import logging
# import uuid
from logging.handlers import TimedRotatingFileHandler
import pyinotify
import argparse
from core.sequencer import sequencer

#
# Load global configuration from config-global.yaml
#
"""
cfg_dir = os.path.dirname(os.path.realpath(__file__)) + '/config'
config_global_file = 'config-global.yaml'
if not os.path.isfile(os.path.join(cfg_dir, config_global_file)):
    print("Global config File not found %s" % os.path.basename(config_global_file))
    exit()
else:
    with open(os.path.join(cfg_dir, config_global_file), "r") as cfggbl:
        config_global = yaml.safe_load(cfggbl)
"""
#
# Load Policy, Rules and Actions Configurations and put into a registry
#
def _setup_config(policy_set_arg=None):
    #
    # check if policy args
    if not policy_set_arg:
        # policy_set = config_global['POLICY_SET']
        print("Policy not set! error. ")
        exit()
    else:
        policy_set = policy_set_arg
    #
    # setup directory paths
    policies_dir = os.path.dirname(os.path.realpath(__file__)) + '/project/policies'
    rules_dir = os.path.dirname(os.path.realpath(__file__)) + '/project/rules'
    rule_config_dir = os.path.dirname(os.path.realpath(__file__)) + '/project/config'
    #
    # setup policy file
    policy_set_policies_file = "policy-" + policy_set + ".yaml"
    
    print(policies_dir)

    #
    # init working dictionaries
    config = {}
    config_sub_rulemap = {}
    config_sub_ruleconfig = {}
    actions_seq = {}
    actions_map = {}
    actions_rule_config = {}
    actions_config = {}
    #
    # Load config for specific policy
    if not os.path.isfile(os.path.join(policies_dir, policy_set_policies_file)):
        print("Policy config File not found %s" % os.path.basename(policy_set_policies_file))
        exit()
    else:
        with open(os.path.join(policies_dir, policy_set_policies_file), "r") as cfg:
            config_policy = yaml.safe_load(cfg)

    #
    # "RULES_SEQUENCE":
    rules_sequence = config_policy['RULES_SEQUENCE']
    for config_rule in config_policy['RULES_SEQUENCE']:
        current_rule = config_policy['RULES_SEQUENCE'][config_rule]
        config_rule_file = 'rule-' + current_rule + '.yaml'
        #
        # ACTION_MAP, ACTIONS_SEQUENCE & ACTION_RULE_CONFIG
        if not os.path.isfile(os.path.join(rules_dir, config_rule_file)):
            print("config File not found %s" % os.path.basename(config_rule_file))
            exit()
        else:
            with open(os.path.join(rules_dir, config_rule_file), "r") as cfg:
                config_sub_rulemap[current_rule.upper()] = yaml.safe_load(cfg)

            actions_seq[current_rule.upper()] = config_sub_rulemap[current_rule.upper()]['ACTIONS_SEQUENCE']
            actions_map[current_rule.upper()] = config_sub_rulemap[current_rule.upper()]['ACTION_MAP']
            if "ACTION_RULE_CONFIG" in config_sub_rulemap[current_rule.upper()]:
                actions_rule_config[current_rule.upper()] = config_sub_rulemap[current_rule.upper()]['ACTION_RULE_CONFIG']
        #
        # ACTIONS_CONFIG
        for k in actions_map[current_rule.upper()]:
            rule_set_config_file = "config-" + actions_map[current_rule.upper()][k] + ".yaml"
            
            if not os.path.isfile(os.path.join(rule_config_dir, rule_set_config_file)):
                print("config File not found %s" % os.path.basename(rule_set_config_file))
                exit()
            else:
                with open(os.path.join(rule_config_dir, rule_set_config_file), "r") as cfg1:
                    config_sub_ruleconfig[current_rule.upper()] = yaml.safe_load(cfg1)
                actions_config[actions_map[current_rule.upper()][k].upper()] = config_sub_ruleconfig[current_rule.upper()]['CONFIG']
    #
    # put all config default_vars into config registry
    config['POLICY_FILE'] = policy_set_policies_file
    # config['RUM_VERSION'] = config_policy['RUM-VERSION']
    config['RULE_SET_PATH'] = rules_dir
    config['ACTION_CONFIG_PATH'] = rule_config_dir
    config['UTILS_PATH'] = os.path.dirname(os.path.realpath(__file__)) + '/utils'
    config["POLICY_NAME"] = policy_set.upper()
    config["LOG_FILE"] = config_policy['LOG_FILE']
    config["LOG_LEVEL"] = config_policy['LOG_LEVEL']
    config["WATCHED_ARCHIVE"] = config_policy['WATCHED_ARCHIVE']
    config['RULES_SEQUENCE'] = rules_sequence
    config['ACTIONS_SEQUENCE'] = actions_seq
    config['ACTION_MAP'] = actions_map
    config['ACTIONS_CONFIG'] = actions_config
    # config['ACTIONS_RULE_CONFIG'] = actions_rule_config
    #
    """
    # Loop over config_policy options and replace any default options
    for key in config_policy:
        if key != 'RULES_SEQUENCE':
            config[key] = config_policy[key]
    """

    # Loop over actions rule config and replace any actions config values
    for conf_rule in actions_rule_config:
        for conf_action in actions_rule_config[conf_rule]:
            for key_conf in actions_rule_config[conf_rule][conf_action]:
                config['ACTIONS_CONFIG'][conf_action.upper()][key_conf] = actions_rule_config[conf_rule][conf_action][key_conf]

    # @TODO: in progress
    # if 'PERSISTENT_OBJECTS' in config_policy:
        # config['PERSISTENT_OBJECTS'] = config_policy['PERSISTENT_OBJECTS']

    print(config)
    return config


#
# build logger
#
def _setup_logger():
    # Set up RUM-logger
    log = logging.getLogger("RUM-" + config['POLICY_NAME'])
    log_dir = os.path.dirname(os.path.realpath(__file__)) + '/log'
    log_file = os.path.join(log_dir, config['LOG_FILE'])
    # check if exist path & file
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.isfile(log_file):
        open(log_file, 'a').close()
    # Set Log-Level
    log.setLevel(config['LOG_LEVEL'])
    # start log
    file_handler = TimedRotatingFileHandler(log_file, when="midnight")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(file_handler)
    return log


#
# Set Session
#
def _setup_session():
    session = {}
    # make a UUID based on the host address and current time if needed
    # session['GLOBAL_SESS_ID'] = uuid.uuid1()
    return session


#
# event-driven-section
#
#  Event Handler
#
#
class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, config, log, session):
        self.config = config
        self.log = log
        self.session = session
        # init sequencer
        self.sequencer = sequencer(config, log, session)

    #
    # apply rules on every new file into watched directory
    #
    def process_IN_CLOSE_WRITE(self, event):
        self.process(event)

    def process_IN_MOVED_TO(self, event):
        self.process(event)

    def process_IN_CREATE(self, event):
        self.process(event)

    def process(self, event):
        time_initialized2 = datetime.datetime.now()
        self.log.info(" event: %s" % event)
        single_file = event.pathname
        self.log.info(" ** process_IN_MOVED_TO starting with this file  : " + str(single_file))
        #
        # run sequencer
        self.sequencer.doSequence(single_file)
        #
        # end of sequence
        self.log.info(" ** Sequence is done, all rules completed in %s." % (datetime.datetime.now() - time_initialized2))


#
# procedure-driven-section
#
#  Procedure Handler
#
#
class ProcedureHandler():

    def __init__(self, config, log, session):
        self.config = config
        self.log = log
        self.session = session
        # init sequencer
        self.sequencer = sequencer(config, log, session)

    #
    # apply rules on all files in the list
    #
    def process_IN_LIST_FILES(self, list_file):
        time_initialized3 = datetime.datetime.now()
        self.log.info(" ** process_IN_LIST_FILES starting ")
        #
        # run sequencer
        for file in list_file:
            self.log.info(" ** process_IN_LIST_FILES starting with this file  : " + str(file))
            self.sequencer.doSequence(file)
        #
        # end of sequence
        self.log.info(" ** Sequence is done, all rules completed in %s." % (datetime.datetime.now() - time_initialized3))


#
#
# MAIN
#
#
if __name__ != '__main__':
    pass
else:
    parser = argparse.ArgumentParser(description="INGV-ONT RUM - a Basic And Lightweight RUle Manager : \nProcess mSEED files "
                                                 "and apply the specified policy/rules. ")

    # Input file options
    parser.add_argument('--mode', help='execution mode t: terminal = one shot exec; d: daemon = watch on dir', default='t')
    parser.add_argument('--files', help='specific list of files to be processed: file1 file2 ...', nargs='+')
    parser.add_argument('--archive', help='archive (sds or directory) containing the files to process, also with specific --julian-day option ', default=None)
    parser.add_argument('--julian-day', help='process files for a specific julian-day (e.g. 234) to apply this --archive option must specified', default=None)
    parser.add_argument('--policy-set', help='a policy name (point to file) that contains a set of rules in /policies dir', default=None)

    # @TODO: do a project argument
    # parser.add_argument('--project', help='a project name (point to directory) that contains a set of policies ', default=None)
    # parser.add_argument('--version', action='version', version=config['RUM-VERSION'])


    # Get parsed arguments
    parsedargs = vars(parser.parse_args())
    # get config
    config = _setup_config(parsedargs['policy_set'])
    # init log
    log = _setup_logger()
    # get session
    session = _setup_session()



    # Case: [d]
    # Daemon mode - Event-Driven
    #
    if parsedargs['mode'] == 'd':
        #
        # Event Manager
        #
        wm = pyinotify.WatchManager()
        # watched events
        # pipe for multiple events: mask = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE ; pyinotify.IN_MOVED_TO ; ALL_EVENTS
        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO
        # start handler
        handler = EventHandler(config, log, session)
        notifier = pyinotify.Notifier(wm, handler)
        # watched directory and subdirectories
        wdd = wm.add_watch(config["WATCHED_ARCHIVE"], mask, rec=True)

        # go
        log.info(" * * * * * * * * * rule manager daemon mode started * * * * * * * * *")

        #
        # do watcher
        #
        notifier.loop()

    # Case: [t]
    # Terminal mode - Procedural-Driven
    #
    elif parsedargs['mode'] == 't':
        # @TODO: at the moment only config by file is checked
        #
        # Procedure Manager
        #
        # set empty list of files
        my_list_file = []
        handler = ProcedureHandler(config, log, session)

        # switch on Options:
        #
        # list of files
        if parsedargs['files']:
            my_list_file = parsedargs['files'].split(" ")
        #
        # Archive
        elif parsedargs['archive']:

            for root, dirs, files in os.walk(parsedargs['archive']):  # i.e. --archive "/archive/2010/IV"
                for myfile in files:
                    #
                    # Julian day option # i.e. --archive "/archive/2010/IV" --julian-day 235
                    if parsedargs['julian_day']:
                        if myfile.endswith(parsedargs['julian-day']):  # IV.ZCCA
                            my_list_file.append(os.path.join(root, myfile))
                    # all Archive
                    else:
                        my_list_file.append(os.path.join(root, myfile))
        #
        # Some day ago
        elif parsedargs['day-ago']:
            # in progress
            log.info(" - ")
        #
        # if no option raise an error
        else:
            raise Exception("Argument options are mandatory, one of : --files; --archive; --julian-ago")

        # go
        log.info("* * * * * * * * * rule manager terminal mode started * * * * * * * * *")

        #
        # do process
        #
        handler.process_IN_LIST_FILES(my_list_file)

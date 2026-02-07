#! /usr/bin/env python
"""
#
#  adaisacd.ont@ingv.it
#
  
"""

# import os
# import json
import collections
import importlib
import datetime
# from contextlib import suppress # to suppress error key on dictionary


#
# implement rules sequence
#
class sequencer(object):

    # init

    def __init__(self, config, log, session):

        self.config = config
        self.log = log
        self.session = session
        self.action_list = []
        self.log.info("init sequencer for policy: "+self.config['POLICY_NAME'])
        #
        # Load action_list from rules sequence
        self.rules_definition = collections.OrderedDict(sorted(self.config['RULES_SEQUENCE'].items()))
        for k, rule in self.rules_definition.items():
            for i, action in self.config['ACTIONS_SEQUENCE'][rule.upper()].items():
                self.action_list.append(self.config['ACTION_MAP'][rule.upper()][action])

    #
    # run entire Sequence on action_list
    #
    def doSequence(self, digital_object):
        # at the moment a digital_object could be a list of file (t) or a single file (d);
        # it depends who call it (from template.py) : (t)erminal or (d)aemon

        # so, are you list or single?
        if isinstance(digital_object, list):
            for my_file in digital_object:
                self.log.info(
                    " --- --- --- --- --- --- --- --- START SEQUENCE :: " + self.config['POLICY_NAME'] + " ON " + my_file + " \n")
                timeStartMainSeq = datetime.datetime.now()
                #
                # do atcions on file
                self.doActions(my_file)

                self.log.info("*** SEQUENCE is done, completed in %s." % (datetime.datetime.now() - timeStartMainSeq))
                self.log.info(" --- --- --- --- --- --- --- --- END SEQUENCE :: " + self.config['POLICY_NAME'] + " ON " + my_file + "\n")

        elif isinstance(digital_object, str):
            self.log.info(" --- --- --- --- --- --- --- --- START SEQUENCE :: " + self.config['POLICY_NAME'] + " ON " + digital_object + " \n")
            timeStartMainSeq = datetime.datetime.now()
            #
            # do atcions on file
            self.doActions(digital_object)

            self.log.info("*** SEQUENCE is done, completed in %s." % (datetime.datetime.now() - timeStartMainSeq))
            self.log.info(" --- --- --- --- --- --- --- --- END SEQUENCE :: " + self.config['POLICY_NAME'] + " ON " + digital_object + "\n")
        # you're BAD
        else:
            self.log.error(" digital_object ERROR could not execute: " + str(digital_object) + " input param is not valid!\n")
            return

    #
    # do Actions on single file
    #
    def doActions(self, single_file):

        # setup session for all actions in this loop
        #
        local_session = {'SESS_ID': single_file, 'GOTO': 'none', 'SKIP': 0, 'EXIT': 0}
        self.session['SESSION'] = local_session
        
        # for test only
        # print("SESSION-START:")
        # print(self.session)
        # print("-----action list-------")
        # print(self.action_list)
        # print("-------")

        self.log.info(self.action_list)
        # Apply each action on current file
        for my_action in self.action_list:

            # Check session control flow:
            # from inside an action we could speficy some flow control, like skip, jump or exit, via setting the appropriate session-key.
            # Session could be used, also, to comunicate some info between actions in the same loop (enteire policy cycle on a single file).
            self.log.info("list of my action: " + my_action)
            self.log.info(self.session)

            #
            # SKIP: skip to next action
            if self.session['SESSION']['SKIP'] == 1:
                self.log.info(" --- --- --- --- --- --- --- --- SKIP ACTION " + my_action.upper() + " \n")
                self.log.info(" --- --- --- --- --- --- --- --- SKIP TO NEXT ACTION \n")
                # reset skip
                self.session['SESSION']['SKIP'] = 0
                continue

            #
            # GOTO: jump to action
            # be aware! goto action could be executed only in forward direction.
            # suggest: don't use it, if not strectly neccesary.
            if self.session['SESSION']['GOTO'] != "none":
                self.log.info(
                    " --- --- --- --- --- --- --- --- GO TO ACTION " + self.session['SESSION']['GOTO'] + " \n")
                if self.session['SESSION']['GOTO'] != my_action:
                    continue
                else:
                    # reset jump
                    self.session['SESSION']['GOTO'] = "none"

            #
            # EXIT: skip to next file
            if self.session['SESSION']['EXIT'] == 1:
                self.log.info(" --- --- --- --- --- --- --- --- EXIT ACTION " + my_action.upper() + " \n")
                self.log.info(" --- --- --- --- --- --- --- --- EXIT: SKIP TO NEXT FILE \n")
                # destroy session
                del(self.session['SESSION'])
                return

            # Flow control ok: GO for Action
            self.log.info(" --- --- --- --- --- --- --- --- START ACTION " + my_action.upper() + " \n")

            # Convert action/plug-in from naming convention
            module_name = "project.actions."+my_action
            my_run = "do_" + my_action

            # load action module
            module = importlib.import_module(module_name)

            # build action's class
            myclass = getattr(module, f"{my_action}")

            # instantiate action objct
            myobject = myclass(self.config, self.log, self.session)

            try:
                self.log.info(my_action + " in sequence")
                # run action
                myresult = getattr(myobject, f"{my_run}")(single_file)
            except Exception as ex:
                self.log.error(" ACTION error, could not execute: " + my_action)
                self.log.error(ex)
                pass

            self.log.info(" --- --- --- --- --- --- --- --- END ACTION " + my_action.upper() + " \n")

        # for test only
        # print("SESSION-END:")
        #print(self.session)
        
        # destroy session
        del(self.session['SESSION'])
        return

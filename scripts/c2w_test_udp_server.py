#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from set_path import set_path
stockrsm_path = set_path()

# PYTHON_ARGCOMPLETE_OK

import argcomplete, argparse
import subprocess
import os
import sys

from argcomplete.completers import ChoicesCompleter
from argcomplete.completers import EnvironCompleter

class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

def main():
    trial_class = 'c2w.test.protocol.udp_server_test.c2wUdpChatServerTestCase'
    parser = argparse.ArgumentParser(description='Trial udp server test',
                                 formatter_class=SmartFormatter)  
    with open(os.path.join(stockrsm_path, "data",
                           "c2w",
                           "test",
                           "udp_server_tests_list.txt")) as tests_list:
        tests = list(l.rstrip('\n') for l in tests_list.readlines())
    if not tests:
        print("Sorry, no test available for the moment")
        exit()
    # stupid hack for [""] + tests for getting the alignment of values. To be modified.
    parser.add_argument("--scenario", 
                        help='''R|Scenario name. Allowed values are
                        ''' + '\n'.join([""] + tests,)).completer=ChoicesCompleter(tuple(tests))

    argcomplete.autocomplete(parser)
    options = parser.parse_args()
    
    cmdLine = ['trial', trial_class + ".test_" + options.scenario]
    
    os.environ['STOCKRSMPATH'] = stockrsm_path
    
    del sys.argv[-1]
    del sys.argv[-1]
    sys.argv.append(trial_class + ".test_" + options.scenario)
    sys.path.insert(0, os.path.abspath(os.getcwd()))
    
    from twisted.scripts.trial import run
    run()
    
#     try:
#         _ = subprocess.call(cmdLine, env={'PYTHONPATH':':'.join(sys.path),
#                                           'STOCKRSMPATH':stockrsm_path})
#     except KeyboardInterrupt:
#         pass  # ignore CTRL-C

if __name__ == '__main__':
    main()

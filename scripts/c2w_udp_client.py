#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import os

# Set path and import C2wStart
from set_path import set_path
set_path()
from  c2w.main.c2w_client import C2wStart

# Settings
protocol = 'UDP'

parser = argparse.ArgumentParser(description='c2w Client (UDP Version)')
parser.add_argument('-e', '--debug',
                    dest='debugFlag',
                    help='Raise the log level to debug',
                    action="store_true",
                    default=False)
parser.add_argument('-l', '--loss-pr', dest='lossPr',
                    help='The packet loss probability for outgoing ' +
                    'packets.', type=float, default=0)

options = parser.parse_args()


# Call start function
C2wStart(protocol,
         options.debugFlag, 
         options.lossPr)


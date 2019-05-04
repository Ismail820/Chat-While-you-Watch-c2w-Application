#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import os

# Set path and import C2wStart
from set_path import set_path
set_path()
from  c2w.main.c2w_server import C2wStart

# Settings
protocol = 'UDP'

parser = argparse.ArgumentParser(description='c2w Server (UDP Version)')
parser.add_argument('-p', '--port', dest='serverPort', type=int,
                    help='The port number to be used for listening.',
                    default=1950)
parser.add_argument('-n', '--no-video',
                    dest='noVideoFlag',
                    help='Do not use the video part.',
                    action="store_true", default=False)
parser.add_argument('-s', '--stream-video',
                    dest='streamVideoFlag',
                    help='Enable sending the video stream to other ' +
                    'computers (if this option is not given, only ' +
                    'on the local machine will be able to receive the ' +
                    'video stream).',
                    action="store_true", default=False)
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
         options.serverPort,
         options.noVideoFlag,
         options.streamVideoFlag,
         options.debugFlag, 
         options.lossPr)


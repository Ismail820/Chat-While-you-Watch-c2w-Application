# -*- coding: utf-8 -*-

import sys
import os
from os.path import dirname

env_var_name = 'RESPYTHONPATH'
test_var_name = 'RESIMPLPATH'

default_c2w_path = '~/Documents/c2w-implementation/res209'
stockrsm_twisted_path = "/usr/home/enstb2/projets/stockrsm/.local/lib/python3.4/site-packages"

def set_path():
    c2w_path = os.getenv(env_var_name, default_c2w_path)
    script_path = dirname(dirname(dirname(os.path.abspath(__file__))))
    stock_rsm_path = os.path.expanduser(c2w_path)
    
    # test si RESIMPLPATH exists
    if test_var_name in os.environ:
        sys.path.insert(0, os.environ[test_var_name])
        test_path = os.path.dirname(os.environ[test_var_name])
    else:
        test_path = stock_rsm_path

    sys.path.insert(0, script_path)
    sys.path.insert(0, stock_rsm_path)
    
    if (os.path.isdir(stockrsm_twisted_path)):
        sys.path.insert(0, stockrsm_twisted_path)
    
    import twisted
    print ("Twisted version in use: " + twisted.version.short())
    
    print (sys.path)
    return test_path

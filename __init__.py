import sys

sys.dont_write_bytecode = True

from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

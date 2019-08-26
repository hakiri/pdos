#!/usr/bin/env python3

import os
import sys
if os.getuid() != 0:
	print ("Must be run as root, sorry.")
	sys.exit(-1)

from solcx import install_solc_pragma
install_solc_pragma('>0.5.0 <0.6.0')

print ("Done.")

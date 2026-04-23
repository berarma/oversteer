#!/bin/bash
python3 -c "
import sys
sys.path.insert(0, '/home/caz/Documents/oversteer')
from oversteer.application import Application
app = Application('dev', '/home/caz/Documents/oversteer/data', '/home/caz/Documents/oversteer/data')
sys.exit(app.run(sys.argv))
" "$@"
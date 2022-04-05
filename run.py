import sys
import os
path = ""

sys.path.append(os.path.join(path, "facecap_setup_device"))
from facecap_setup_tool import run
run()
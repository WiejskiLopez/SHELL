import sys
import pathlib

THIS_DIR = pathlib.Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent.parent.parent  # shell/

if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

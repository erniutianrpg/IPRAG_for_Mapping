import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from python_experiment_runner import main


if __name__ == "__main__":
    main(SCRIPT_DIR)

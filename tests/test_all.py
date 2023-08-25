import unittest
import sys

from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if (str(ROOT)) not in sys.path:
    sys.path.append(str(ROOT))  # add root directory to PATH

if __name__ == '__main__':
    testsuite = unittest.TestLoader().discover(start_dir='tests/')
    unittest.TextTestRunner(verbosity=1).run(testsuite)

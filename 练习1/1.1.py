import os
import sys


if __name__ == "__main__":
    pip_path = sys.base_exec_prefix + '/Scripts/pip.exe'
    os.system(pip_path + ' list')


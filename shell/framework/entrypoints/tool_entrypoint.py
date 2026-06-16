import sys

from shell.framework.cli.main import main

if __name__ == '__main__':
    sys.exit(main(['tool', *sys.argv[1:]]))


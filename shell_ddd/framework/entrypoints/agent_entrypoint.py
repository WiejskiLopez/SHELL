import sys

from shell_ddd.framework.cli.main import main

if __name__ == '__main__':
    sys.exit(main(['agent', *sys.argv[1:]]))


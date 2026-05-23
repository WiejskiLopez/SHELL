import sys

from shell.app.app import App
def main() -> int:
    app = App.init_app(mode='agent', runner_root_dir=__file__)
    return app.run_app()
if __name__ == "__main__":
    sys.exit(main())

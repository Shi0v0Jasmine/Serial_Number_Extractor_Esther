"""Compatibility entrypoint for Serial Number Extractor."""

from serial_extractor.app import *  # noqa: F401,F403
from serial_extractor.app import main


if __name__ == "__main__":
    raise SystemExit(main())

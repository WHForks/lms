#!/usr/bin/env python
import os
import sys
from pathlib import Path

from django.core.management import execute_from_command_line

ROOT_DIR = Path(__file__).parent.resolve()
sys.path.append(str(ROOT_DIR / "apps/"))


def main():
    # On production use --settings to override default behavior
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.settings.extended")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

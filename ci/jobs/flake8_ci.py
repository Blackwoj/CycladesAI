import os
import sys

from badge_generator import generate_badge
from flake8.main import cli as flake8

job_name = "flake8"


def flake8_run():
    try:
        flake8.main()
    except SystemExit as e:
        return e.code
    return False


def code_to_value(fail):
    if fail is False:
        return "pass"
    return "fail"


def main():
    fail = flake8_run()

    if not os.path.exists(job_name):
        os.mkdir(job_name)

    value = code_to_value(fail)
    thresholds = {
        "pass": "green",
        "fail": "brightred",
    }
    generate_badge(job_name, value, thresholds)
    return fail


if __name__ == "__main__":
    sys.exit(main())

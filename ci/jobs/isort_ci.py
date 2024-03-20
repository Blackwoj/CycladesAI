import os
import sys

from badge_generator import generate_badge
from isort.main import main as isort_main

job_name = "isort"


def isort_run():
    try:
        isort_main()
    except SystemExit as e:
        return e.code
    return False


def code_to_value(code):
    if code == 0:
        return "pass"
    return "fail"


def main():
    code = isort_run()

    if not os.path.exists(job_name):
        os.mkdir(job_name)

    value = code_to_value(code)
    thresholds = {
        "pass": "green",
        "fail": "brightred",
    }
    generate_badge(job_name, value, thresholds)
    return code


if __name__ == "__main__":
    sys.exit(main())

import os
import sys

import pytest

from badge_generator import generate_badge


job_name = "pytest"


def pytest_run():
    return pytest.main()


def code_to_value(code):
    if code == 0:
        return "pass"
    return "fail"


def main():
    code = pytest_run()

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

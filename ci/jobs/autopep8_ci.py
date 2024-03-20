import os
import sys

import autopep8
from badge_generator import generate_badge

job_name = "autopep8"


def autopep8_run():
    return autopep8.main()


def code_to_value(code):
    print(code)
    if autopep8.EXIT_CODE_OK == code or code is None:
        return "pass"
    if autopep8.EXIT_CODE_EXISTS_DIFF == code:
        return "fail"
    return "error"


def main():
    code = autopep8_run()

    if not os.path.exists(job_name):
        os.mkdir(job_name)

    value = code_to_value(code)
    thresholds = {
        "pass": "green",
        "error": "maroon",
        "fail": "brightred"
    }
    generate_badge(job_name, value, thresholds)
    return code


if __name__ == "__main__":
    sys.exit(main())

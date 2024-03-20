import glob
import os
import sys

import pylint.lint
from badge_generator import generate_badge

job_name = "pylint"


def pylint_run():
    modules = glob.glob('./**/*.py')
    pylint_opts = modules
    return pylint.lint.Run(pylint_opts, do_exit=False)


def get_pylint_score(run):
    score_value = run.linter.generate_reports()

    if score_value < run.linter.config.fail_under:
        return True, score_value  # Fail
    return False, score_value  # Pass


def main():
    run = pylint_run()
    fail, score = get_pylint_score(run)

    if not os.path.exists(job_name):
        os.mkdir(job_name)

    thresholds = {
        10: "green",
        8: "yellow",
        6: "orange",
        4: "red",
        2: "brightred"
    }
    generate_badge(job_name, score, thresholds, value_format="%.2f", value_suffix="/10")
    return fail


if __name__ == "__main__":
    sys.exit(main())

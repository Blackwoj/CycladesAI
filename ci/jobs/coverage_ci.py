import os
import sys

from coverage.cmdline import main as coverage_main


job_name = "coverage"


def coverage_run():
    return coverage_main()


def main():
    code = coverage_run()

    if not os.path.exists(job_name):
        os.mkdir(job_name)
    return code


if __name__ == "__main__":
    sys.exit(main())

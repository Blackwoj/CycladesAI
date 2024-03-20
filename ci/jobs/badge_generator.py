import anybadge


def generate_badge(job_name, value, thresholds, value_format='%s', value_suffix=''):
    badge = anybadge.Badge(
        label=job_name,
        value=value,
        default_color="lightgrey",
        thresholds=thresholds,
        value_format=value_format,
        value_suffix=value_suffix
    )
    badge.write_badge("{}/{}.svg".format(job_name, job_name), overwrite=True)

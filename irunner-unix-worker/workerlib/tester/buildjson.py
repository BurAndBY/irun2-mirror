import json

from workerlib.iface import CheckFailed


def parse_buildjson(path):
    try:
        with path.open() as fd:
            return json.load(fd)
    except (IOError, json.JSONDecodeError):
        raise CheckFailed('Unable to parse build JSON')


def extract_compilation_log(buildjson):
    logs = {}

    for res in buildjson['results']:
        log = res.get('log')
        configuration = res.get('configuration')

        if log is not None:
            cfgs = logs.setdefault(log, [])
            if configuration:
                cfgs.append(configuration)

    log = None
    if logs:
        output = []
        for log, configurations in logs.items():
            if log:
                if len(logs) > 1 and len(configurations) > 0:
                    output.append('=== Configurations: {} ==='.format(', '.join(configurations)))
                output.append(log)
        log = '\n'.join(output)

    return buildjson.get('success', False), log

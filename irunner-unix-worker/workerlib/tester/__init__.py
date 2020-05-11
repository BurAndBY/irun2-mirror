def create_tester(mode, cache):
    if mode == 'LOCAL':
        from .local import LocalTester
        return LocalTester(cache)

    elif mode == 'DOCKER':
        # depends on Docker client library
        from .docker import DockerTester
        return DockerTester(cache)

    else:
        raise ValueError('Unsupported mode: {}'.format(mode))

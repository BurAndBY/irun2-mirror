import argparse
import configparser
import logging
import random
import string

from workerlib.apiclient import IRunnerApiClient, IRunnerApiStateCallback
from workerlib.iface import CheckFailed, TestingReport
from workerlib.cache import Cache
from workerlib.sleeper import Sleeper
from workerlib.tester import create_tester


def set_up_logging():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler('worker.log'),
            logging.StreamHandler()
        ]
    )


def gen_name():
    return 'unix:{}'.format(''.join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    ))


def main():
    set_up_logging()
    logging.info('Hello, Sir! It\'s test server.')
    worker_name = gen_name()

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path to config file', default='config.ini', nargs='?')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    cache = Cache('cache')

    api_client = IRunnerApiClient(
        worker_name,
        config['Server']['endpoint'],
        config['Server']['token']
    )

    sleeper = Sleeper(
        api_client,
        float(config['Server']['interval'])
    )

    tester = create_tester(config['Tester']['mode'], cache)

    need_sleep = False
    while True:
        if need_sleep:
            try:
                sleeper.sleep()
            except KeyboardInterrupt:
                logging.info('Bye!')
                break

        job = api_client.take_job(cache)
        if job is None:
            logging.info('Nothing to test')
            need_sleep = True
            continue

        callback = IRunnerApiStateCallback(api_client, job.job_id)
        try:
            report = tester.run(job, 'sandbox', callback)
        except CheckFailed as e:
            logging.exception(e.message)
            report = TestingReport.check_failed(e.message)
        api_client.put_report(job.job_id, report)
        need_sleep = False


if __name__ == '__main__':
    main()

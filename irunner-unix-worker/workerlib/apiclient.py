import logging
import urllib
import requests

from requests.adapters import HTTPAdapter
from requests.exceptions import Timeout
from requests.packages.urllib3.util.retry import Retry

from .resourceid import (
    ResourceId,
    tojson,
)
from .iface import (
    LibraryFile,
    TestingJob,
    TestCase,
    IStateCallback,
)


class IRunnerApiClient:
    def __init__(self, name, endpoint, token):
        self._greeting = {
            'name': name,
            'tag': 'unix'
        }
        self._endpoint = endpoint

        self._session = requests.Session()
        self._session.headers['Worker-Token'] = token
        self._session.headers['X-iRunner-Worker-Tag'] = 'unix'
        self._set_up_retries(self._session)

    def wait_on_semaphore(self):
        try:
            r = self._session.post(self._url('semaphore/wait'), timeout=60.0)
        except Timeout:
            logging.warning('Semaphore request timeout')
            return False
        return r.status_code == requests.codes.OK

    def take_job(self, cache):
        r = self._session.post(self._url('jobs/take'), json=self._greeting)
        if r.status_code == requests.codes.NOT_FOUND:
            return None

        logging.debug('Got job: %s', r.json())

        jsonjob = r.json()
        jsonproblem = jsonjob['problem']
        jsonchecker = jsonproblem['checker']
        assert jsonchecker['kind'] in (TestingJob.PYTEST, TestingJob.GTEST)

        job_id = jsonjob['id']
        job = TestingJob(job_id)

        job.solution_resource_id = self._fetch_resource(cache, jsonjob['solution'])
        job.solution_compiler = jsonjob['solution'].get('compiler')
        job.checker_resource_id = self._fetch_resource(cache, jsonchecker['source'])
        job.checker_kind = jsonchecker['kind']
        job.default_time_limit = jsonproblem.get('defaultTimeLimit', job.default_time_limit)
        job.solution_filename = jsonjob['solution'].get('filename', job.solution_filename)

        for lib in jsonproblem['libraries']:
            source = lib['source']
            job.libraries.append(LibraryFile(
                resource_id=self._fetch_resource(cache, source),
                filename=source['filename'],
                compiler=source['compiler']
            ))

        for jsontest in jsonproblem['tests']:
            tc = TestCase()
            tc.test_case_id = jsontest.get('id')
            tc.input_resource_id = self._fetch_resource(cache, jsontest.get('input'))
            tc.answer_resource_id = self._fetch_resource(cache, jsontest.get('answer'))
            job.test_cases.append(tc)

        return job

    def set_compiling_state(self, job_id):
        self._session.put(self._url('jobs/{}/state'.format(job_id)), json={'status': 'COMPILING'})

    def set_testing_state(self, job_id):
        self._session.put(self._url('jobs/{}/state'.format(job_id)), json={'status': 'TESTING'})

    def put_report(self, job_id, report):
        jsontests = []
        for test in report.tests:
            tcr = {
                'outcome': test.outcome.name,
                'checkerMessage': test.message,
                'timeUsed': test.time_used,
                'timeLimit': test.time_limit,
                'outputResourceId': tojson(self._push_resource(test.traceback)),
                'stdoutResourceId': tojson(self._push_resource(test.stdout)),
                'stderrResourceId': tojson(self._push_resource(test.stderr)),
            }
            if test.score is not None:
                tcr['score'] = test.score
            if test.max_score is not None:
                tcr['max_score'] = test.max_score
            if test.test_case is not None:
                tcr['id'] = test.test_case.test_case_id
                tcr['inputResourceId'] = tojson(test.test_case.input_resource_id)
                tcr['answerResourceId'] = tojson(test.test_case.answer_resource_id)
            jsontests.append(tcr)
        logs = []
        if report.compilation_log is not None:
            logs.append({
                'kind': 'SOLUTION_COMPILATION',
                'resourceId': tojson(self._push_resource(report.compilation_log))
            })
        jsonreport = {
            'outcome': report.outcome.name,
            'tests': jsontests,
            'logs': logs,
        }
        if report.score is not None:
            jsonreport['score'] = report.score
        if report.max_score is not None:
            jsonreport['max_score'] = report.max_score
        if report.first_failed_test is not None:
            jsonreport['first_failed_test'] = report.first_failed_test
        logging.info(jsonreport)
        r = self._session.put(self._url('jobs/{}/result'.format(job_id)), json=jsonreport)
        print(r.text)
        r.raise_for_status()

    def fs_download_data(self, resource_id):
        r = self._session.get(self._url('fs/{}').format(resource_id.hexstr), stream=True)
        r.raise_for_status()
        return r.content

    def fs_upload_data(self, blob):
        if isinstance(blob, str):
            blob = blob.encode('utf-8')
        if not isinstance(blob, bytes):
            raise ValueError('invalid data type: {}'.format(type(blob).__name__))

        r = self._session.post(self._url('fs/new'), data=blob)
        logging.info(r.json())
        return ResourceId(r.json()['resourceId'])

    def _url(self, path):
        return urllib.parse.urljoin(self._endpoint, path)

    @staticmethod
    def _set_up_retries(session, retries=3):
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _fetch_resource(self, cache, r):
        if r is None:
            return None
        resource_id = ResourceId(r['resourceId'])
        if resource_id not in cache:
            data = self.fs_download_data(resource_id)
            cache.put(resource_id, data)
        return resource_id

    def _push_resource(self, string):
        if string is None:
            return None
        return self.fs_upload_data(string)


class IRunnerApiStateCallback(IStateCallback):
    def __init__(self, client, job_id):
        self._client = client
        self._job_id = job_id

    def set_compiling(self):
        self._client.set_compiling_state(self._job_id)

    def set_testing(self):
        self._client.set_testing_state(self._job_id)

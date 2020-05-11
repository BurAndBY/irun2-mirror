from subprocess import Popen, PIPE

BUILD_CONFIGURATIONS = ['O0', 'O2', 'asan', 'msan', 'ubsan']


def test(executable, testcase):
    p = Popen([executable], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(testcase.input.text())
    assert stderr == ''
    assert stdout == testcase.answer.text()

import os
import sys
import subprocess
import unicodedata
from subprocess import Popen as _Popen, PIPE as _PIPE

import jaraco.envs


class VirtualEnv(jaraco.envs.VirtualEnv):
    name = '.env'
    # Some version of PyPy will import distutils on startup, implicitly
    # importing setuptools, and thus leading to BackendInvalid errors
    # when upgrading Setuptools. Bypass this behavior by avoiding the
    # early availability and need to upgrade.
    create_opts = ['--no-setuptools']

    def run(self, cmd, *args, **kwargs):
        cmd = [self.exe(cmd[0])] + cmd[1:]
        kwargs = {"cwd": self.root, **kwargs}  # Allow overriding
        return subprocess.check_output(cmd, *args, **kwargs)


def _which_dirs(cmd):
    result = set()
    for path in os.environ.get('PATH', '').split(os.pathsep):
        filename = os.path.join(path, cmd)
        if os.access(filename, os.X_OK):
            result.add(path)
    return result


def run_setup_py(cmd, pypath=None, path=None,
                 data_stream=0, env=None):
    """
    Execution command for tests, separate from those used by the
    code directly to prevent accidental behavior issues
    """
    if env is None:
        env = dict()
        for envname in os.environ:
            env[envname] = os.environ[envname]

    # override the python path if needed
    if pypath is not None:
        env["PYTHONPATH"] = pypath

    # override the execution path if needed
    if path is not None:
        env["PATH"] = path
    if not env.get("PATH", ""):
        env["PATH"] = _which_dirs("tar").union(_which_dirs("gzip"))
        env["PATH"] = os.pathsep.join(env["PATH"])

    cmd = [sys.executable, "setup.py"] + list(cmd)

    # http://bugs.python.org/issue8557
    shell = sys.platform == 'win32'

    try:
        proc = _Popen(
            cmd, stdout=_PIPE, stderr=_PIPE, shell=shell, env=env,
        )

        if isinstance(data_stream, tuple):
            data_stream = slice(*data_stream)
        data = proc.communicate()[data_stream]
    except OSError:
        return 1, ''

    # decode the console string if needed
    if hasattr(data, "decode"):
        # use the default encoding
        data = data.decode()
        data = unicodedata.normalize('NFC', data)

    # communicate calls wait()
    return proc.returncode, data

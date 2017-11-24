
from cx_Freeze import setup, Executable
import sys

    
# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [])


base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('helloworld.py', base=base),
]

setup(name='hello world',
      version = '1.0.1',
      description = 'test',
      options = dict(build_exe = buildOptions),
      executables = executables,
      script_args = ['build']
      )
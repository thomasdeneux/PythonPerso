from cx_Freeze import setup, Executable
import sys


# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [], icon = 'connect.ico', 
                    include_files = ['connect.ico', 'synchronizedFolderIcon.ico'])


base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('secureboxinstall.py', base=base, icon = 'connect.ico'),
    Executable('secureboxdeamon.py', base=base),
    Executable('secureboxboard.py', base=base, icon = 'connect.ico'),
    Executable('secureboxregister.py', base=base),
    Executable('secureboxuninstall.py', base=base),
    Executable('helloworld.py', base=base),
]

setup(name='secure box',
      version = '1.0.5',
      description = 'Secure Box',
      options = dict(build_exe = buildOptions),
      executables = executables,
      script_args = ['build']
      )

# Make sure that printing was disabled
print 'checking that printing was disabled'
import settings
print 'PRINTING WAS NOT DISABLED!!! UNCOMMENT LINES IN SETTINGS.PY BEFORE PACKAGING!'    

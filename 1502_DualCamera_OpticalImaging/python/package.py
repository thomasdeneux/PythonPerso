from cx_Freeze import setup, Executable
import sys


# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ['scipy'], excludes = [], 
                    include_files = ['keyboard.png', ('C:\\Users\\THomas\\Anaconda\\Lib\\site-packages\\scipy\\special\\_ufuncs.pyd','_ufuncs.pyd')])

                     
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('dualcamera.py', base=base),
]

setup(name='dualcamera',
      version = '1.0',
      description = 'alignment tool for dual camera setup',
      options = dict(build_exe = buildOptions),
      executables = executables,
      script_args = ['build']
      )

# Make sure that printing was disabled
print 'MAKE SURE THAT THERE WERE NO PRINT INSTRUCTIONS, AS THEY CAUSE ERRORS'    

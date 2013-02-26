
from dict.bin import checkTasks
from dict.bin.ConfigLoader import ConfigLoader
import os
import sys

""" Modify the python path to point to the /bin directory. """
dirname, filename = os.path.split(sys.argv[0])
sys.path.insert(0, os.path.join(dirname, 'bin'))

""" Execute it immediately to perform the work. """
cl =  ConfigLoader(sys.argv[1:])
checkTasks.run(cl)

""" That's it! """    

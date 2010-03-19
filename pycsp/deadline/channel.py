"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets.channel import Channel as greenletsChannel, ChannelReq as greenletsChannelReq
from scheduling import RT_Scheduler,DeadlineException,Now
from pycsp.greenlets.const import *

class Channel(greenletsChannel):
    def __init__(self, name=None):
        greenletsChannel.__init__(self,name)
        self.readerprocesses = []
        self.s = RT_Scheduler()
      
    def _read(self):
        msg  = greenletsChannel._read(self)
        logging.debug("read: ")
        if self.s.current.has_priority and self.s.current.deadline<Now():
            raise DeadlineException(self.s.current)
        return msg

    def _write(self,msg):
        #if no readers are ready to read we augments their priority to speed up my own write
        if not self.readers:
            logging.warning("no readers will try inherience")
        returnvalue =  greenletsChannel._write(self,msg)
        if self.s.current.has_priority and self.s.current.deadline<Now():
            logging.debug("Throwing Deadline exception")
            raise DeadlineException(self.s.current)
        return returnvalue

    def _addReaderProcess(self, process):
        logging.warning("_addProcess. self: %s\nprocess:%s",self,process)
        self.readerprocesses.append(process)
        
# Run tests
Channel.__doc__ = greenletsChannel.__doc__
def testsuite():
  return
from pycsp.greenlets.channelend import *
testsuite.__doc__ = IN.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += OUT.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += retire.__doc__
testsuite.__doc__ += '\n'  
testsuite.__doc__ += poison.__doc__

if __name__ == '__main__':
    import doctest
    doctest.testmod()

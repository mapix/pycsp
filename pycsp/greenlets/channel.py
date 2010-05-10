"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
"""

# Imports
from scheduling import Scheduler
from channelend import ChannelEndRead, ChannelEndWrite, ChannelRetireException
from const import *

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        logging.debug("creating posion exception")
        pass

# Classes
class ChannelReq:
    def __init__(self, process, msg=None):
        self.msg = msg
        self.result = FAIL
        self.process = process

    def __str__(self):
            return "ChannelReq: msg: %s,\tresult: %s,\t%s"%(self.msg,self.result,"")

    def poison(self):
            logging.debug("poison in ChannelReq")
            if self.result != SUCCESS:
                self.result = POISON
                self.process.notify(POISON)

    def retire(self):
        if self.result != SUCCESS:
            self.result = RETIRE
            self.process.notify(RETIRE)

    def offer(self, recipient):
        logging.error("\nself: %s\nrecipient: %s"%(self.process, recipient.process))
        if self.process.state == recipient.process.state == ACTIVE:
            recipient.msg= self.msg
            self.result=SUCCESS
            recipient.result=SUCCESS
            self.process.notify(DONE)
            recipient.process.notify(DONE)
            logging.error("made a succesful offer with msg %s,%s"%(type(self.msg),self.msg))
            return True
        return False


class Channel:
    """ Channel class. Blocking communication
    
    >>> from __init__ import *

    >>> @process
    ... def WrapP():
    ...     @process
    ...     def P1(cout):
    ...         while True:
    ...             cout('Hello World')
    ...
    ...     C = Channel()
    ...     Spawn(P1(OUT(C)))
    ...
    ...     cin = IN(C)
    ...     print cin()
    ...
    ...     retire(cin)

    >>> Parallel(WrapP())
    Hello World
    """

    def __init__(self, name=None):

        if name == None:
            # Create name based on host ID and current time
            import uuid
            name = str(uuid.uuid1())

        self.name=name

        self.readqueue = []
        self.writequeue = []
        
        # Count, makes sure that all processes knows how many channel ends have retired
        self.readers = 0
        self.writers = 0

        self.ispoisoned = False
        self.isretired = False

        self.s = Scheduler()
        #logging.warning("init greenletsChannel %s"%self.s)
        
    def check_termination(self): 
        logging.debug("check_termnation. %s"%self)       
        if self.ispoisoned:
            logging.debug("will raise poison exception")
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()
            

    def _read(self):
        #logging.warning("greenlets _read")
        self.check_termination()

        p = self.s.current
        # If anyone is on the writequeue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        #for w in self.writequeue:
        #    if w.process.state == ACTIVE:
        #        msg = w.msg
        #        w.result = SUCCESS
        #        w.process.state = DONE
        #        if p != w.process:
        #            self.s.activate(w.process)
        #        return msg        

        p.setstate(ACTIVE)
        req = ChannelReq(p)
        self.post_read(req)
        req.process.wait()
        self.remove_read(req)
        if req.result==SUCCESS:
          logging.warning("got success in channel read")
          return req.msg
        
        self.check_termination()
            
        print 'We should not get here in read!!!'
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.check_termination()

        p = self.s.current
        #logging.warning("\n\n\nself.s %s, \nprocess is %s"%(self.s,p))
        # If anyone is on the readqueue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        #for r in self.readqueue:
        #    if r.process.state == ACTIVE:
        #        r.msg = msg
        #        r.result = SUCCESS
        #        r.process.state = DONE
        #        if p != r.process:
        #            self.s.activate(r.process)
        #        return True
        p.setstate(ACTIVE)
        req = ChannelReq(p,msg=msg)
        self.post_write(req)
        req.process.wait()
        self.remove_write(req)

        if req.result==SUCCESS:
            logging.warning("got succes in channel, write")
            return True
    
        self.check_termination()

        print 'We should not get here in write!!!'
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        logging.warning("greenlets post_read")
        self.check_termination()
        self.readqueue.append(req)
        self.match()

    def remove_read(self, req):
        logging.warning("greenlets remove_read")
        self.readqueue.remove(req)
        
    def post_write(self, req):
        self.check_termination()
        self.writequeue.append(req)
        self.match()

    def remove_write(self, req):
        logging.warning("greenlets remove_write")
        self.writequeue.remove(req)

    def match(self):
        logging.warning("in match read: %d, write: %d"%(len(self.readqueue),len(self.writequeue)))
        if self.readqueue and self.writequeue:
            for w in self.writequeue:
                for r in self.readqueue:
                    #logging.warning("in loop")
                    if w.offer(r):
                        logging.warning("made succesful match")
                        # Did an offer
                        # We can guarantee, that there will always be someone to call offer,
                        # since everything is run in a single thread. Thus we break the loop.
                        return

    def poison(self):
        logging.debug("poison channel")
        if not self.ispoisoned:
            logging.debug("channel was not poisoned") 
            self.ispoisoned = True
            map(ChannelReq.poison, self.readqueue)
            map(ChannelReq.poison, self.writequeue)
        import sys, traceback
        #traceback.print_exc(file=sys.stdout)
        #traceback.print_stack()
        logging.debug("done poison")
        

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def reader(self):
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        if not self.isretired:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.isretired = True
                for p in self.writequeue[:]:
                    p.retire()

    def leave_writer(self):
        if not self.isretired:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.isretired = True
                for p in self.readqueue[:]: # ATOMIC copy
                    p.retire()

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
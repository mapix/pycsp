"""
Alternation module

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
import inspect
import types
from channel import *

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Decorators
def choice(func):
    """
    Decorator for creating choice objets
    
    >>> from __init__ import *
    >>> @choice
    ... def action(__channel_input=None):
    ...     print 'Hello'

    >>> from guard import Skip
    >>> Alternation([{Skip():action()}]).execute()
    Hello
    """
    # __choice_fn func_name used to identify function in Alternation.execute
    def __choice_fn(*args, **kwargs):
        return Choice(func, *args, **kwargs)
    return __choice_fn

# Classes
class Choice:
    """ Choice(func, *args, **kwargs)
    It is recommended to use the @choice decorator, to create Choice instances
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def invoke_on_input(self, __channel_input):
        self.kwargs['__channel_input'] = __channel_input
        self.fn(*self.args, **self.kwargs)
        del self.kwargs['__channel_input']

    def invoke_on_output(self):
        self.fn(*self.args, **self.kwargs)


class RealAlternation:
    """
    RealAlternation is the Alternation object that handles synchronization
    at the channel server daemon.
    """

    def __init__(self, guards):
        self.guards=guards

    def choose(self):
        req_status=ReqStatus()
        reqs={}
        try:
            idx = 0
            for prio_item in self.guards:
                c, op, msg = prio_item
                if op==WRITE:
                    req=ChannelReq(req_status,msg=msg)
                    c.post_write(req)
                else:
                    req=ChannelReq(req_status)
                    c.post_read(req)
                reqs[req]=(idx, c, op)
                idx += 1

        except (ChannelPoisonException, ChannelRetireException) as e:
            for req in reqs.keys():
                _, c, op = reqs[req]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise e

        # If noone have offered a channelrequest, we wait.
        req_status.cond.acquire()
        if req_status.state==ACTIVE:
            req_status.cond.wait()
        req_status.cond.release()

        act=None
        poison=False
        retire=False
        for req in reqs.keys():
            _, c, op = reqs[req]
            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)
            if req.result==SUCCESS:
                act=req
            elif req.result==POISON:
                poison=True
            elif req.result==RETIRE:
                retire=True

        if poison:
            raise ChannelPoisonException()
        if retire:
            raise ChannelRetireException()

        idx, c, op = reqs[act]
        return (idx, act, c, op)



# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
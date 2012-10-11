"""
PyCSP implementation of the CSP Core functionality (Channels, Processes, PAR, ALT).

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports

from guard import Skip, SkipGuard, Timeout, TimeoutGuard
from alternation import choice, Alternation
from altselect import FairSelect, AltSelect, InputGuard, OutputGuard
from channel import Channel, retire, poison
from process import Process, process, Sequence, Parallel, Spawn, current_process_id, init, shutdown
from multiprocess import MultiProcess, multiprocess
from exceptions import ChannelRetireException, ChannelPoisonException, ChannelSocketException, FatalException
from configuration import *
from compat import *

version = (0,8,0, 'sockets')

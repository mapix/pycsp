"""
Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>
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
from common import *

@process
def Prefix(cin, cout, prefix):
    cout(prefix)
    while True:
        cout(cin())

@process
def Delta2(cin, cout1, cout2):
    while True:
        msg = cin()
        Alternation([{
            (cout1,msg):'cout2(msg)',
            (cout2,msg):'cout1(msg)'
            }]).execute()

@process
def Plus(cin1, cin2, cout):
    while True:
        cout(cin1() + cin2())

@process
def Tail(cin, cout):
    dispose = cin()
    while True:
        cout(cin())

@process
def Pairs(cin, cout):
    pA, pB, pC = Channel('pA'), Channel('pB'), Channel('pC')
    Parallel(
        Delta2(cin, -pA, -pB),
        Plus(+pA, +pC, cout),
        Tail(+pB, -pC)
    )
    
@process
def Printer(cin, limit):
    for i in xrange(limit):
        print cin(),
    poison(cin)

A = Channel('A')
B = Channel('B')
C = Channel('C')
D = Channel('D')
printC = Channel()

Parallel(
    Prefix(+B, -A, prefix=0),
    Prefix(+C, -B, prefix=1),
    Pairs(+D, -C),
    Delta2(+A, -D, -printC),
    Printer(+printC, limit=20)
)


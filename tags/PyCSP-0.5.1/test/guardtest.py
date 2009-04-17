from common import *
from pycsp import *
import time
import random

@io
def sleep_long():
    time.sleep(2)

@io
def sleep_random():
    time.sleep(random.random()/2)

@io
def sleep_long_random():
    time.sleep(random.random()*2)


@process
def writer(cout, id, cnt, sleeper):
    for i in range(cnt):
        if sleeper: sleeper()
        cout((id, i))

@process
def par_reader_skip_sel(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:'', cin2:''},{Skip():''},{cin3:'', cin4:''}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c ,'got',msg
    retire(cin1, cin2, cin3, cin4)

@process
def par_reader_timeout_sel(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:'', cin2:''},{cin3:'', cin4:''},{Timeout(0.1):''}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        c,msg = alt.select()
        print 'From ',c ,'got',msg
    retire(cin1, cin2, cin3, cin4)

@process
def par_reader_skip_exec(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:"print 'From cin1 got', ChannelInput",
                        cin2:"print 'From cin2 got', ChannelInput"},
                       {Skip():"print 'Skip'"},
                       {cin3:"print 'From cin3 got', ChannelInput",
                        cin4:"print 'From cin4 got', ChannelInput"}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        alt.execute()
    retire(cin1, cin2, cin3, cin4)

@process
def par_reader_timeout_exec(cin1,cin2,cin3,cin4, cnt, sleeper):
    alt = Alternation([{cin1:"print 'From cin1 got', ChannelInput",
                        cin2:"print 'From cin2 got', ChannelInput"},
                       {cin3:"print 'From cin3 got', ChannelInput",
                        cin4:"print 'From cin4 got', ChannelInput"},
                       {Timeout(seconds=0.1):"print 'Timeout(seconds=0.1)'"}])
    for i in range(cnt*4):
        if sleeper: sleeper()
        alt.execute()
    retire(cin1, cin2, cin3, cin4)


def Any2One_Alting_Test(par_reader, read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_reader(IN(c1),IN(c2),IN(c3),IN(c4),cnt, read_sleeper),
             writer(OUT(c1),0,cnt, write_sleeper),
             writer(OUT(c2),1,cnt, write_sleeper),
             writer(OUT(c3),2,cnt, write_sleeper),
             writer(OUT(c4),3,cnt, write_sleeper))


def Any2Any_Alting_Test(par_reader, read_sleeper, write_sleeper):
    c=Channel('C')

    cnt = 10
    
    Parallel(par_reader(IN(c),IN(c),IN(c),IN(c),cnt, read_sleeper),
             writer(OUT(c),0,cnt, write_sleeper),
             writer(OUT(c),1,cnt, write_sleeper),
             writer(OUT(c),2,cnt, write_sleeper),
             writer(OUT(c),3,cnt, write_sleeper))



print "Any2One_Alting_Test(par_reader_skip_sel, sleep_random, sleep_random)"
Any2One_Alting_Test(par_reader_skip_sel, sleep_random, sleep_random)

print "Any2One_Alting_Test(par_reader_timeout_sel, sleep_random, sleep_long_random)"
Any2One_Alting_Test(par_reader_timeout_sel, sleep_random, sleep_long_random)

print "Any2One_Alting_Test(par_reader_skip_exec, sleep_random, sleep_random)"
Any2One_Alting_Test(par_reader_skip_exec, sleep_random, sleep_random)

print "Any2One_Alting_Test(par_reader_timeout_exec, sleep_random, sleep_long_random)"
Any2One_Alting_Test(par_reader_timeout_exec, sleep_random, sleep_long_random)

print "Any2Any_Alting_Test(par_reader_skip_sel, None, sleep_long)"
Any2Any_Alting_Test(par_reader_skip_sel, None, sleep_long)

print "Any2Any_Alting_Test(par_reader_timeout_sel, None, sleep_long)"
Any2Any_Alting_Test(par_reader_timeout_sel, None, sleep_long)

        

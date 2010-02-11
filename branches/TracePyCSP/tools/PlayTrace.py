"""
Play a trace of a PyCSP application

Usage:
  python PlayTrace.py <trace file>

Requires:
  Graphviz
  wxPython 2.8+
  PyCSP

The DrawFrame class has been based on the FloatCanvas.py demo from the wxPython
package written by Chris Barker <Chris.Barker@noaa.gov>.

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

import wx
import subprocess, time, random
import cStringIO
from pycsp_import import *
#from pycsp.common.trace import *
from pycsp.common import toolkit

#TraceInit('tracer.trace')

DOT = toolkit.which('dot')

STATE_INIT, STATE_BLOCKED, STATE_RUNNING = range(3)
READ, WRITE = range(2)

def DOT_ID(id):
    new_id = id.translate(None, ". <>")
    return "node_"+new_id

class MainFrame(wx.Frame):
    def __init__(self, parent, title, pos):
        wx.Frame.__init__(self, parent, -1, title,
                          pos, size=(700, 700))

        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu 
        menu = wx.Menu()

        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit!")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.Shutdown, id=wx.ID_EXIT)

        # and put the menu on the menubar
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar()
        

        # Now create the Panel to put the other controls on.
        panel = wx.Panel(self)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.stateBtnPlay = 'pause'
        self.btnPlay = wx.Button(panel, wx.ID_NEW, "Play Trace", (215,48), (100,30))
        self.Bind(wx.EVT_BUTTON, self.OnPlayTrace, self.btnPlay)

        self.delay = wx.Slider(
            panel, 1000, 25, 1, 1000, (30, 60), (200, -1), 
            wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )
        
        self.btnStep = wx.Button(panel, wx.ID_OK, "Step Trace", (215,48), (100,30))
        self.Bind(wx.EVT_BUTTON, self.OnStepTrace, self.btnStep)

        # bind the button events to handlers
        topSizer.Add(self.btnPlay, 1, wx.ALL | wx.EXPAND, 1)
        topSizer.Add(self.delay, 1 , wx.EXPAND | wx.ALL, 1)  
        topSizer.Add(self.btnStep, 1 , wx.EXPAND | wx.ALL, 1)
        

        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topSizer)

        # Create ImagePanel
        self.ImagePanel = wx.Window(panel, -1,
                                    style=wx.SUNKEN_BORDER)
        self.ImagePanel.SetBackgroundColour(wx.WHITE)
        self.ImagePanel.Bind(wx.EVT_PAINT, self.OnPaintEvent)

        sizer.Add(self.ImagePanel, 5, wx.EXPAND | wx.ALL, 5)

        # Create MsgWindow
        self.MsgWindow = wx.TextCtrl(panel, wx.ID_ANY,
                                     "Look Here for output\n",
                                     style = (wx.TE_MULTILINE |
                                              wx.TE_READONLY |
                                              wx.SUNKEN_BORDER)
                                     )
        sizer.Add(self.MsgWindow, 1, wx.EXPAND | wx.ALL, 5)
        
        # Set auto layout
        panel.SetAutoLayout(True)
        panel.SetSizer(sizer)

        wx.CallLater(1, self.UpdateScreenSize)

        self.get_image = +IMAGE_FILE_CHAN
        self.setup_dotfile = -DOTFILE_SETUP_CHAN
        self.setup_dotcmd = -DOTCMD_SETUP_CHAN        
        self.OnUpdate()
                
    def OnPaintEvent(self, event):
        """ Respond to a request to redraw the contents of our drawing panel.
        """
        self.UpdateScreenSize()
    
    def Log(self, text):
        self.MsgWindow.AppendText(text)

    def UpdateScreenSize(self):
        try:
            self.setup_dotfile(('size',self.ImagePanel.GetSize()))        
        except ChannelPoisonException:
            return

    def OnStepTrace(self, event):
        pass

    def OnPlayTrace(self, event):
        if self.stateBtnPlay == 'pause':
            self.stateBtnPlay = 'play'
            self.btnPlay.SetLabel('Pause Trace')
            self.btnStep.Enabled = False

            #self.onPlayTrace2()
        else:
            self.stateBtnPlay = 'pause'
            self.btnPlay.SetLabel('Play Trace')
            self.btnStep.Enabled = True

    def OnUpdate(self):
        
        # Try to fetch new image
        try:
            g, update = Alternation([(self.get_image, None), (Skip(), None)]).select()
        except ChannelPoisonException:
            return

        # Got image
        if g == self.get_image:
            
            img, trace_output = update

            # Print traced stdout
            if trace_output:
                self.Log("".join(trace_output))

            # Convert image
            stream = cStringIO.StringIO(img)
            bmp = wx.BitmapFromImage( wx.ImageFromStream( stream ))

            # Draw converted image
            dc = wx.PaintDC(self.ImagePanel)
            dc.Clear()
            dc.BeginDrawing()
            x, y = 0, 0
            w, h = self.ImagePanel.GetClientSize()
            dc.DrawBitmap(bmp, x + (w - bmp.GetWidth()) / 2,
                          y + (h - bmp.GetHeight()) / 2, True)
            dc.EndDrawing()

        # Setup 10 ms. delay to handle GUI
        wx.CallLater(self.delay.Value, self.OnUpdate)

    def Shutdown(self, evt):
        """Event handler for shutting down."""
        poison(self.get_image)
        self.Close()
        

class MainApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, "PyCSP Trace Visualizer",wx.DefaultPosition)
        self.SetTopWindow(frame)

        frame.Show(True)
        return True

class TracedChannel():
    def __init__(self, chan_name):
        self.chan_name = chan_name
        self.dot_id = 'chan_'+DOT_ID(str(random.random()) + str(time.time()))

        self.reading = {}
        self.writing = {}

        self.diamond_location = None

    def update_diamond_location(self):

        if self.diamond_location == None:
            parent_count = {}
            for a in self.reading:
                parent, p = a
                if parent_count.has_key(parent):
                    parent_count[parent] += 1
                else:
                    parent_count[parent] = 1

            for b in self.writing:
                parent, p = b
                if parent_count.has_key(parent):
                    parent_count[parent] += 1
                else:
                    parent_count[parent] = 1
            
            max = (0,0)
            for parent, count in parent_count.items():
                if count > max[1]:
                    max = (parent, count)

            if max != (0,0):
                self.diamond_location = max[0]
            

    def update(self, parent_process_id, process_id, _type):
        
        # Reset
        self.diamon_location = None

        update_data = self.writing 
        if _type == READ:
            update_data = self.reading

        key = (parent_process_id, process_id)
        if update_data.has_key(key):
            update_data[key] += 1
        else:
            update_data[key] = 1
            
        # Set active
        if int(update_data[key]) == update_data[key]:
             update_data[key] += 0.5

    def try_insert_diamond(self, parent_process_id):

        if len(self.reading) == 1 and len(self.writing) == 1:
            return None
        elif len(self.reading) >= 1 and len(self.writing) >= 1:
            
            # Update
            self.update_diamond_location()
        
            if parent_process_id == self.diamond_location:
                return self.dot_id + " [label=\"\", shape=diamond, width=0.2, height=0.2];"
            else:
                return None

    def to_dot(self):
        
        if len(self.reading) == 1 and len(self.writing) == 1:
            cin_id = self.reading.keys()[0]
            cout_id = self.writing.keys()[0]

            # test active
            active = ""
            if int(self.writing[cout_id]) != self.writing[cout_id]:
                self.writing[cout_id] -= 0.5
                active = ",color=blue"
            if int(self.reading[cin_id]) != self.reading[cin_id]:
                self.reading[cin_id] -= 0.5
                active = ",color=blue"            

            return [DOT_ID(cout_id[1]) + " -> " + DOT_ID(cin_id[1]) + " [weight="+str(self.writing[cout_id])+""+active+"];"]
        elif len(self.reading) >= 1 and len(self.writing) >= 1:
            contents = []
            for cout_id in self.writing:
                
                # test active
                active = ""
                if int(self.writing[cout_id]) != self.writing[cout_id]:
                    self.writing[cout_id] -= 0.5
                    active = ",color=blue"

                contents.append(DOT_ID(cout_id[1]) + " -> " + self.dot_id + " [weight="+str(self.writing[cout_id])+""+active+"];")

            for cin_id in self.reading:

                # test active
                active = ""
                if int(self.reading[cin_id]) != self.reading[cin_id]:
                    self.reading[cin_id] -= 0.5
                    active = ",color=blue"

                contents.append(self.dot_id + " -> " + DOT_ID(cin_id[1]) + " [weight="+str(self.reading[cin_id])+""+active+"];") 

            return contents
        else:
            return []

class TracedProcess():
    def __init__(self, id, func_name):
        self.id = id
        self.func_name = func_name
        self.processes = []
        self.parent = None

        # STATE_INIT, STATE_BLOCKED, STATE_RUNNING
        self.state = STATE_INIT
        self.state_msg = ""

        # Used to perform cleanup, when removing process
        self.channels = []

    def talking_to(self, chan):
        if not chan in self.channels:
            self.channels.append(chan)
            
    def silence(self):
        for chan in self.channels:
            if chan.reading.has_key(self.id):
                chan.reading.pop(self.id)
            if chan.writing.has_key(self.id):
                chan.writing.pop(self.id)
        self.channels = []
            

    def to_dot(self, l=1):
        msg = ""
        if self.state_msg != "":
            msg = " ("+self.state_msg+")"

        if self.processes:
            contents = []
            contents.append("\t"*l + "subgraph cluster_"+DOT_ID(self.id)+" {")
            contents.append("\t"*(l+1) + "label=\""+self.func_name+msg+"\";")
            contents.append("\t"*(l+1) + "style=filled;")
            if self.state == STATE_BLOCKED:                
                contents.append("\t"*(l+1) + "fillcolor=\"gray\";")
            else:
                contents.append("\t"*(l+1) + "fillcolor=\"white\";")
            contents.append("\t"*(l+1) + DOT_ID(self.id)+" [width=0.3, height=0.3, style=invis, label=\"\"];")
            for p in self.processes:
                contents.extend(p.to_dot(l+1))

                for chan in p.channels:
                    diamond_node = chan.try_insert_diamond(self.id)
                    if diamond_node != None:
                        contents.append(diamond_node)

            contents.append("\t"*l + "}")
        
            return contents
        else:
            if self.state == STATE_BLOCKED:
                return ["\t"*l + DOT_ID(self.id) + " [label=\""+self.func_name+msg+"\", style=filled, fillcolor=\"gray\"];"]
            else:
                return ["\t"*l + DOT_ID(self.id) + " [label=\""+self.func_name+msg+"\", style=filled, fillcolor=\"white\"];"]

@process
def GenerateDotFiles(get_objects, send_objects, send_dotfile, get_setup):
    trace_output = []
    trace_processes = {}
    trace_channels = {}

    size = (6,6)

    while True:
        send_objects((trace_processes, trace_channels, trace_output))
        (trace_processes, trace_channels, trace_output, CHANGE_LEVEL) = get_objects()        
        if CHANGE_LEVEL > 1:
            
            next = False
            while (not next):

                new_dot_file_1 = "digraph G {\nsize=\""+str(size[0])+","+str(size[1])+"\";\n"

                contents = []

                if trace_processes.has_key('__main__'):
                    contents.extend(trace_processes['__main__'].to_dot())

                for chan in trace_channels.values():
                    contents.extend(chan.to_dot())

                new_dot_file_2 = "\n}"

                g, cmd = Alternation([
                            (send_dotfile, (new_dot_file_1 + "\n".join(contents) + new_dot_file_2, trace_output), None),
                            (get_setup, None)
                            ]).select()

                if (g == send_dotfile):
                    next = True
                    trace_output = []

                elif (g == get_setup):                    
                    if cmd[0] == 'size':
                        size = (int(cmd[1][0] / 96), int(cmd[1][1] / 96))
                
                    

@process
def RunDotParser(get_dotfile, send_image, get_setup):
    while True:
        dotfile, trace_output = get_dotfile()
        while (dotfile != None):
            p = subprocess.Popen((DOT, '-Tpng'), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            pngfile, _ = p.communicate(dotfile)

            g, cmd = Alternation([
                    (send_image,(pngfile, trace_output), None),
                    (get_setup,None)
                    ]).select()
            if g == send_image:            
                dotfile = None

            elif g == get_setup:
                if cmd[0] == 'zoom':
                    pass
                    
            
        
        

@process
def UpdateTrace(get_trace, get_objects, send_objects):
    while True:
        try:
            tracelist = get_trace()
        except ChannelRetireException:
            poison(get_objects)
            return

        # Parse..
        for trace in tracelist:
            trace = eval(trace)

            #print trace

            (trace_processes, trace_channels, trace_output) = get_objects()

            try:
                CHANGE_LEVEL = 0
                if trace['type'] == 'Output':
                    trace_output.append(trace['msg'])
                    CHANGE_LEVEL = 1

                elif trace['type'] == 'Msg':
                    p = trace_processes[trace['process_id']]
                    p.state_msg = 'msg:'+trace['msg']
                    
                    CHANGE_LEVEL = 2
                elif trace['type'] == 'BlockOnParallel':
                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.processes.append(p)
                        p.parent = parent

                    parent.state = STATE_BLOCKED
                    parent.state_msg = 'Parallel'
                    CHANGE_LEVEL = 3
                elif trace['type'] == 'BlockOnSequence':
                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.processes.append(p)
                        p.parent = parent

                    parent.state = STATE_BLOCKED
                    parent.state_msg = 'Sequence'
                    CHANGE_LEVEL = 3
                elif trace['type'] == 'Spawn':
                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.processes.append(p)
                        p.parent = parent

                    CHANGE_LEVEL = 3
                elif trace['type'] == 'QuitProcess':
                    proc = trace_processes.pop(trace['process_id'])

                    proc.silence()

                    if proc.parent != None:                        
                        proc.parent.processes.remove(proc)
                    
                    CHANGE_LEVEL = 3
                elif trace['type'] == 'DoneParallel':
                    parent = trace_processes[trace['process_id']]

                    parent.state = STATE_RUNNING
                    parent.state_msg = ''

                    CHANGE_LEVEL = 2
                elif trace['type'] == 'DoneSequence':
                    parent = trace_processes[trace['process_id']]

                    parent.state = STATE_RUNNING
                    parent.state_msg = ''

                    CHANGE_LEVEL = 2
                elif (trace['type'] == 'BlockOnRead' or 
                      trace['type'] == 'BlockOnWrite'):
                    trace_processes[trace['process_id']].state = STATE_BLOCKED

                    if not trace_channels.has_key(trace['chan_name']):
                        trace_channels[trace['chan_name']] = TracedChannel(trace['chan_name'])                    

                    chan = trace_channels[trace['chan_name']]
                    p = trace_processes[trace['process_id']]

                    if trace['type'] == 'BlockOnRead':
                        chan.update(p.parent.id, p.id, READ) 
                    else:
                        chan.update(p.parent.id, p.id, WRITE) 

                    p.talking_to(chan)

                    CHANGE_LEVEL = 3   
                elif (trace['type'] == 'DoneRead' or
                      trace['type'] == 'DoneWrite'):
                    trace_processes[trace['process_id']].state = STATE_RUNNING
                    CHANGE_LEVEL = 2
                elif (trace['type'] == 'BlockOnAlternation.execute' or
                      trace['type'] == 'BlockOnAlternation.select'):
                    trace_processes[trace['process_id']].state = STATE_BLOCKED
                    CHANGE_LEVEL = 2
                elif (trace['type'] == 'DoneAlternation.execute' or
                      trace['type'] == 'DoneAlternation.select'):
                    trace_processes[trace['process_id']].state = STATE_RUNNING
                    guard = trace['guard']

                    _type = None
                    if guard['type'] == 'ReadGuard':
                        _type = READ
                    elif guard['type'] == 'WriteGuard':
                        _type = WRITE

                    if _type != None:

                        if not trace_channels.has_key(guard['chan_name']):
                            trace_channels[guard['chan_name']] = TracedChannel(guard['chan_name'])

                        chan = trace_channels[guard['chan_name']]
                        p = trace_processes[trace['process_id']]

                        chan.update(p.parent.id, p.id, _type)
                        p.talking_to(chan)

                    CHANGE_LEVEL = 3
            except Exception, e:
                print 'KeyError', e
            send_objects((trace_processes, trace_channels, trace_output, CHANGE_LEVEL ))


if len(sys.argv) > 1:
    TRACE_FILE = sys.argv[1]
    DOT_FILE_CHAN = Channel('Dot')
    IMAGE_FILE_CHAN = Channel('Image')
    DOTFILE_SETUP_CHAN = Channel('DotFileSetup')
    DOTCMD_SETUP_CHAN = Channel('DotCmdSetup')    
    TRACE_FILE_CHAN = Channel('TraceFile')
    TRACE_OBJECTS_CHAN = Channel('TraceObjects')

    Spawn(
        toolkit.file_r(-TRACE_FILE_CHAN, TRACE_FILE),
        UpdateTrace(+TRACE_FILE_CHAN, +TRACE_OBJECTS_CHAN, -TRACE_OBJECTS_CHAN),
        GenerateDotFiles(+TRACE_OBJECTS_CHAN, -TRACE_OBJECTS_CHAN, -DOT_FILE_CHAN, +DOTFILE_SETUP_CHAN),
        RunDotParser(+DOT_FILE_CHAN, -IMAGE_FILE_CHAN, +DOTCMD_SETUP_CHAN)
        )
    
    app = MainApp(redirect=False)
    app.MainLoop()

else:
    print __doc__
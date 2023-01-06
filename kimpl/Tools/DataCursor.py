
import matplotlib.pyplot as plt
import matplotlib
from numpy import argmin
from PyQt5.QtWidgets import QAction,QMenu
from PyQt5.QtCore import QPoint

class DataCursor:
    """Add Cursor to an existing plot and data set
        
        ax : matplotlib.axes._subplots.AxesSubplot
            Add a matplotlib axis to associate the cursor to.
        dataline : matplotlib.lines.Line2D or None
            Any matplotlib line, if none is specified, then the cursor will automatically be
            assigned to the last plotted line if there is one. If not, the cursor will not
            be assigned a line.
        datalock : bool
            datalock allows you to lock a cursor to a specific line of data. Right click
            will give the option to turn off the datalock.
        snap : bool
            snap causes the cursor to snap to a data point if the cursor is close to a line.
            Right click will give the option to turn off the snap.
            
        **kwargs
        
        xlock: bool, when True, stops x coordinate from changing during dragging
        ylock: bool, when True stops y coordinate from changing during dragging
        label_vis: bool, when False, no label is displayed
        color: str, when blank, default color is black
        xy: tuple, (x,y), used when no dataline is given, sets default position
        
        dataline is assigned whenever a cursor gets close to a line on the plot, this is
        evident by a color change in the cursor. You can lock onto that line by right
        clicking and setting datalock. If you select snap in the context menu, you will
        snap to points on the line but will not lock onto the line.
        
        A cursor becomes active when it is either created or clicked on. When it is active
        you can move it by pressing right or left. The stepsize can be changed by calling
        self.setShiftSize(n) #n is an integer
    """
    def __init__(self,ax=None,dataline=None,datalock=False,snap=True,label='',**kwargs):
        if ax==None:
            self.ax=plt.gca()
        else:
            self.ax=ax
        if 'cursors' not in self.ax.__dict__:  #add a list of cursors, like the lines, legends, images etc. for axes properties
            self.ax.cursors=[]
        if 'right' in matplotlib.rcParams['keymap.forward']:
            matplotlib.rcParams['keymap.forward'].remove('right')  #overwrites what right and left on the keyboard do
            matplotlib.rcParams['keymap.back'].remove('left')  #I don't feel bad about doing this because there are still v for forward and c,backspace for back
        templines=list(self.ax.lines).copy()
        for i in self.ax.cursors:
            templines.remove(i.line)
        if dataline!=None:
            self.dataline=dataline
        elif len(templines)>0:
            self.dataline=templines[-1]
        else:
            datalock=False
            self.dataline=None
        self.fig=self.ax.figure
        self.canvas=self.fig.canvas
        if self.dataline!=None:
            tempx,tempy=self.dataline.get_data()
            self.x,self.y=tempx[0],tempy[0]
            self.color=self.dataline.get_color()
            self.d=0
        else:
            self.x,self.y=kwargs.pop('xy',(0,0))
            print(self.x,self.y)
            self.color=kwargs.pop('color','black')
        self.line,=self.ax.plot(self.x,self.y,'x',markersize=8.0,color=self.color)
        self.ax.cursors.append(self)
        if label!='':
            self.label=label+", "
        else:
            self.label=label
        self.text=self.ax.annotate("{:s}{:g},{:g}".format(self.label,self.x,self.y),(self.x,self.y),(10,10),textcoords='offset pixels',fontsize=8,visible=kwargs.pop('label_vis',True))
        self.datalock=datalock
        self.snap=snap
        self.xlock=kwargs.pop('xlock',False)
        self.ylock=kwargs.pop('ylock',False)
        self.clicked=False
        self.active=False #for comparison with other cursors
        self.shiftsize=1  #number of steps for right and left button presses
        self.ContextMenu()
        self.connect()
        
    def set_label_visible(self,val=True):
        self.text.set_visible(val)
        
    def set_position(self,x,y):
        self.x,self.y=x,y
        self._move()
        
    def get_position(self):
        return self.x,self.y
    
    def set_lock(self,axis='x',val=False):
        if axis=='x':
            self.xlock=val
        elif axis=='y':
            self.ylock=val
        elif axis=='both':
            self.xlock=val
            self.ylock=val
            
        
    def connect(self):
        self.cid=[]
        for i,j in zip(['button_press_event','motion_notify_event','button_release_event','button_press_event'],[
                self.on_click,self.on_motion,self.on_release,self.open_ContextMenu]):
            self.cid.append(self.canvas.mpl_connect(i,j))
        self.connect_bpress()
        
    def disconnect(self):
        for i in self.cid:
            self.canvas.mpl_disconnect(i)
        self.disconnect_bpress()
        
    def connect_bpress(self):
        for i in self.ax.cursors:
            if i.active:
                i.active=False
                i.canvas.mpl_disconnect(i.cidactive)
        self.active=True
        self.cidactive=self.canvas.mpl_connect('key_press_event',self.button_press)
    
    def disconnect_bpress(self):
        self.active=False
        self.canvas.mpl_disconnect(self.cidactive)
        
    def get_background(self):
        self.bg=self.canvas.copy_from_bbox(self.ax.bbox)
        
    def draw_clear(self):
        self.canvas.restore_region(self.bg)
        
    def redraw(self):
        self.ax.draw_artist(self.line)
        self.ax.draw_artist(self.text)
        self.canvas.blit(self.ax.bbox)
        
        
    def on_click(self,event):
        if event.inaxes!=self.ax: return
        if event.button!=1: return
        if self.canvas.toolbar.mode!='': return
        contains,attrd=self.line.contains(event)
        if not contains: return
        self.clicked=True
        tempcursors=self.ax.cursors.copy()
        temp=[i.clicked for i in tempcursors].index(True)
        for i in tempcursors[temp+1:]:
            i.clicked=False
        if not self.clicked: return
        if not self.active:
            self.connect_bpress()
        
        self.line.set_animated(True)
        self.text.set_animated(True)
        self.datalines=list(self.ax.lines).copy()
        for i in self.ax.cursors:
            self.datalines.remove(i.line)
        self.ax.figure.canvas.draw()
        self.get_background()
        self.redraw()
    
    def on_motion(self,event):
        if (not self.clicked) or (event.inaxes!=self.ax): return
        if not self.xlock:
            self.x=event.xdata
        if not self.ylock:
            self.y=event.ydata
        
        self.event=event
        self._dragmove()
        self.draw_clear()
        self.redraw()
        
    def _dragmove(self):
        if self.datalock:
            tempx,tempy=self.dataline.get_data()
            self.d=argmin((tempx-self.x)**2+(tempy-self.y)**2)
            self.x,self.y=tempx[self.d],tempy[self.d]
        else:
            contains=[i.contains(self.event)[0] for i in self.datalines]
            try:
                arg=contains.index(True)
                self.dataline=self.datalines[arg]
                if self.snap:
                    tempx,tempy=self.dataline.get_data()
                    self.d=argmin((tempx-self.x)**2+(tempy-self.y)**2)
                    self.x,self.y=tempx[self.d],tempy[self.d]
                self.color=self.dataline.get_color()
            except ValueError:
                self.dataline=None
                self.color='black'
        self._move()
    def _move(self):
        self.line.set_color(self.color)
        self.line.set_data(self.x,self.y)
        self.text.xy=(self.x,self.y)
        self.text.set_text("{:s}{:g},{:g}".format(self.label,self.x,self.y))
        
    def on_release(self,event):
        self.clicked=False
        if self.dataline==None:
            self.active=False
            self.disconnect_bpress()
        self.line.set_animated(False)
        self.text.set_animated(False)
        self.canvas.draw()
        
    def button_press(self,event):
        if self.dataline!=None:
            if event.key=='right':
                shift=self.shiftsize
            elif event.key=='left':
                shift=-self.shiftsize
            else:
                return
            tempx,tempy=self.dataline.get_data()
            self.d=max(min((self.d+shift),tempx.shape[0]-1),0) #ensures d stays in bounds
            self.x,self.y=tempx[self.d],tempy[self.d]
            self._move()
            self.fig.canvas.draw()
        
    def open_ContextMenu(self,event):
        if event.inaxes!=self.ax: return
        if event.button!=3: return
        if self.canvas.toolbar.mode!='': return
        contains,attrd=self.line.contains(event)
        if not contains: return
        self.cmenu.exec(self.canvas.mapToGlobal(QPoint(event.x,self.canvas.geometry().height()-event.y)))
        
    def ContextMenu(self):
        self.cmenu=QMenu(self.canvas)
        self.cmenu.setToolTipsVisible(True)
        self.actionDatalock=QAction("Datalock",self.cmenu,checkable=True)
        self.actionDatalock.setToolTip("Locks cursor to dataline")
        self.actionDatalock.setChecked(self.datalock)
        self.actionDatalock.triggered.connect(self.fDatalock)
        
        self.actionSnap=QAction("Snap",self.cmenu,checkable=True)
        self.actionSnap.setToolTip("Snaps cursor to data points\nwhen close to line")
        self.actionSnap.setChecked(self.snap)
        self.actionSnap.triggered.connect(self.fSnap)
        
        self.actionRemove=QAction("Remove",self.cmenu)
        self.actionRemove.triggered.connect(self.remove)
        
        self.cmenu.addAction(self.actionDatalock)
        self.cmenu.addAction(self.actionSnap)
        self.cmenu.addAction(self.actionRemove)
    
    def fDatalock(self):
        self.datalock=self.actionDatalock.isChecked()
        if self.dataline==None:
            self.datalock=False
            self.actionDatalock.setChecked(0)
        if self.datalock:
            self.x,self.y=self.text.xy
            self._move()
            self.canvas.draw()
            
    def fSnap(self):
        self.snap=self.actionSnap.isChecked()
        if self.snap:
            self._move()
            self.canvas.draw()
    def setShiftSize(self,n):
        """n : int, set the shift size when pressing right or left"""
        if n>0 and type(n)==int:
            self.shiftsize=n
            
    def remove(self):
        self.disconnect()
        self.ax.lines.remove(self.line)
        self.ax.cursors.remove(self)
        self.ax.texts.remove(self.text)
        self.canvas.draw()
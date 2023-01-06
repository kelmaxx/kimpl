# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 16:39:52 2022

@author: TSM
"""
import numpy as np
import matplotlib as mpl
from .._PlotMod import subplots
import warnings

class DraggableLine:
    lines=[] #list of all draggable lines
    active_line=None #the current line that is being drug
    
    def __init__(self,data,dragaxes=None,dataaxes=None,x=None,y=None,orientation='horizontal',data_orientation='horizontal',**kwargs):
        """
        Draggable line for examining data in 2d arrays along individual axes. Multiple input dragaxes and dataaxes allow the data to be displayed on multiple plots. May be used with linear-log plots. kwargs are passed through to calls of ax.plot()

        Parameters
        ----------
        data : ndarray
            2D array from which data extracted.
        dragaxes : list or ndarray, optional
            List of matplotlib axes where draggable lines are added. If no input is given a new axis is created.
        dataaxes : list or ndarray, optional
            DESCRIPTION. The default is None.
        x : ndarray, optional
            Array of x coordinates with size matching data.shape[1]. The default results in arange(data.shape[1]).
        y : ndarray, optional
            Array of y coordinates with size matching data.shape[0]. The default results in arange(data.shape[0]).
        orientation : str, optional
            Orientation determines axes for extracting data. vertical is axis 0,horizontal is axis 1. The default is 'horizontal'.
        data_orientation : str, optional
            Orientation along which the datalines will be plotted. 'horizontal' is plotted as (x,y), 'vertical' is plotted as (y,x). The default is 'horizontal'.

        """
        if orientation not in ['vertical','horizontal']:
            raise ValueError("orientation must be 'vertical' or 'horizontal'")
        if data_orientation not in ['vertical','horizontal']:
            raise ValueError("data_orientation must be 'vertical' or 'horizontal'")
        if (dragaxes is None) and (dataaxes is None):
            _,(dragaxes,dataaxes)=subplots(1,2) #create a plot if one is not currently available
        elif dragaxes is None:
            _,dragaxes=subplots(1,1)
        elif dataaxes is None:
            _,dataaxes=subplots(1,1)
        if not np.iterable(dragaxes):
            dragaxes=[dragaxes]
        if not np.all((isinstance(ax,mpl.axes.Axes) for ax in dragaxes)):
            raise ValueError("dragaxes must be an instance or iterable of matplotlib axes")
        if not np.iterable(dataaxes):
            dataaxes=[dataaxes]
        if not np.all((isinstance(ax,mpl.axes.Axes) for ax in dataaxes)):
            raise ValueError("dataaxes must be an instance or iterable of matplotlib axes")
            
        
        self.data=data
        self.orientation=orientation
        self.data_orientation=data_orientation #plot as (x,y) or as (y,x)
        self.linekwargs=kwargs #keywords for all of the lines
        
        self.dragaxes=dragaxes
        self.dataaxes=dataaxes
        self.figs=[]
        self.dragfigs=[]
        self.datafigs=[]
        #create list of unique figures to prevent unnecessary drawing
        for i in [i.figure for i in dragaxes]:
            if i not in self.figs: #keep track of all figures associated with axes
                self.figs.append(i)
            if i not in self.dragfigs:
                self.dragfigs.append(i)
        for i in [i.figure for i in dataaxes]:
            if i not in self.figs: #keep track of all figures associated with axes
                self.figs.append(i)
            if i not in self.datafigs:
                self.datafigs.append(i)
        
        
        self.draglines=[]
        self.datalines=[]
        
        self.joined=[self] #list of other draggable lines that can move together with this, used for comparing data sets
        
        self._buildxy(x,y)
        self._addLines()
        self.__class__.lines.append(self)
        
        self.set_self_animated(True)
        self.connect()
        
        
        
            
    def _buildxy(self,x,y):
        """
        Construct 2d x and y arrays whose size match self.data.shape input arrays.

        Parameters
        ----------
        x : ndarray or None
            If None, generated array using self.data.shape[1].
        y : ndarray or None
            If None, generate array using self.data.shape[0].

        Returns
        -------
        None.

        """
        if isinstance(x,np.ndarray) or isinstance(y,np.ndarray):
            self.colormesh=True #determines if the data is plotted as an image or a pcolormesh
        else:
            self.colormesh=False
        yshape,xshape=self.data.shape
        if self.colormesh:
            if x is None:
                x=np.repeat(np.arange(xshape)[np.newaxis],yshape,0)
            if y is None:
                y=np.repeat(np.arange(yshape)[:,np.newaxis],xshape,1)
            if y.ndim==1:
                y=np.repeat(y[:,np.newaxis],xshape,1)
            if x.ndim==1:
                x=np.repeat(x[np.newaxis],yshape,0)
            if (x.ndim==1) and (y.ndim==1):
                x,y=np.meshgrid(x,y)
        if self.colormesh:
            self.x=x #2d array of x coordinates
            self.y=y #2d array of y coordinates
        else:
            self.x=np.repeat(np.arange(xshape)[np.newaxis],yshape,0)
            self.y=np.repeat(np.arange(yshape)[:,np.newaxis],xshape,1)
    
    def _addLines(self):
        for ax in self.dragaxes: #plot draggable line in each drag axis
            self.draglines.append(ax.plot([0,0],[0,0],pickradius=10,**self.linekwargs)[0])
        for ax in self.dataaxes: #plot data line in each data axis
            self.datalines.append(ax.plot([0,0],[0,0],**self.linekwargs)[0])
        if 'color' not in self.linekwargs: #matches color for all lines if none is provided
            idx=0
            line=self.draglines[0]
            for l in self.draglines+self.datalines:
                tidx=l.axes.lines.index(l)
                if tidx>idx:
                    idx=tidx
                    line=l
            self.set_color(line.get_color())
            self.linekwargs['color']=line.get_color()
        midy=int(self.data.shape[0]/2)
        midx=int(self.data.shape[1]/2)
        self.updateLines(self.x[midy,midx],self.y[midy,midx])
        
    def addDataAxis(self,ax,**kwargs):
        linekwargs=self.linekwargs.copy()
        linekwargs.update(kwargs)
        self.dataaxes.append(ax)
        x,y=self.datalines[0].get_data()
        self.datalines.append(ax.plot(x,y,**linekwargs,scalex=False,scaley=False)[0])
        if ax.figure not in self.figs:
            self.figs.append(ax.figure)
            self.datafigs.append(ax.figure)
        xmin,xmax=self.dataaxes[0].get_xlim()
        ymin,ymax=self.dataaxes[0].get_ylim()
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(ymin,ymax)
        
            
    def updateLines(self,xin,yin):
        """
        Update data lines to match the data in the proper axis closest to the point (xin,yin)

        Parameters
        ----------
        xin : float
            data point whose closest index will be extracted from self.x.
        yin : float
            data point whose closest index will be extracted from self.y.

        """
        if self.orientation=='horizontal': #horizontal
            #y=int(max(min(round(event.ydata),self.data.shape[self.dir]-1),0))
            if self.colormesh:
                tempx,tempy,tempz=argmin2d(yin,x2d=self.x,y2d=self.y,z2d=self.data,axis=0,returnalt=True) #find closest x,y, and data coordinates 
            else:
                y=np.argmin(np.abs(yin-self.y[:,0]))
                tempx=self.x[y]
                tempy=self.y[y]
                tempz=self.data[y,:]
            for i in self.draglines:
                i.set_data(tempx,tempy)
            for i in self.datalines:
                if self.data_orientation=='horizontal':
                    i.set_data(tempx,tempz) #update lines
                elif self.data_orientation=='vertical':
                    i.set_data(tempz,tempx)
        elif self.orientation=='vertical': #vertical
            #y=int(max(min(round(event.ydata),self.data.shape[self.dir]-1),0))
            if self.colormesh:
                tempx,tempy,tempz=argmin2d(xin,x2d=self.x,y2d=self.y,z2d=self.data,axis=1,returnalt=True)
            else:
                x=np.argmin(np.abs(xin-self.x[0]))
                tempx=self.x[:,x]
                tempy=self.y[:,x]
                tempz=self.data[:,x]
            for i in self.draglines:
                i.set_data(tempx,tempy)
            for i in self.datalines:
                if self.data_orientation=='horizontal':
                    i.set_data(tempy,tempz)
                elif self.data_orientation=='vertical':
                    i.set_data(tempz,tempy)
    
    def set_color(self,c):
        """
        Sets color of all data and draggable lines to the same.

        Parameters
        ----------
        c : str
            color can match any acceptable input of a line's .set_color method.

        """
        for i in self.draglines:
            i.set_color(c)
        for i in self.datalines:
            i.set_color(c)
            
    def set_label(self,s):
        """
        Sets color of all data and draggable lines to the same.

        Parameters
        ----------
        c : str
            color can match any acceptable input of a line's .set_color method.

        """
        for i in self.draglines:
            i.set_label(s)
        for i in self.datalines:
            i.set_label(s)
                
    def updateData(self,data):
        """
        Load in new data for comparison.

        Parameters
        ----------
        data : ndarray
            2d array of data.

        """
        self.data=data
        tempx=self.draglines[0].get_xdata()[0]
        tempy=self.draglines[0].get_ydata()[0]
        self.updateLines(tempx,tempy)
        
    def duplicate(self,**kwargs):
        """
        Create a second draggable line with matching axes. kwargs is used to update the properties of the lines

        Returns
        -------
        DraggableLine

        """
        linekwargs=self.linekwargs.copy()
        linekwargs.update(kwargs)
        return DraggableLine(self.data,self.dragaxes,self.dataaxes,self.x,self.y,self.orientation,self.data_orientation,**linekwargs)
        
    def set_self_animated(self,b):
        """This is for incorporating the drawing functionality into other code that blit's the image"""
        self.self_animated=b
        self.restore_background=b
        self.blit=b
        
        
    def draw(self,restore_background=None,blit=None):
        if restore_background is None:
            restore_background=self.restore_background
        if blit is None:
            blit=self.blit
            
        if restore_background:
            self.set_background()
                
        for i in self.draglines:
            i.axes.draw_artist(i)
        for i in self.datalines:
            i.axes.draw_artist(i)
            
        if blit:
            self.blit_axes()
        
    def connect(self):
        """Connect actions performed on interface"""
        for i in self.dragfigs:
            i.canvas.mpl_connect('button_press_event',self.fpressed)
            i.canvas.mpl_connect('motion_notify_event',self.fmotion)
            i.canvas.mpl_connect('button_release_event',self.fdepressed)
            
    def set_animated(self,b:bool):
        for i in self.draglines:
            i.set_animated(b)
        for i in self.datalines:
            i.set_animated(b)
    
    def canvasdraw(self):
        redrawn=[]
        for i in self.joined:
            for j in i.figs: #keeps track of which figures have been redrawn
                if j not in redrawn:
                    j.canvas.draw()
                    redrawn.append(j)
                    
            
    def get_background(self):
        self.bg={} #collect backgrounds
        for i in self.dragaxes:
            self.bg[i]=i.figure.canvas.copy_from_bbox(i.bbox)
        for i in self.dataaxes:
            self.bg[i]=i.figure.canvas.copy_from_bbox(i.bbox)
            
    def set_background(self):
        for i in self.dragaxes:
            i.figure.canvas.restore_region(self.bg[i])
        for i in self.dataaxes:
            i.figure.canvas.restore_region(self.bg[i])
            
    def blit_axes(self):
        for i in self.dragaxes:
            i.figure.canvas.blit(i.bbox)
        for i in self.dataaxes:
            i.figure.canvas.blit(i.bbox)        
        
    def fpressed(self,event):
        """When a button is pressed on interface"""
        if event.inaxes not in self.dragaxes: return #if the mouse-click is not in the dragaxes list, then return
        if event.button!=1: return
        if event.inaxes.figure.canvas.toolbar.mode!='':return #this blocks lines from being drug while, pan/zoom, etc. is set
        if self.__class__.active_line is not None: return #if there is already an active line, then ignore
        
        contains=False
        for i in self.draglines:
            if i.contains(event)[0]:
                contains=True #check if any one of the draggable lines contains the event
        if not contains: return
        self.__class__.active_line = self #set the active_line to this instance
        
        for i in self.joined:
            i.set_animated(True)
        self.canvasdraw()
        
        for i in self.joined:
            i.get_background()
            
        for i in self.joined:
            i.draw(False,False)
            
        for i in self.joined:
            i.blit_axes()  
        
    def fmotion(self,event):
        if self.__class__.active_line not in self.joined: return
        if event.inaxes not in self.dragaxes: return
        for i in self.joined: #exclude self
            i.updateLines(event.xdata,event.ydata)
        for i in self.joined:
            i.set_background()
        for i in self.joined:
            i.draw(False,False)
        for i in self.joined:
            i.blit_axes()
    
    def fdepressed(self,event):
        if self.__class__.active_line is not self: return
        self.__class__.active_line = None
        
        for i in self.joined:
            i.set_animated(False)
        self.canvasdraw()
    
    def join(self,draggableline):
        """Link draggable lines together for comparing datasets"""
        if draggableline not in self.joined:
            self.joined.append(draggableline)
            draggableline.joined.append(self)
            for i in draggableline.joined[1:-1]:
                self.join(i)
            for i in self.joined[1:-1]:
                draggableline.join(i)
        
        
def argmin2d(pos,x2d=None,y2d=None,z2d=None,axis=0,returnalt=False):
    """Returns the indices in a 2d array that most closely match the input position, even when the data sets are non-linear
    
        pos: int or float, value that function looks for minimum position in either x2d or y2d
        x2d: 2d numpy.array, 2d array of x values (mxn)
        y2d: 2d numpy.array, 2d array of y values (mxn)
        z2d: 2d numpy.array, 2d array of z values (mxn)
        axis: int, axis to slice from
        returnalt: bool, return the values for the axis you are slicing"""
    for i in [x2d,y2d,z2d]:
        if i is not None:
            yshape,xshape=i.shape
    if z2d is None:
        if axis==0:
            warnings.warn("z2d defaulting to 2d arange array along the y axis",Warning)
            z2d=repeat(np.arange(yshape)[:,np.newaxis],xshape,1)
        elif axis==1:
            warnings.warn("z2d defaulting to 2d arange array along the y axis",Warning)
            z2d=repeat(np.arange(xshape)[np.newaxis],yshape,0)
    if x2d is None:
        if axis==0:
            warnings.warn("x2d defaulting to 2d arange array",Warning)
        x2d=repeat(np.arange(xshape)[np.newaxis],yshape,0)
    if y2d is None:
        if axis==1:
            warnings.warn("y2d defaulting to 2d arange array",Warning)
        y2d=repeat(np.arange(yshape)[:,np.newaxis],xshape,1)
    
    if axis==0:
        temp=np.argmin(np.abs(y2d-pos),0)
        x=x2d[temp,np.arange(temp.shape[0])]
        y=y2d[temp,np.arange(temp.shape[0])]
        z=z2d[temp,np.arange(temp.shape[0])]
        if returnalt:
            return x,y,z
        else:
            return x,z
    elif axis==1:
        temp=np.argmin(np.abs(x2d-pos),1)
        x=x2d[np.arange(temp.shape[0]),temp]
        y=y2d[np.arange(temp.shape[0]),temp]
        z=z2d[np.arange(temp.shape[0]),temp]
        if returnalt:
            return x,y,z
        else:
            return y,z        
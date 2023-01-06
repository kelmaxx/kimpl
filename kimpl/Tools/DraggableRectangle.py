# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 17:17:00 2020

@author: kelma_7rms4km
"""
import matplotlib.patches as patches
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from matplotlib.lines import Line2D
from numpy import newaxis,arange,argmin,repeat,meshgrid,ma,sum,average
import pkg_resources
import warnings
import os

from enum import Enum
#Currently not interactive, haven not implemented the _Mode and new syntax
class _Mode(str, Enum):
    NONE = ""
    RECT_ZOOM = 'RECT_ZOOM'

    def __str__(self):
        return self.value

    @property
    def _navigate_mode(self):
        return self.name if self is not _Mode.NONE else None

class updateToolbar:
    
    def __init__(self,toolbar):
        pass
    
def argmin2d(pos,x2d=None,y2d=None,z2d=None,axis=0,return_values=False,return_coords=False):
    """Returns the slice(s) in a 2d array that most closely match the input position, even when the data sets are curved
    
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
            z2d=repeat(arange(yshape)[:,newaxis],xshape,1)
        elif axis==1:
            warnings.warn("z2d defaulting to 2d arange array along the y axis",Warning)
            z2d=repeat(arange(xshape)[newaxis],yshape,0)
    if x2d is None:
        if axis==0:
            warnings.warn("x2d defaulting to 2d arange array",Warning)
        x2d=repeat(arange(xshape)[newaxis],yshape,0)
    if y2d is None:
        if axis==1:
            warnings.warn("y2d defaulting to 2d arange array",Warning)
        y2d=repeat(arange(yshape)[:,newaxis],xshape,1)
    
    if axis==0:
        ycoords=argmin(abs(y2d-pos),0)
        xcoords=arange(ycoords.shape[0])
        
    if axis==1:
        xcoords=argmin(abs(x2d-pos),1)
        ycoords=arange(xcoords.shape[0])
        
    if return_coords:
        return ycoords,xcoords
    
    x=x2d[ycoords,xcoords]
    y=y2d[ycoords,xcoords]
    z=z2d[ycoords,xcoords]
    if return_values:
        return x,y,z
    elif axis==0:
        return x,z
    elif axis==1:
        return x,y
        
class DraggableLine:
    def __init__(self,ax1,ax2,data,x=None,y=None,data_axis=0):
        self.ax1=ax1 #axis where the data (image or pcolormesh is plotted) is displayed
        self.ax2=ax2 
        self.data=data
        self.data_axis=data_axis
        
        self._setup_xy(x,y)
        self.active=False
        
        self.line,=self.ax1.plot([0,0],[0,0],pickradius=10,linewidth=1.3)
        self.dataline,=self.ax2.plot([0,0],[0,0],color=self.line.get_color())
        midy=int(self.data.shape[0]/2)
        midx=int(self.data.shape[1]/2)
        self._updateLine(self.x[midy,midx],self.y[midy,midx])
        
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax1.figure.canvas.draw()
        if self.ax2.figure!=self.ax1.figure:
            self.ax2.figure.canvas.draw()
        self.enable()
        
    def _setup_xy(self,x,y):
        yshape,xshape=self.data.shape
        if x is None:
            x=repeat(arange(xshape)[newaxis],yshape,0)
        if y is None:
            y=repeat(arange(yshape)[:,newaxis],xshape,1)
        if y.ndim==1:
            y=repeat(y[:,newaxis],xshape,1)
        if x.ndim==1:
            x=repeat(x[newaxis],yshape,0)
        if (x.ndim==1) and (y.ndim==1):
            x,y=meshgrid(x,y)
        self.x=x
        self.y=y
        
    def updateData(self,data):
        self.data=data
        tempx=self.line.get_xdata()[0]
        tempy=self.line.get_ydata()[0]
        self.updateLine(tempx,tempy)
        
    def set_data_axis(self,data_axis):
        self.data_axis=data_axis
        midy=int(self.data.shape[0]/2)
        midx=int(self.data.shape[1]/2)
        self._updateLine(self.x[midy,midx],self.y[midy,midx])
        self.ax2.relim()
        self.ax2.autoscale_view()
        
    def _updateLine(self,xin,yin):
        if self.data_axis==0:
            val_in=yin
        else:
            val_in=xin
        tempx,tempy,tempz=argmin2d(val_in,x2d=self.x,y2d=self.y,z2d=self.data,axis=self.data_axis,returnalt=True)
        self.line.set_data(tempx,tempy)
        if self.data_axis==0:  #horizontal line
            self.dataline.set_data(tempx,tempz)
        else:  #vertical line
            self.dataline.set_data(tempy,tempz)
        
                
    def enable(self):
        self._idpress=self.ax1.figure.canvas.mpl_connect('button_press_event',self._press)
        self._idrelease=self.ax1.figure.canvas.mpl_connect('button_release_event',self._release)
        self._idmotion=self.ax1.figure.canvas.mpl_connect('motion_notify_event',self._motion)
        
    def disable(self):
        self.ax1.figure.canvas.mpl_disconnect(self._idpress)
        self.ax1.figure.canvas.mpl_disconnect(self._idrelease)
        self.ax1.figure.canvas.mpl_disconnect(self._idmotion)  

            
    def _press(self,event):
        if event.inaxes!=self.ax1: return
        if event.button!=1: return
        contains=self.line.contains(event)[0]
        if contains:
            self.line.set_animated(True)
            self.dataline.set_animated(True)
            self.ax1.figure.canvas.draw()
            if self.ax2.figure!=self.ax1.figure:
                self.ax2.figure.canvas.draw()
            self.bg1=self.ax1.figure.canvas.copy_from_bbox(self.ax1.bbox)
            self.bg2=self.ax2.figure.canvas.copy_from_bbox(self.ax2.bbox)
            self.ax1.draw_artist(self.line)
            self.ax2.draw_artist(self.dataline)
            self.ax1.figure.canvas.blit(self.ax1.bbox)
            self.ax2.figure.canvas.blit(self.ax2.bbox)
            self.active=True
    
    def _motion(self,event):
        if event.inaxes!=self.ax1: return
        if not self.active: return
        self._updateLine(event.xdata,event.ydata)
        self.ax1.figure.canvas.restore_region(self.bg1)
        self.ax2.figure.canvas.restore_region(self.bg2)
        self.ax1.draw_artist(self.line)
        self.ax2.draw_artist(self.dataline)
        self.ax1.figure.canvas.blit(self.ax1.bbox)
        self.ax2.figure.canvas.blit(self.ax2.bbox)
    
    def _release(self,event):
        self.active=False
        self.line.set_animated(False)
        self.dataline.set_animated(False)
        self.ax1.figure.canvas.draw()
        if self.ax2.figure!=self.ax1.figure:
            self.ax2.figure.canvas.draw()
            
class DraggableRectangle:
    def __init__(self,ax1,blit=True,**kwargs):
        """ax1 is where the rectanble is drawn, ax2 is the axis whose xlim and ylim are set to match the rectangle space in ax1"""
        self.ax1=ax1
        self.fig1=self.ax1.figure
        self.canvas1=self.fig1.canvas
        self.toolbar1=self.canvas1.toolbar
        
        x,y,w,h=self._new_coords()
        
        self.rect=patches.Rectangle((x,y),w,h,fill=False,color='red')
        self.ax1.add_patch(self.rect)
        self.resizer,=self.ax1.plot(x+w,y+h,'+',color='red',markersize=14,mew=2,scalex=False,scaley=False)
        
        self.blit=blit 
        self.press=None
        self.bg1=None
        self.enabled=False
        self.connect()
    
    def _new_coords(self):
        """Returns the coordinates for the rectangle that are 10% from the edges"""
        x0,x1=self.ax1.get_xlim()
        y0,y1=self.ax1.get_ylim()
        x=0.1*(x1-x0)+x0
        y=0.1*(y1-y0)+y0
        w=0.8*(x1-x0)
        h=0.8*(y1-y0)
        return x,y,w,h
    
    def reset_rect(self):
        self.set_rect(*self._new_coords())
    
    def set_rect(self,x=None,y=None,w=None,h=None):
        ox,oy,ow,oh=self._get_coords()
        if x is None: x=ox
        if y is None: y=oy
        if w is None: w=ow
        if h is None: h=oh
        self.resizer.set_data(x+w,y+h)
        self.rect.set_xy((x,y))
        self.rect.set_width(w)
        self.rect.set_height(h)
    
    def _get_coords(self):
        """Get coordinates of rectangle and resizer"""
        x,y=self.rect.xy
        w,h=self.rect.get_width(),self.rect.get_height()
        
        
        return x,y,w,h
    
    def connect(self):
        self._id_press=self.canvas1.mpl_connect('button_press_event',self._rect_zoom_handler)
        self._id_release=self.canvas1.mpl_connect('button_release_event',self._rect_zoom_handler)
        self._id_drag=self.canvas1.mpl_connect('motion_notify_event',self._rect_zoom_handler)
    
    def _press(self,event):
        if event.inaxes!=self.ax1: return
        self.contains, attrd=self.rect.contains(event)
        self.contains2,attrd=self.resizer.contains(event)
        if self.contains or self.contains2:
            self.press=*self._get_coords(),event.xdata,event.ydata
            if self.blit:
                self._blit_animate()
                self._blit_setup()
                self._blit()
        
    def _motion(self,event):
        if event.inaxes!=self.ax1: return
        if self.press is None: return
        x,y,w,h,xpress,ypress=self.press
        dx=event.xdata-xpress
        dy=event.ydata-ypress
        
        if self.contains2: #resizer
            w,h=w+dx,h+dy
            self.set_rect(w=w,h=h)
        elif self.contains: #move box
            x,y=x+dx,y+dy
            self.set_rect(x=x,y=y)
        if self.blit:
            self._blit_restore()
            self._blit()
        else:
            self._draw()
        
        
        
    def _release(self,event):
        self.press=None
        if self.blit:
            self._blit_takedown()
        self._draw()
    
    def _blit_animate(self):
        self.rect.set_animated(True)
        self.resizer.set_animated(True)
    
    def _blit_setup(self):
        self.canvas1.draw()
        self.bg1=self.canvas1.copy_from_bbox(self.ax1.bbox)
        
    def _blit_restore(self):
        self.canvas1.restore_region(self.bg1)
        
        
    def _blit(self):
        self.ax1.draw_artist(self.rect)
        self.ax1.draw_artist(self.resizer)
        self.canvas1.blit(self.ax1.bbox)
        
    def _blit_takedown(self):
        self.rect.set_animated(False)
        self.resizer.set_animated(False)
        
    def _draw(self):
        """(Slower) Alternative to blitting"""
        self.canvas1.draw_idle()
    
            
    def add_to_toolbar(self):
        fpath=os.path.dirname(__file__)
        a=QAction(QIcon(fpath+os.sep+'../DraggableRectangle.ico'),"Enable draggable rectangle",None)
        a.triggered.connect(self.rect_zoom)
        a.setCheckable(True)
        self.toolbar1.insertAction(self.toolbar1._actions['zoom'],a)
        self.toolbar1._actions['rect zoom']=a
        self.toolbar1._actions['zoom'].triggered.connect(self._update_buttons_checked)
        self.toolbar1._actions['pan'].triggered.connect(self._update_buttons_checked)
    
    def _rect_zoom_handler(self,event):
        if self.toolbar1.mode == _Mode.RECT_ZOOM:
            if event.name == 'button_press_event':
                self._press(event)
            elif event.name == 'button_release_event':
                self._release(event)
            elif event.name == 'motion_notify_event':
                self._motion(event)
    
    def rect_zoom(self):
        if not self.toolbar1.canvas.widgetlock.available(self.toolbar1):
            self.self.toolbar1.set_message('rect_zoom unavailable')
        if self.toolbar1.mode.name == _Mode.RECT_ZOOM:
            self.toolbar1.mode = _Mode.NONE
            self.canvas1.widgetlock.release(self.toolbar1)
        else:
            self.toolbar1.mode = _Mode.RECT_ZOOM
            self.canvas1.widgetlock(self.toolbar1)
        
        self._update_buttons_checked()
        
    
        
        
    def _update_buttons_checked(self):
        # sync button checkstates to match active mode
        self.toolbar1._actions['pan'].setChecked(self.toolbar1.mode.name == 'PAN')
        self.toolbar1._actions['zoom'].setChecked(self.toolbar1.mode.name == 'ZOOM')
        self.toolbar1._actions['rect zoom'].setChecked(self.toolbar1.mode.name == 'RECT_ZOOM')
        
        
        
        
        
class DraggableRectangleZoom(DraggableRectangle):
    def __init__(self,ax1,ax2,blit=False,**kwargs):
        """ax1 is where the rectangle is drawn, ax2 is the axis whose xlim and ylim are set to match the rectangle space in ax1"""
        
        self.ax2=ax2
        self.fig2=self.ax2.figure
        self.canvas2=self.fig2.canvas
        super().__init__(ax1=ax1,blit=blit,**kwargs)
        self._drz_idmotion=None
        self._update_ax2()
    
    def _motion(self,event):
        super()._motion(event)
        self._update_ax2()
        
    def _update_ax2(self):
        x,y,w,h=self._get_coords()
        self.ax2.set_xlim(x,x+w)
        self.ax2.set_ylim(y,y+h)
        if self.blit:
            #self.ax2.redraw_in_frame()
            pass
        elif self.canvas2!=self.canvas1:
            self.canvas2.draw_idle()
            
    def _blit_animate(self):
        super()._blit_animate()
        ax2=self.ax2
        redraw_objects=ax2.collections+ax2.images+ax2.lines+ax2.patches+ax2.texts
        for i in redraw_objects:
            i.set_animated(True)
        for i in ax2.images:
            i.set_visible(0)
    
    def _blit_setup(self):
        super()._blit_setup()
        if self.canvas2!=self.canvas1:
            self.canvas2.draw()
        self.bg2=self.canvas2.copy_from_bbox(self.ax2.bbox)
        for i in self.ax2.images:
            i.set_visible(1)
            
    def _blit_restore(self):
        super()._blit_restore()
        self.canvas2.restore_region(self.bg2)
        
    def _blit(self):
        super()._blit()
        ax2=self.ax2
        redraw_objects=ax2.collections+ax2.images+ax2.lines+ax2.patches+ax2.texts
        for i in redraw_objects:
            self.ax2.draw_artist(i)
        self.canvas2.blit(self.ax2.bbox)
        
    def _blit_takedown(self):
        super()._blit_takedown()
        ax2=self.ax2
        redraw_objects=ax2.collections+ax2.images+ax2.lines+ax2.patches+ax2.texts
        for i in redraw_objects:
            i.set_animated(False)
            
    def _draw(self):
        """(Slower) Alternative to blitting"""
        super()._draw()
        if self.canvas2!=self.canvas1:
            self.canvas2.draw_idle()  
        
    
        
        
class DraggableRectangleSum(DraggableRectangle):
    """not for use with data sets with distorted axes"""
    def __init__(self,ax1,data,x=None,y=None,mode='sum',blit=True,**kwargs):
        self.data=data
        self._setup_xy(x,y)
        if mode not in ['sum','average']: raise ValueError("Unrecognized mode {}. Use 'sum' or 'average'".format(mode))
        self.mode=mode
        super().__init__(ax1,blit,**kwargs)
        
        self.hline=Line2D([0],[0])
        self.vline=Line2D([0],[0])
        self.hfig,self.hax,self.hcanvas,self.hbg=None,None,None,None
        self.vfig,self.vax,self.vcanvas,self.vbg=None,None,None,None
        self.hactive=False
        self.vactive=False
        self._drs_idmotion=None
        self._updateLine()
    
    def _setup_xy(self,x=None,y=None):
        yshape,xshape=self.data.shape
        if x is None:
            x=repeat(arange(xshape)[newaxis],yshape,0)
        if y is None:
            y=repeat(arange(yshape)[:,newaxis],xshape,1)
        if y.ndim==1:
            y=repeat(y[:,newaxis],xshape,1)
        if x.ndim==1:
            x=repeat(x[newaxis],yshape,0)
        if (x.ndim==1) and (y.ndim==1):
            x,y=meshgrid(x,y)
        self.x=x
        self.y=y
        
    def add_hline(self,ax):
        if self.hline.axes is not None: raise ValueError("'hline' has already been added to an axis.")
        self.hax=ax
        self.hax.add_line(self.hline)
        self.hfig=self.hax.figure
        self.hcanvas=self.hfig.canvas
        self.hax.relim()
        self.hax.autoscale_view()
        self.hax.set_ylim(0)
        self.hactive=True
        
    
    def add_vline(self,ax):
        if self.vline.axes is not None: raise ValueError("'hline' has already been added to an axis.")
        self.vax=ax
        self.vax.add_line(self.vline)
        self.vfig=self.vax.figure
        self.vcanvas=self.vfig.canvas
        self.vax.relim()
        self.vax.autoscale_view()
        self.vax.set_ylim(0)
        self.vactive=True
        
    def updateData(self,data,x=None,y=None):
        self.data=data
        self._setup_xy(x,y)
        self._updateLine()
        
    def _updateLine(self):
        x,y,w,h=self._get_coords()
        x0=min(x,x+w)
        x1=max(x,x+w)
        y0=min(y,y+h)
        y1=max(y,y+h)
        masky=(self.x<x0)|(self.x>x1)
        maskx=(self.y<y0)|(self.y>y1)
        mask_arrx=ma.masked_array(self.data,maskx)
        mask_arry=ma.masked_array(self.data,masky)
        if self.mode=='average':
            datax=average(mask_arrx,0)
            datay=average(mask_arry,1)
            
        elif self.mode=='sum':
            datax=sum(mask_arrx,0)
            datay=sum(mask_arry,1)
            
        self.hline.set_data(self.x[0],datax)
        self.vline.set_data(self.y[:,0],datay)
        
        
    def _motion(self,event):
        super()._motion(event)
        self._updateLine()
        
        
    def _blit_animate(self):
        super()._blit_animate()
        for i in [self.hline,self.vline]:
            i.set_animated(True)
    
    def _blit_setup(self):
        super()._blit_setup()
        if self.hactive:
            if self.hcanvas!=self.canvas1:
                self.hcanvas.draw()
            self.hbg=self.hcanvas.copy_from_bbox(self.hax.bbox)
        if self.vactive:
            if self.vcanvas!=self.canvas1:
                self.vcanvas.draw()
            self.vbg=self.hcanvas.copy_from_bbox(self.vax.bbox)
            
    def _blit_restore(self):
        super()._blit_restore()
        if self.hactive:
            self.hcanvas.restore_region(self.hbg)
        if self.vactive:
            self.vcanvas.restore_region(self.vbg)
        
    def _blit(self):
        super()._blit()
        if self.hactive:
            self.hax.draw_artist(self.hline)
            self.hcanvas.blit(self.hax.bbox)
        if self.vactive:
            self.vax.draw_artist(self.vline)
            self.vcanvas.blit(self.vax.bbox)
        
    def _blit_takedown(self):
        super()._blit_takedown()
        for i in [self.hline,self.vline]:
            i.set_animated(False)
            
    def _draw(self):
        """(Slower) Alternative to blitting"""
        super()._draw()
        if self.hactive:
            if self.hcanvas!=self.canvas1:
                self.hcanvas.draw_idle()
        if self.vactive:
            if self.vactive!=self.canvas1:
                self.vcanvas.draw_idle()
            
            
    def disable(self):
        super().disable()
        if self._drs_idmotion is not None:
            self.canvas1.mpl_disconnect(self._drs_idmotion)

class DraggableRectangleSumZoom(DraggableRectangleZoom,DraggableRectangleSum):
    def __init__(self,ax1,ax2,data,x=None,y=None,mode='sum',blit=True):
        super().__init__(ax1=ax1,ax2=ax2,blit=blit,data=data,x=x,y=y,mode=mode)


    

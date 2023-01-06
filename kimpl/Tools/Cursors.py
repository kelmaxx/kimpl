# -*- coding: utf-8 -*-
"""
Created on Tue Oct 18 12:33:49 2022

@author: TSM
"""

from matplotlib.patches import Ellipse
from PyQt5.QtCore import pyqtSignal,QObject
import numpy as np

class simpleCursor(QObject):
    valueChanged = pyqtSignal((float,float),name='valueChanged') 
    def __init__(self,xy,ax,edgecolor='black'):
        super().__init__()
        self.ax=ax
        self.el=None
        self.xy=xy
        
        self._limChanged(self.ax)
        
        self.el=Ellipse(self.xy,self.w,self.h,facecolor='none',edgecolor=edgecolor,linewidth=2.5)
        self.ax.add_patch(self.el)
        
        #motion params
        self.objs=[self.el] #list of things to redraw
        self._animated=True
        self._pressed=False
        self._restore_background=True
        self._redraw=True
        self.getBackground()
        
        self.connect()
        
    def connect(self):
        self.ax.callbacks.connect('xlim_changed',self._limChanged)
        self.ax.callbacks.connect('ylim_changed',self._limChanged)
        self.ax.figure.canvas.mpl_connect('resize_event',lambda e: self._limChanged(self.ax))
        self.ax.figure.canvas.mpl_connect('resize_event',lambda e: self._limChanged(self.ax))
        self.ax.figure.canvas.mpl_connect('button_press_event',self._on_click)
        self.ax.figure.canvas.mpl_connect('motion_notify_event',self._on_motion)
        self.ax.figure.canvas.mpl_connect('button_release_event',self._on_release)
            
    def _limChanged(self,ax):
        x0,y0,x1,y1=ax.transData.inverted().transform((0,0,12,12))
        self.w=abs(x1-x0)
        self.h=abs(y1-y0)
        if self.el is not None:
            self.el.set_width(self.w)
            self.el.set_height(self.h)
            
    
    
    def animate(self,b):
        for i in self.objs:
            i.set_animated(b)
    
    def redraw(self):
        if self._restore_background:
            self.ax.figure.canvas.restore_region(self.bg)
        for i in self.objs:
            self.ax.draw_artist(i)
        self.ax.figure.canvas.blit(self.ax.bbox)
    
    def _on_click(self,event):
        if self.ax.figure.canvas.toolbar.mode!='': return
        if not self._animated: return
        contains,attrd=self.el.contains(event)
        if not contains: return
        self._pressed=True
        self.getBackground()
        self.animate(True)
        if self._redraw:
            self.redraw()
        
    
    def _on_motion(self,event):
        if not self._pressed: return
        if event.inaxes!=self.ax: return
        xy=event.xdata,event.ydata
        self.setxy(xy)
        
        if self._redraw:
            self.redraw()
        
    
    def _on_release(self,event):
        self._pressed=False
        self.animate(False)
        
    def getBackground(self):
        self.animate(True)
        self.ax.figure.canvas.draw()
        self.bg=self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.animate(False)
        
    def getxy(self):
        return self.xy
    
    def setxy(self,xy):
        self.xy=xy
        self._limChanged(self.ax)
        self.el.set_center(xy)
        self.valueChanged.emit(*xy)
        
    def resizeEvent(self):
        self._limChanged(self.ax)
        self.getBackground()
        self.redraw()
        
    

def coerce(x,xmin=None,xmax=None):
    if xmin is None: xmin=-np.inf
    if xmax is None: xmax=np.inf
    x=max(x,xmin)
    x=min(x,xmax)
    return x
        
class CrosshairCursor(simpleCursor):
    valueChanged = pyqtSignal((int,int),name='valueChanged') 
    def __init__(self,xy,ax,xlim,ylim,edgecolor='black',xcolor='red',ycolor='#47D7FF'):
        self.xlim=xlim
        self.ylim=ylim
        self.xcolor=xcolor
        self.ycolor=ycolor
        xy=self.coerce(xy)
        super().__init__(xy,ax,edgecolor)
        
        self.xline,=self.ax.plot(self.xlim,[self.xy[1],self.xy[1]],color=xcolor)
        self.yline,=self.ax.plot([self.xy[0],self.xy[0]],self.ylim,color=ycolor)
        
        self.objs.append(self.xline)
        self.objs.append(self.yline)
        
    def _on_motion(self,event):
        if not self._pressed: return
        if event.inaxes!=self.ax: return
        xy=event.xdata,event.ydata
        self.setxy(xy)
        if self._redraw:
            self.redraw()
        
        
    def coerce(self,xy):
        x,y=xy
        x=coerce(x,self.xlim[0],self.xlim[1]-1)
        y=coerce(y,self.ylim[0],self.ylim[1]-1)
        
        x=int(round(x))
        y=int(round(y))
        return x,y
    
    def set_xlim(self,xmin=None,xmax=None):
        if xmin is None:
            xmin=self.xlim[0]
        if xmax is None:
            xmax=self.xlim[1]
        self.xlim=(xmin,xmax)
        self.xline.set_xdata(self.xlim)
        
        xy=self.coerce(self.xy)
        
    
    def set_ylim(self,ymin=None,ymax=None):
        if ymin is None:
            ymin=self.ylim[0]
        if ymax is None:
            ymax=self.ylim[1]
        self.ylim=(ymin,ymax)
        self.yline.set_ydata(self.ylim)
        
        xy=self.coerce(self.xy)
        
    def setxy(self,xy):
        xy=self.coerce(xy)
        super().setxy(xy)
        self.xline.set_ydata([xy[1],xy[1]])
        self.yline.set_xdata([xy[0],xy[0]])
        self.redraw()
        
        
        
    
class DataCursor:
    
    def __init__(self,data,cax,xax,yax,xT=False,yT=True,zmin=None,zmax=None):
        if data.ndim==2:
            data=data[np.newaxis]
        self.data=data
        self.cax=cax
        self.xax=xax
        self.yax=yax
        self.xT=xT
        self.yT=yT
        
        self.n,self.yshape,self.xshape = self.data.shape #n is number of datasets to overlap with cursor
        self.ci=0 #index of dataset whose x and y lines will be blue
        
        self.xlim=(0,self.xshape-1)
        self.ylim=(0,self.yshape-1)
        
        
        
        self.xlines=[]
        self.ylines=[]
        
        self.cc=CrosshairCursor((0,0),self.cax,self.xlim,self.ylim,edgecolor='yellow')
        self.cc.valueChanged.connect(self._setxy)
        
        self._restore_background=True
        self._redraw=True
        
        x=np.arange(self.xshape)
        y=np.arange(self.yshape)
        for i in range(self.n):
            xdata=np.zeros(x.shape)
            ydata=np.zeros(y.shape)
            if self.xT:
                xline,=self.xax.plot(xdata,x,color='black')
            else:
                xline,=self.xax.plot(x,xdata,color='black')
            if self.yT:
                yline,=self.yax.plot(ydata,y,color='black')
            else:
                yline,=self.yax.plot(y,ydata,color='black')
            self.xlines.append(xline)
            self.ylines.append(yline)
        
        if zmin is None:
            zmin=0
        if zmax is None:
            zmax=255
        
        self.set_zlim(zmin,zmax)    
        
        self.setIndex(self.ci)
        self.animate(True)
        self.getBackground()
        self.animate(False)
        
        self.cax.callbacks.connect('xlim_changed',self.match_axis_lims)
        self.cax.callbacks.connect('ylim_changed',self.match_axis_lims)
        
        self.redraw()
    
    def animate(self,b):
        for xline,yline in zip(self.xlines,self.ylines):
            xline.set_animated(b)
            yline.set_animated(b)
            
    def getBackground(self):
        self.animate(True)
        self.xax.figure.canvas.draw()
        self.yax.figure.canvas.draw()
        self.bgx=self.xax.figure.canvas.copy_from_bbox(self.xax.bbox)
        self.bgy=self.yax.figure.canvas.copy_from_bbox(self.yax.bbox)
        self.animate(False)
            
    def _setxy(self,xi,yi):
        x=np.arange(self.xshape)
        y=np.arange(self.yshape)
        for i,(xline,yline) in enumerate(zip(self.xlines,self.ylines)):
            xdata=self.data[i,yi,:]
            ydata=self.data[i,:,xi]
            if self.xT:
                xline.set_data(xdata,x)
            else:
                xline.set_data(x,xdata)
            if self.yT:
                yline.set_data(ydata,y)
            else:
                yline.set_data(y,ydata)
        if self.cc._pressed:
            self.animate(True)
            self.redraw()
            self.animate(False)
    
    def setxy(self,xy):
        self.cc.setxy(xy)
        self.redraw()
        
    def getxy(self):
        return self.cc.getxy()
        
    def redraw(self):
        if self._restore_background:
            self.xax.figure.canvas.restore_region(self.bgx)
            self.yax.figure.canvas.restore_region(self.bgy)
        for xline,yline in zip(self.xlines,self.ylines):
            self.xax.draw_artist(xline)
            self.yax.draw_artist(yline)
        self.xax.figure.canvas.blit(self.xax.bbox)
        self.yax.figure.canvas.blit(self.yax.bbox)
        
    def setIndex(self,i):
        self.ci=i
        for xline,yline in zip(self.xlines,self.ylines):
            xline.set_color('black')
            yline.set_color('black')
        self.xlines[i].set_color(self.cc.xcolor)
        self.ylines[i].set_color(self.cc.ycolor)
        
    def set_zlim(self,zmin=None,zmax=None):
        if zmin is None:
            zmin=self.zlim[0]
        if zmax is None:
            zmax=self.zlim[1]
        self.zlim=(zmin,zmax)
        
        if self.xT:
            self.xax.set_xlim(*self.zlim)
        else:
            self.xax.set_ylim(*self.zlim)
        if self.yT:
            self.yax.set_xlim(*self.zlim)
        else:
            self.yax.set_ylim(*self.zlim)
            
        self.xax.figure.canvas.draw()
        self.yax.figure.canvas.draw()
        
    def set_data(self,data):
        if data.ndim==2:
            data=data[np.newaxis]
        if data.shape!=(self.n,self.yshape,self.xshape):
            self.n,self.yshape,self.xshape=data.shape
            self.xlim=(0,self.xshape-1)
            self.ylim=(0,self.yshape-1)
            self.cc.set_xlim(*self.xlim)
            self.cc.set_ylim(*self.ylim)
        self.data=data
        self.setxy(self.cc.xy) #coerce into bounds if needed
        
    def match_axis_lims(self,ax):
        if self.xT:
            self.xax.set_ylim(*self.cax.get_xlim())
        else:
            self.xax.set_xlim(*self.cax.get_xlim())
            
        if self.yT:
            self.yax.set_ylim(*self.cax.get_ylim())
        else:
            self.yax.set_xlim(*self.cax.get_ylim())
        self.drawCanvas()
        
    def resizeEvent(self):
        self.getBackground()
        self.cc.resizeEvent()
        self.redraw()
        
    def drawCanvas(self):
        self.cax.figure.canvas.draw()
        self.xax.figure.canvas.draw()
        self.yax.figure.canvas.draw()
        
            
        
        
        
        
        
        
        
        
        
        
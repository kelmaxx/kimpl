# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 10:45:40 2022

@author: TSM
"""
import matplotlib.pyplot as plt
import matplotlib
from .DataCursor import DataCursor
class CrosshairCursor:
    
    def __init__(self,img,hline_ax,vline_ax=None,**kwargs):
        """
        Create a draggable cursor linked to an image that returns the horizontal and vertical intensity slices from the image.

        Parameters
        ----------
        img : mpl.image.AxesImage
            Matplotlib image the cursor is connected to.
        hline_ax : mpl.axes._subplots.AxesSubplot
            Axis used to plot the data for a horizontal slice at the cursor position.
        vline_ax : mpl.axes._subplots.AxesSubplot, optional
            Axis used to plot the datat for a vertical slice at the cursor position. The default is the same axis as hline_ax.
        color: str, optional
            Color used for cursor
        colorxy: str, optional
            Color used for horizontal and vertical lines
        transposey: bool, optional
            Plot vertical slice on a sideways plot.
        

        Returns
        -------
        None.

        """
        img: matplotlib.image.AxesImage
        self.img=img
        self.data=img.get_array()
        self.ylim,self.xlim=self.data.shape
        self.ax1=img.axes
        
        if vline_ax is None:
            vline_ax=hline_ax
        self.hax=hline_ax
        self.vax=vline_ax
        self.color=kwargs.pop('color','black')
        self.colorxy=kwargs.pop('colorxy',('red','#47D7FF'))
        self.ty=kwargs.pop("transposey",False)
        
        
        #crosshair lines
        self.lx,=self.ax1.plot([0,self.xlim],[self.ylim/2,self.ylim/2],color=self.colorxy[0])
        self.ly,=self.ax1.plot([self.xlim/2,self.xlim/2],[0,self.ylim],color=self.colorxy[1])
        
        #datalines
        self.dx,=self.hax.plot(self.data[int(self.ylim/2),:],color=self.colorxy[0])
        self.dy,=self.vax.plot(self.data[:,int(self.xlim/2)],color=self.colorxy[1])
        self.cx,=self.hax.plot([int(self.xlim/2)],self.data[int(self.ylim/2),int(self.xlim/2)],'o',markerfacecolor=self.colorxy[0],markeredgecolor='black')
        self.cy,=self.vax.plot([int(self.ylim/2)],self.data[int(self.ylim/2),int(self.xlim/2)],'o',markerfacecolor=self.colorxy[1],markeredgecolor='black')
        
        self.hax.set_ylim(*self.img.get_clim())
        self.vax.set_ylim(*self.img.get_clim())
        
        
        self.dc=DataCursor(self.ax1,snap=False,color=self.color,xy=(self.xlim/2,self.ylim/2))
        self.dc.set_position(self.xlim/2,self.ylim/2)
        self.dc.draw_clear=lambda: None
        self.dc.get_background=lambda: None
        self.ax1.figure.canvas.mpl_connect('button_press_event',self.on_click)
        self.ax1.figure.canvas.mpl_connect('motion_notify_event',self.on_motion)
        self.ax1.figure.canvas.mpl_connect('button_release_event',self.on_release)
        
        
     
    def redraw(self):
        for i in [self.lx,self.ly,
                  self.dx,self.dy,
                  self.cx,self.cy]:
            i.axes.draw_artist(i)
        self.ax1.figure.canvas.blit(self.ax1.bbox)
        self.hax.figure.canvas.blit(self.hax.bbox)
        if self.vax is not self.hax:
            self.vax.figure.canvas.blit(self.vax.bbox)
    
    def on_click(self,event):
        self.event=event
        if event.inaxes!=self.ax1: return
        if event.button!=1: return
        if self.ax1.figure.canvas.toolbar.mode!='': return
        for i in [self.lx,self.ly,
                  self.dx,self.dy,
                  self.cx,self.cy]:
            i.set_animated(True)
        self.ax1.figure.canvas.draw()
        if self.ax1.figure is not self.hax.figure: #only redraw once
            self.hax.figure.canvas.draw()
        if self.hax.figure is not self.vax.figure:
            self.vax.figure.canvas.draw()
        self.bg1=self.ax1.figure.canvas.copy_from_bbox(self.ax1.bbox)
        self.dc.bg=self.bg1
        self.hbg=self.hax.figure.canvas.copy_from_bbox(self.hax.bbox)
        if self.hax is self.vax:
            self.vbg=self.hbg
        else:
            self.vbg=self.vax.figure.canvas.copy_from_bbox(self.vax.bbox)
        self.dc.redraw()
        self.redraw()
                  
        
    
    def on_motion(self,event):
        if not self.dc.clicked: return
        self.update_lines()
        
        self.ax1.figure.canvas.restore_region(self.bg1)
        self.hax.figure.canvas.restore_region(self.hbg)
        if self.vax is not self.hax:
            self.vax.figure.canvas.restore_region(self.vbg)
        
        self.dc.redraw()
        self.redraw()
        
            
    def on_release(self,event):
        for i in [self.lx,self.ly,
                  self.dx,self.dy,
                  self.cx,self.cy]:
            i.set_animated(False)
        self.ax1.figure.canvas.draw()
        if self.ax1.figure is not self.hax.figure: #only redraw once
            self.hax.figure.canvas.draw()
        if self.hax.figure is not self.vax.figure:
            self.vax.figure.canvas.draw()
    
    def update_lines(self):
        x,y=self.dc.get_position()
        x=max(0,x)
        x=min(x,self.xlim-1)
        y=max(0,y)
        y=min(y,self.ylim-1) #limit x and y
        
        self.lx.set_ydata([y,y])
        self.ly.set_xdata([x,x])
        
        self.dx.set_ydata(self.data[int(y),:])
        self.dy.set_ydata(self.data[:,int(x)])
        self.cx.set_data([int(x)],self.data[int(y),int(x)])
        self.cy.set_data([int(y)],self.data[int(y),int(x)])
        
    
    def set_data(self,data):
        self.data=data
        self.img.set_data(data)
        self.update_lines()
        
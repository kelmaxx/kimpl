# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 11:10:31 2021

@author: TSM
"""

# from KellysTools import getIndex,loadz
# from kmatplotlib import *
# import matplotlib as mpl
import warnings
warnings.filterwarnings( "ignore")
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib import ticker
from numpy import iterable
# import os

def _align_axes(ax1,ax2,axis='x',which='max'):
    if axis=='x':
        x0,x1=ax1.get_xlim()
        xn0,xn1=ax2.get_xlim()
        if ax2.get_xscale()=='log':
            x0=max(x0,.01)
            x1=max(x1,.01)
        if which=='max':
            xn0=x1
            if x1>=xn1:
                xn1=xn1+.1*abs(xn1)
            ax2.set_xlim(xmin=xn0,xmax=xn1,emit=False)
        elif which=='min':
            xn1=x0
            if x0<xn0:
                xn0=xn0-.1*abs(xn0)
            ax2.set_xlim(xmin=xn0,xmax=xn1,emit=False)
    elif axis=='y':
        y0,y1=ax1.get_ylim()
        if ax2.get_yscale()=='log':
            y0=max(y0,.01)
            y1=max(y1,.01)
        if which=='max':
            ax2.set_ylim(ymin=y1,emit=False)
        elif which=='min':
            ax2.set_ylim(ymax=y0,emit=False)
    ax1.figure.canvas.draw_idle()

class TwinAx:
    def __init__(self,axes):
        self.ax=axes
        
    def imshow(self,*args,**kwargs):
        out = []
        for i in self.ax:
            out.append(i.imshow(*args,**kwargs))
        return out
            
    def plot(self,*args,**kwargs):
        out=[]
        for i in self.ax:
            out.append(i.plot(*args,**kwargs))
        return out
            
    def pcolormesh(self,*args,**kwargs):
        out=[]
        for i in self.ax:
            out.append(i.imshow(*args,**kwargs))
        return out

def split_shared_ax(ax,position,size='100%',pad=0,lims=None):
    """
    *position*
       ["left"|"right"|"bottom"|"top"]
    *lims*
       (min,max) or (min,mid,max)
    """
    opposite=dict(right='left',left='right',top='bottom',bottom='top')
    ax1=ax._make_twin_axes()
    divider=make_axes_locatable(ax1)
    ax2=divider.append_axes(position,size=size,pad=pad)
    if position in ['left','right']:
        ax1.sharey(ax2)
        if position == 'right':
            ax1.spines['right'].set_visible(False)
            ax2.spines['left'].set_linestyle('dotted')
            ax2.spines['left'].set_color('#A0A0A0')
            ax2.yaxis.set_tick_params(left=False,labelleft=False)
            if lims is None:
                xmin,xmax=ax1.get_xlim()
                xmid=(xmax-xmin)/2
            elif iterable(lims):
                if len(lims)==2:
                    xmin,xmax=lims
                    xmid=(xmax-xmin)/2
                elif len(lims)==3:
                    xmin,xmid,xmax=lims
            else:
                xmin,xmax=ax1.get_xlim()
                xmid=(xmax-xmin)/2
            ax1.set_xlim(xmin,xmid)
            ax2.set_xlim(xmid,xmax)
            ax1.callbacks.connect('xlim_changed',lambda ax: _align_axes(ax1,ax2,axis='x',which='max'))
            ax2.callbacks.connect('xlim_changed',lambda ax: _align_axes(ax2,ax1,axis='x',which='min'))
        elif position == 'left':
            # ax1.spines['left'].set_visible(True)
            ax1.spines['left'].set_linestyle('dotted')
            ax1.spines['left'].set_color('#A0A0A0')
            ax2.spines['right'].set_visible(False)
            ax1.yaxis.set_tick_params(left=False,labelleft=False)
            if lims is None:
                xmin,xmax=ax1.get_xlim()
                xmid=(xmax-xmin)/2
            elif iterable(lims):
                if len(lims)==2:
                    xmin,xmax=lims
                    xmid=(xmax-xmin)/2
                elif len(lims)==3:
                    xmin,xmid,xmax=lims
            else:
                xmin,xmax=ax1.get_xlim()
                xmid=(xmax-xmin)/2
            
            ax1.set_xlim(xmid,xmax)
            ax2.set_xlim(xmin,xmid)
            ax1.callbacks.connect('xlim_changed',lambda ax: _align_axes(ax1,ax2,axis='x',which='min'))
            ax2.callbacks.connect('xlim_changed',lambda ax: _align_axes(ax2,ax1,axis='x',which='max'))
        
    elif position in ['top','bottom']:
        ax1.sharex(ax2)
        if position == 'top':
            ax1.spines['top'].set_visible(True)
            ax1.spines['top'].set_linestyle('dotted')
            ax1.spines['top'].set_color('#A0A0A0')
            ax2.spines['bottom'].set_visible(False)
            ax2.xaxis.set_tick_params(bottom=False,labelbottom=False)
            if lims is None:
                ymin,ymax=ax1.get_ylim()
                ymid=(ymax-ymin)/2
            elif iterable(lims):
                if len(lims)==2:
                    ymin,ymax=lims
                    ymid=(ymax-ymin)/2
                elif len(lims)==3:
                    ymin,ymid,ymax=lims
            else:
                ymin,ymax=ax1.get_ylim()
                ymid=(ymax-ymin)/2
            ax1.set_ylim(ymin,ymid)
            ax2.set_ylim(ymid,ymax)
            ax1.callbacks.connect('ylim_changed',lambda ax: _align_axes(ax1,ax2,axis='y',which='max'))
            ax2.callbacks.connect('ylim_changed',lambda ax: _align_axes(ax2,ax1,axis='y',which='min'))
        elif position == 'bottom':
            ax1.spines['bottom'].set_visible(False)
            ax2.spines['top'].set_visible(True)
            ax2.spines['top'].set_linestyle('dotted')
            ax2.spines['top'].set_color('#A0A0A0')
            ax1.xaxis.set_tick_params(bottom=False,labelbottom=False)
            if lims is None:
                ymin,ymax=ax1.get_ylim()
                ymid=(ymax-ymin)/2
            elif iterable(lims):
                if len(lims)==2:
                    ymin,ymax=lims
                    ymid=(ymax-ymin)/2
                elif len(lims)==3:
                    ymin,ymid,ymax=lims
            else:
                ymin,ymax=ax1.get_ylim()
                ymid=(ymax-ymin)/2
            ax1.set_ylim(ymid,ymax)
            ax2.set_ylim(ymin,ymid)
            ax1.callbacks.connect('ylim_changed',lambda ax: _align_axes(ax1,ax2,axis='y',which='min'))
            ax2.callbacks.connect('ylim_changed',lambda ax: _align_axes(ax2,ax1,axis='y',which='max'))
    ax.tick_params(left = False, right = False , labelleft = False ,
                labelbottom = False, bottom = False)
    ax.figure.align_labels((ax,ax1))
    lab=hex(id(ax))
    ax.set_label(f"<Parent> (id: {lab})")
    ax1.set_label(f"<{opposite[position]}> (id: {lab})")
    ax2.set_label(f"<{position}> (id: {lab})")
    return ax1,ax2

def logify(ax,axis='x'):
    if axis=='x' or axis=='both':
        xmin,_=ax.get_xlim()
        if xmin<=0:
            ax.set_xlim(xmin=.01)
        ax.set_xscale('log')
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    if axis=='y'or axis=='both':
        ymin,_=ax.get_ylim()
        if ymin<=0:
            ax.set_ylim(ymin=.01)
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

# fig,ax=subplots(2,2)
# ax1=split_shared_ax(ax[0,0],position='top')    
# ax2=split_shared_ax(ax[1,0],position='bottom')
# ax3=split_shared_ax(ax[0,1],position='left')    
# ax4=split_shared_ax(ax[1,1],position='right')

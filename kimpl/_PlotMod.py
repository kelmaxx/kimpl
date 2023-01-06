# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 16:22:54 2017

@author: Kelly
"""

import matplotlib.pyplot as plt
import matplotlib
from PyQt5.QtWidgets import QApplication,QAction,QFileDialog,QMenu,QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QPoint
import dill as pickle
import pkg_resources
import os
#matplotlib.style.use('basicfigure')
from numpy import argmin
class kPlotInteractive:
    
    def __init__(self,fig):
        
        self.fig=fig
        self.clipboard=QApplication.clipboard()
        # self.fig.kmatplotlib=self removed for pkg name change
        self.fig.kimpl = self
        fpath=os.path.dirname(__file__)
        self.dumpAction=QAction(QIcon(fpath+os.sep+'Dump.ico'),'Save figure w/ data',self.fig.canvas.toolbar)
        self.copyAction=QAction(QIcon(fpath+os.sep+'CopyIcon.ico'),'Copy Image to Clipboard',self.fig.canvas.toolbar)
        saveAction=self.fig.canvas.toolbar._actions['save_figure']
        actions=self.fig.canvas.toolbar.actions()
        idx=actions.index(saveAction)
        if idx+1>=len(actions):
            self.fig.canvas.toolbar.addAction(self.dumpAction)
            self.fig.canvas.toolbar.addAction(self.copyAction)
        else:
            self.fig.canvas.toolbar.insertAction(actions[idx+1],self.dumpAction)
            self.fig.canvas.toolbar.insertAction(actions[idx+1],self.copyAction)
        self.fig.canvas.toolbar._actions['dump']=self.dumpAction
        self.fig.canvas.toolbar._actions['copy']=self.copyAction
        self.connect()
        
    def connect(self):
        
        self.dumpAction.triggered.connect(self.savedump)
        self.copyAction.triggered.connect(self.copyfig)
        self.fig.canvas.mpl_connect('scroll_event',self.zoom)
    
    def copyfig(self):
        self.clipboard.setPixmap(self.fig.canvas.grab())
        self.fig.canvas.window().statusBar().showMessage("Figure copied to clipboard",3000)
        
    def savedump(self,state,filename_dialog=True): #state is a placeholder
        try: dirpath=self.fig.canvas.get_window_title()
        except:
            try: dirpath=self.fig.canvas.manager.get_window_title()
            except: dirpath=''
        if filename_dialog:
            filepath=QFileDialog.getSaveFileName(directory=dirpath,filter="Pickle (*.pickle)")[0]
        else:
            filepath=dirpath
        if filepath!='':
            self.fig.savefig(filepath+'.png')
            pickle.dump(self.fig,open(filepath,'wb'))
            try: self.fig.canvas.set_window_title(filepath)
            except:
                try: self.fig.canvas.manager.set_window_title(filepath)
                except: pass
            self.fig.canvas.window().statusBar().showMessage("{} saved successfully".format(filepath),3000)
        else:
            self.fig.canvas.window().statusBar().showMessage("Save unsuccessful",3000)
    def addCursorTrack(self):
        self.lab=QLabel()
        self.fig.canvas.toolbar.addWidget(self.lab)
        self.fig.canvas.mpl_connect('motion_notify_event',self.plotcoords)
        
    def plotcoords(self,event):
        if event.inaxes==None:
            self.lab.setText("")
            return
        x,y=event.xdata,event.ydata
        tempstr="x={:<7g} y={:<7g}".format(x,y)
        if len(event.inaxes.images)>0:
            temparr=event.inaxes.images[-1].get_array()
            ty,tx=int(round(y)),int(round(x))
            if 0<=tx<temparr.shape[1] and 0<=ty<temparr.shape[0]:
                z=temparr[ty,tx]
                tempstr+="  [{:g}]".format(z)
        self.lab.setText(tempstr)
        
    def zoom(self,event):
        if event.inaxes is None: return
        x=event.xdata
        y=event.ydata
        ax=event.inaxes
        xmin,xmax=ax.get_xlim()
        ymin,ymax=ax.get_ylim()
        px=(x-xmin)/(xmax-xmin) #get the proportional position of x,y relative to edges
        py=(y-ymin)/(ymax-ymin) 
        scaling_factor=.1
        newxrange=(xmax-xmin)*(1-scaling_factor*event.step)
        newyrange=(ymax-ymin)*(1-scaling_factor*event.step)
        
        newxmin=x-newxrange*px
        newxmax=newxmin+newxrange
        newymin=y-newyrange*py
        newymax=newymin+newyrange
        
        ax.set_xlim(newxmin,newxmax)
        ax.set_ylim(newymin,newymax)
        ax.figure.canvas.draw_idle()
        
    def __getstate__(self):
        return {}

def decorate_subplots(new_subplots):
    def wrapper_function(nrows=1, ncols=1, sharex=False, sharey=False, squeeze=True, subplot_kw=None, gridspec_kw=None, **fig_kw):
        fig,ax = plt.subplots(nrows, ncols, sharex=sharex, sharey=sharey, squeeze=squeeze, subplot_kw=subplot_kw, gridspec_kw=gridspec_kw, **fig_kw) #run original function
        new_subplots(fig) #apply new code
        return fig,ax #return original results
    wrapper_function.__doc__=plt.subplots.__doc__ #set doc string to match
    return wrapper_function

@decorate_subplots
def subplots(fig):
    kPlotInteractive(fig)
        
def decorate_figure(new_figure):
    def wrapper_function(num=None, figsize=None, dpi=None, facecolor=None, edgecolor=None, frameon=True, FigureClass=plt.Figure, **kwargs):
        fig=plt.figure(num, figsize, dpi, facecolor, edgecolor, frameon, FigureClass, **kwargs)
        new_figure(fig)
        return fig
    wrapper_function.__doc__=plt.figure.__doc__
    return wrapper_function

@decorate_figure 
def figure(fig):
    kPlotInteractive(fig)

def loadPlot(filepath):
    temp=pickle.load(open(filepath,'rb'))
    temp.kimplfig=kPlotInteractive(temp)
    temp.show()
    temp.canvas.manager.set_window_title(filepath)
    return temp
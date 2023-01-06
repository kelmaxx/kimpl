# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 15:21:56 2023

@author: TSM
"""

from PyQt5 import QtWidgets,QtCore
import os
import matplotlib.pyplot as plt
from ._PlotMod import kPlotInteractive


class TabbedFigure(QtWidgets.QWidget):
    def __init__(self,fig):
        super().__init__()
        self.fig=fig
        self.old_mw=fig.canvas.parent() #save original mainwindow for later (if popping out figure)
        self.canvas=fig.canvas
        self.toolbar=self.canvas.toolbar
        self.refresh_name()
        
        
        layout=QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.old_mw.hide() #hide window
    
    def remove(self,show=True,close=False):
        """Remove itself from the tabbed figure, reopen original window if show is true, close figure if show is false and close is true"""
        l=self.layout()
        l.removeWidget(self.canvas)
        l.removeWidget(self.toolbar)
        self.old_mw.setCentralWidget(self.canvas) #rebuild original mainwindow
        self.old_mw.addToolBar(QtCore.Qt.TopToolBarArea,self.toolbar)
        if show:
            self.old_mw.show()
        else:
            if close:
                self.old_mw.close()
            
    def refresh_name(self):
        """There is no way to detect if the name changes, this handles that case"""
        name=self.fig.canvas.manager.get_window_title()
        self.name=name
        self.sname=os.path.basename(name)[:20]
            
        
class Tabs(QtWidgets.QTabWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._figs={}
    def contextMenuEvent(self, e):
        """Creates context menu for removing or closing a figure"""
        tbar=self.tabBar()
        pos=tbar.mapFromParent(e.pos())
        tabindex=tbar.tabAt(pos)
        if tabindex==-1: return
        w=self.widget(tabindex)
        w.refresh_name()
        self.setTabText(tabindex,w.sname)
        self.menuObj=QtWidgets.QMenu(self)
        t=QtWidgets.QAction("Remove",self.menuObj)
        t.triggered.connect(lambda: self.removeFig(tabindex))
        self.menuObj.addAction(t)
        t=QtWidgets.QAction("Close",self.menuObj)
        t.triggered.connect(lambda: self.closeFig(tabindex))
        self.menuObj.addAction(t)
            
        self.menuObj.exec_(e.globalPos())
        
    def addFig(self,fig):
        """add a figure under a new tab"""
        tf=TabbedFigure(fig)
        self.addTab(tf,tf.sname)  #add Tab with widget holding figure with abbreviated name
        self.setTabToolTip(self.indexOf(tf),tf.name) #set the tab tool tip to the full name of the figure
        self._figs[fig]=tf  #add to dictionary containing all figures
        self.setCurrentWidget(tf) #set the current tab to this fig's tab
        
    def removeFig(self,idx):
        """remove figure at index idx. idx can either be tab index or mpl fig reference"""
        if type(idx) is int: #if idx is referring to tab index
            tf=self.widget(idx)
        elif idx in self._figs: #if idx is referring to figure
            tf=self._figs[idx]
        tf.remove(show=True,close=False) #remove widget items and put them back in their original window
        self.removeTab(self.indexOf(tf)) #remove tab
        self._figs.pop(tf.fig) #remove reference to widget from list
        
    def closeFig(self,idx):
        if type(idx) is int:
            tf=self.widget(idx)
        elif idx in self._figs:
            tf=self._figs[idx]
        tf.remove(False,True) #remove and close figure
        self.removeTab(self.indexOf(tf))
        self._figs.pop(tf.fig)
        
    def figs(self):
        return [self.widget(i).fig for i in range(self.count())] #return list of figures according to their tab order
    
def decorate_subplots(new_subplots):
    """This adds the same functionality as the original plt.subplots to the class StackedFigures"""
    def wrapper_function(self,nrows=1, ncols=1, sharex=False, sharey=False, squeeze=True, subplot_kw=None, gridspec_kw=None, **fig_kw):
        fig,ax = plt.subplots(nrows, ncols, sharex=sharex, sharey=sharey, squeeze=squeeze, subplot_kw=subplot_kw, gridspec_kw=gridspec_kw, **fig_kw) #run original function
        new_subplots(self,fig) #apply new code
        return fig,ax #return original results
    wrapper_function.__doc__=new_subplots.__doc__+"\n\n"+plt.subplots.__doc__ #set doc string to match
    return wrapper_function
        
def decorate_figure(new_figure):
    """This adds the same functionality as the original plt.figure to the class StackedFigures"""
    def wrapper_function(self,num=None, figsize=None, dpi=None, facecolor=None, edgecolor=None, frameon=True, FigureClass=plt.Figure, **kwargs):
        fig=plt.figure(num, figsize, dpi, facecolor, edgecolor, frameon, FigureClass, **kwargs)
        new_figure(self,fig)
        return fig
    wrapper_function.__doc__=new_figure.__doc__+"\n\n"+plt.figure.__doc__
    return wrapper_function       
        

class StackedFigures:
    """Create stacked figures, may be initialized without any figures"""
    def __init__(self,stack=[],name:str=None):
        self.window=QtWidgets.QMainWindow()
        self._tabWidget=Tabs()
        self.window.setCentralWidget(self._tabWidget)
        self.window.resize(640,520)
        self.setName(name)
        
        for fig in stack:
            self.addFig(fig)
        self.window.show()
        
        self.__i=0 #for iterator counter
        
    def addFig(self,fig):
        """Add figure into new tab"""
        self._tabWidget.addFig(fig)
        
    def removeFig(self,idx):
        """
        Remove figure from existing tab.

        Parameters
        ----------
        idx : plt.Figure or int
            Index or reference to figure to be removed.

        """
        self._tabWidget.removeFig(idx)
        
    def closeFig(self,idx):
        """
        Close figure from existing tab.

        Parameters
        ----------
        idx : plt.Figure or int
            Index or reference to figure to be closed.

        """
        self._tabWidget.closeFig(idx)
        
    def setName(self,name:str=None):
        """Set the window title"""
        if name is not None:
            self.window.setWindowTitle(name)
            self.name=name
        else:
            self.name=''
    
    def show(self):
        self.window.show()
        
    def close(self):
        self.window.close()
        
    @decorate_subplots
    def subplots(self,fig):
        """Add subplots figure into StackedFigures"""
        kPlotInteractive(fig)
        self.addFig(fig)
        
    @decorate_figure 
    def figure(self,fig):
        """Add figure into StackedFigures"""
        kPlotInteractive(fig)
        self.addFig(fig)
        
    def __iter__(self):
        return self
    
    def __next__(self):
        i=self.__i
        self.__i+=1
        figs=self._tabWidget.figs()
        if self.__i>len(figs):
            self.__i=0
            raise StopIteration
        return figs[i]
        
    def __getitem__(self,key):
        return self._tabWidget.figs()[key]
    
    def __repr__(self):
        return '<StackedFigures:'+self._tabWidget.figs().__repr__()+">"
        
        
if __name__=='__main__':
    fig,ax=subplots()
    ui=StackedFigures()
    tw=ui.tabWidget
    ui.addFig(fig)
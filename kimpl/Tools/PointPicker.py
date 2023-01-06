# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 12:38:38 2023

@author: TSM
"""

class PointPicker:
    
    def __init__(self,ax):
        self.ax=ax
        self.fig=ax.figure
        self.x=[]
        self.y=[]
        self.line,=self.ax.plot([],[],'o',color='green')
        self.fig.canvas.mpl_connect('button_press_event',self.addPoint)
        self.fig.canvas.mpl_connect('key_press_event',self.pause)
        self.pause=False
    
    def addPoint(self,event):
        if self.pause: return
        if event.inaxes!=self.ax: return
        if self.fig.canvas.toolbar.mode!='':return
        if event.button==1:
            self.x.append(round(event.xdata))
            self.y.append(round(event.ydata))
            self.line.set_data(self.x,self.y)
            self.fig.canvas.draw()
        elif event.button==3 and len(self.x)>0:
            self.x.pop(-1)
            self.y.pop(-1)
            self.line.set_data(self.x,self.y)
            self.fig.canvas.draw()
            
    def pause(self,event):
        if event.key=='m':
            self.pause=not self.pause
            
    def getxy(self):
        return self.x,self.y
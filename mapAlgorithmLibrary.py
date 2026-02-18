# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 08:25:39 2025

@author: mitch.lautigar
"""

import pandas as pb

def mapLoad(fName):
    data2Load = pb.read_excel(fName,names=None,header=None)
    mapWidth = len(data2Load.columns)
    mapHeight = len(data2Load)
    rowStack = []
    mapStack = []
    for ii in range(0,mapHeight): #columns
        for jj in range(0,mapWidth): #rows
            rowStack.append(str(data2Load[jj][ii]))
        mapStack.append(rowStack)
        rowStack = []
    print(mapStack)
        
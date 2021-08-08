# -*- coding: utf-8 -*-
'''
第二次算法培训作业:云检测算法和NDVI等植被指数的计算
宋坤杰
'''
#云检测
import gdal
import h5py
import numpy as np
with h5py.File('202106280700.hdf','r') as f:
    key = list(f.keys())
    bandname = key[0:11]
    data = f[bandname[0]][()]
    band03 = f['B03'][:]
    band05 = f['B05'][:]

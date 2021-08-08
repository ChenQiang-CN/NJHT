# -*- coding: utf-8 -*-
'''
第二次算法培训作业:基于shpfile的裁剪
宋坤杰
'''
from osgeo import gdal
import os
import shapefile
#要裁剪的原图
input_raster = "exercise2.tiff"
input_raster = gdal.Open(input_raster)
input_shape = "CHN.shp"
r = shapefile.Reader(input_shape) #读取shp文件
#剪切后的文件
output_raster = 'after_shp.tiff'
ds = gdal.Warp(output_raster,\
    input_raster,\
    format = 'GTiff',\
    outputBounds=r.bbox,\
    cutlineDSName = input_shape,\
    cutlineWhere = "FIELD = 'whatever'",\
    dstNodata = -1000)
ds = None

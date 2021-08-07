# -*- coding:utf-8 -*-
# Created on 2021/7/26 by luren

import numpy, pandas, netCDF4, h5py
import os
from osgeo import gdal


# Question 1:
# 在控制台中输出当前python环境下的所有第三方库及版本
pkgs = os.popen('conda list', mode='r').readlines()
for _ in pkgs:
    print(_, end='')


# Question 2:
# 使用GDAL读取样例栅格文件，在控制台中输出文件的投影信息、行列数
file_path = '样例数据/true_color_3857.tif'
dataset = gdal.Open(file_path, gdal.GA_ReadOnly)

if not dataset:
    raise Exception('Invalid file path!')
else:
    projection = dataset.GetProjection()
    rows = dataset.RasterYSize
    cols = dataset.RasterXSize
    bands = dataset.RasterCount

print(f'The size of image is:\n{rows} rows, {cols} columns and {bands} bands.')
print(f'The projection of image is:{projection}')





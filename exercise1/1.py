
# 题目a

import os
os.system('conda list')

# 题目b

from osgeo import gdal

dataset = gdal.Open(r"D:\作业\true_color_3857.tif")
width = dataset.RasterXSize       #栅格列数
height = dataset.RasterYSize      #栅格行数
proj = dataset.GetProjection()    #投影信息
print('列数为:', width)
print('行数为:', height)
print('投影信息为:', proj)
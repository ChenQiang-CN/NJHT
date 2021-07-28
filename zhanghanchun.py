#题目a
import os
os.system("conda list")

#题目b
from osgeo import gdal
dataset = gdal.Open(r"D:\算法培训\true_color_3857.tif")
#栅格矩阵的列数
im_width = dataset.RasterXSize
#栅格矩阵的行数
im_height = dataset.RasterYSize
#投影信息
im_proj = dataset.GetProjection()
print('列数为:', im_width)
print('行数为:', im_height)
print('投影信息为:', im_proj)
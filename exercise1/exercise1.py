import numpy as np
from osgeo import gdal, gdal_array
import cv2
import matplotlib.pyplot as plt

#a.输出当前python环境下的所有第三方库及版本
pip3 list | findstr numpy

#b.使用GDAL读取样例栅格文件
data = gdal.Open(r"D:/_B学习资料/01遥感算法培训/tif/tif/true_color_3857.tif")

cols = data.RasterXsize
rows = data.RasterYSize

print(data.GetDescription)

print(data.RasterCount)

print(data.GetGeoTransform())

print(data.GetProjection())
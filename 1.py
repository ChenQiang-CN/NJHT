
# 题目a

import os

os.system('pip list')


# 题目b

from osgeo import gdal

# 打开文件
dataset = gdal.Open(r"C:\Users\EDZ\Desktop\true_color_3857.tif")
 # 栅格矩阵的列数
im_width = dataset.RasterXSize
# 栅格矩阵的行数
im_height = dataset.RasterYSize
# 地图投影信息
im_proj = dataset.GetProjection()
print('投影信息为:', im_proj)
print('列为:', im_width)
print('行为:', im_height
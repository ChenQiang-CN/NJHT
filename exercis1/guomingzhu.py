import sys
import os
import numpy as np, pandas as pd

modules = {'NumPy': np, 'pandas': pd}

os.system('python -m pip list')
print('Python version: %s' % (sys.version))
for i in modules.items():
    print('{} version: {}'.format(i[0], i[1].__version__))



from osgeo import gdal

# 打开文件
dataset = gdal.Open(r"C:\Users\EDZ\Desktop\true_color_3857.tif")
 # 栅格矩阵的列数
im_width = dataset.RasterXSize
# 栅格矩阵的行数
im_height = dataset.RasterYSize
# 地图投影信息
im_proj = dataset.GetProjection()

print("列", im_width, "行", im_height)
print("投影信息为", im_proj)
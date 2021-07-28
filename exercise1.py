# question1
import os
os.system('pip list')



# question2
from osgeo import gdal

dataset = gdal.Open(r' D:\tif\tif\picture_0000.tif ')
proj = dataset.GetProjection()
width = dataset.RasterXSize
height = dataset.RasterYSize

print('投影信息为:', proj)
print('列为:', width)
print('行为:', height)

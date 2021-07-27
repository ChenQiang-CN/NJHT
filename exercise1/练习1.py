import os
os.system('pip list')

from osgeo import gdal

dataset = gdal.Open(r' D:\tif\tif\true_color_3857.tif ')
im_proj = dataset.GetProjection()
im_width = dataset.RasterXSize
im_height = dataset.RasterYSize

print('投影信息为:', im_proj)
print('列为:', im_width)
print('行为:', im_height)
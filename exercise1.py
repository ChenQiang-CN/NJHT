# 输出第三方库及版本
from os import path
import sys
from osgeo import gdal as gdal
import h5py as h5py, netCDF4 as nc4, numpy as np, pandas as pd

modules = {'gdal': gdal, 'h5py': h5py , 'netCDF4' : nc4 , 'numpy' : np,'pandas': pd}

print('Python version: %s' % (sys.version))
for i in modules.items():
    print('{} version: {}'.format(i[0],i[1].__version__))

#输出栅格文件信息
from osgeo import gdal
path = 'F:\\20210722training\\2\\true_color_3857.tif'
def readTif():
  #print("test")
  dataset = gdal.Open (path)
  if dataset == None:
    print(fileName+"文件无法打开")
  else:   
    im_width =  dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_proj =   dataset.GetProjection()
  return  im_width,im_height,im_proj

im_width,im_height,im_proj = readTif()  
print('列数：', im_width)
print('行数：', im_height)
print('投影信息：', im_proj)

import numpy
import gdal
import pandas
import netCDF4
import h5py

from pip import _internal #以编程方法运行pip list 或直接在Terminal输入pip list也可以查看所有第三方库版本
_internal.main(['list'])

dataset = gdal.Open(r'E:\算法产品\true_color_3857.tif')
width = dataset.RasterXSize#栅格列数
height = dataset.RasterYSize#栅格行数
proj = dataset.GetProjection()#投影信息

print('列数为:',width)
print('行数为:',height)
print('投影信息为:',proj)

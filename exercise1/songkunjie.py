#1.输出第三方库和版本
from pip import _internal
_internal.main(['list'])
# import pkg_resources
# print([p.project_name for p in pkg_resources.working_set])
# from pkgutil import iter_modules
# print([p.name for p in iter_modules()])
#2.读取栅格数据
from osgeo import gdal
import numpy as np
dataset = gdal.Open(r'C:\Users\fct\zuoye\NJHT\样例数据\true_color_3857.tif')
print(dataset.GetDescription())
print("波段数",dataset.RasterCount)
print("空间参考信息",dataset.GetGeoTransform())
print("行数",dataset.RasterXSize)
print("列数",dataset.RasterYSize)
print("投影信息",dataset.GetProjection)
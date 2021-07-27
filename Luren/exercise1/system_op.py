
import os
from osgeo import gdal

# Question 1
os.system('conda list')

# Question 2
dataset = gdal.Open('../../样例数据/true_color_3857.tif')
print('Projection: %s' % dataset.GetProjection())

x_size = dataset.RasterXSize
y_size = dataset.RasterYSize
print('wide: %4d' % x_size, 'length: %4d' % y_size)


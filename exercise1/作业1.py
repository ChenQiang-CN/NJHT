import os
from osgeo import gdal

command = "pip list"
os.system(command）

ds = gdal.Open(r"C:\Users\Lenovo\Desktop\1\true_color_3857.tif")
im_proj = ds.GetProjection()
cols = ds.RasterXSize
rows = ds.RasterYSize
print("Projection Information：" + im_proj)
print(r"rows:{0}".format(rows))
print(r"cols:{0}".format(cols))



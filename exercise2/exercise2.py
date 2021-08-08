# -*- coding: utf-8 -*-
'''
第二次算法培训作业 hdf to tiff
宋坤杰
'''
import gdal
import h5py
import numpy as np
from osgeo import osr,ogr
with h5py.File('202106280700.hdf','r') as f:
    key = list(f.keys())
    bandname = key[0:11]
    data = f[bandname[0]][()]
    content = f['B01'][:]
    extend =f.attrs['extend'] # 四至
    # print(extend)
    N_Lon = int(extend[1]-extend[0])
    N_Lat = int(extend[3]-extend[2])
    xsize = int(N_Lon/0.005)
    ysize = int(N_Lat/0.005)
    data1 = np.array(data)
#创建.TIFF文件
driver = gdal.GetDriverByName("GTiff")
out_tiff_name = 'exercise2.tiff'
out_tiff=driver.Create(out_tiff_name, xsize, ysize, 1, gdal.GDT_Float32) #x,y图像大小，bands是图像的波段(通道)数，datatype就是图像的象元数据类型
#设置图像范围
geotransform = [extend[0], 0.005, 0, extend[3], 0, -0.005] #左上角x坐标， 水平分辨率，旋转参数， 左上角y坐标，旋转参数，竖直分辨率
out_tiff.SetGeoTransform(geotransform)
#获取地理坐标信息
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)
out_tiff.SetProjection(srs.ExportToWkt()) # 给新图册增加投影信息
band = out_tiff.GetRasterBand(1)
band.WriteArray(data1)
out_tiff = None #关闭tiff文件
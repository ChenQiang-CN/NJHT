# -*- coding: utf-8 -*-
'''
第二次算法培训作业:resample
宋坤杰
'''
from osgeo import gdal, gdalconst
import os
import numpy as np
path=r"C:\Users\Song\Desktop\piesat\4\test\zuoye"
os.chdir(path)
source_file ="exercise2.tiff"
dataset = gdal.Open(source_file, gdalconst.GA_ReadOnly)
# band_count = dataset.RasterCount  # 波段数
# print(band_count)
scale = 2.0
# cols = dataset.RasterXSize  # 列数
# rows = dataset.RasterYSize  # 行数
# cols = int(cols * scale)  # 计算新的行列数
# rows = int(rows * scale)
geotrans = list(dataset.GetGeoTransform())
# print(dataset.GetGeoTransform())
# print(geotrans)
geotrans[1] = geotrans[1] / scale  # 像元宽度变为原来的0.5倍
geotrans[5] = geotrans[5] / scale  # 像元高度变为原来的0.5倍
# print(geotrans)

if os.path.exists('resample.tiff') and os.path.isfile('resample.tiff'):  # 如果已存在同名影像
    os.remove('resample.tiff')  # 删除

band1 = dataset.GetRasterBand(1)
xsize = band1.XSize
ysize = band1.YSize
data=band1.ReadAsArray(buf_xsize=xsize*2, buf_ysize=ysize*2) # 使用更大的缓冲读取影像，与重采样后影像行列对应
out_ds = dataset.GetDriver().Create('resample.tif', xsize*2, ysize*2, 1, band1.DataType)#创建一幅重采样后的影像的句柄，行列数都变成原来的2倍
out_ds.SetProjection(dataset.GetProjection()) #设置投影坐标
out_ds.SetGeoTransform(geotrans)#设置地理变换参数
out_band = out_ds.GetRasterBand(1)
out_band.WriteArray(data) #写入数据到新影像中
out_band.FlushCache()
out_band.ComputeBandStats(False) #计算统计信息
# out_ds.BuildOverviews('average',[1,2,4,8,16,32]) #构建金字塔
del out_ds # 删除句柄
del dataset
print("完成")

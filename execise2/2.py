#  gdal打开hdf数据集
import gdal
import scipy
import numpy
import osr
from pip._internal.cli.cmdoptions import src

datasets = gdal.Open(r"C:\Users\EDZ\Desktop\2\2\data\HDF\202106280700.hdf")
SubDatasets = datasets.GetSubDatasets()
SubDatasetsNum =  len(datasets.GetSubDatasets())
#  输出各子数据集的信息
print("子数据集一共有{0}个: ".format(SubDatasetsNum))
for i in range(SubDatasetsNum):
    print(datasets.GetSubDatasets()[i])

#  获取hdf中的元数据
Metadata = datasets.GetMetadata()
#  获取元数据的个数
MetadataNum = len(Metadata)
#  输出各子数据集的信息
print("元数据一共有{0}个: ".format(MetadataNum))
for key,value in Metadata.items():
    print('{key}:{value}'.format(key = key, value = value))



DatasetNDVI = datasets.GetSubDatasets()[0][0]
RasterNDVI = gdal.Open(DatasetNDVI)
NDVI = RasterNDVI.ReadAsArray()

#  获取四个角的维度
Latitudes = Metadata["GRINGPOINTLATITUDE.1"]
#  采用", "进行分割
LatitudesList = Latitudes.split(", ")
#  获取四个角的经度
Longitude = Metadata["GRINGPOINTLONGITUDE.1"]
#  采用", "进行分割
LongitudeList = Longitude.split(", ")

# 图像四个角的地理坐标
GeoCoordinates = np.zeros((4, 2), dtype="float32")
GeoCoordinates[0] = np.array([float(LongitudeList[0]), float(LatitudesList[0])])
GeoCoordinates[1] = np.array([float(LongitudeList[1]), float(LatitudesList[1])])
GeoCoordinates[2] = np.array([float(LongitudeList[2]), float(LatitudesList[2])])
GeoCoordinates[3] = np.array([float(LongitudeList[3]), float(LatitudesList[3])])

#  列数
Columns = float(Metadata["DATACOLUMNS"])
#  行数
Rows = float(Metadata["DATAROWS"])
#  图像四个角的图像坐标
PixelCoordinates = np.array([[0, 0],
                             [Columns - 1, 0],
                             [Columns - 1, Rows - 1],
                             [0, Rows - 1]], dtype="float32")

#  计算仿射变换矩阵
from scipy.optimize import leastsq


def func(i):
    Transform0, Transform1, Transform2, Transform3, Transform4, Transform5 = i[0], i[1], i[2], i[3], i[4], i[5]
    return [
        Transform0 + PixelCoordinates[0][0] * Transform1 + PixelCoordinates[0][1] * Transform2 - GeoCoordinates[0][0],
        Transform3 + PixelCoordinates[0][0] * Transform4 + PixelCoordinates[0][1] * Transform5 - GeoCoordinates[0][1],
        Transform0 + PixelCoordinates[1][0] * Transform1 + PixelCoordinates[1][1] * Transform2 - GeoCoordinates[1][0],
        Transform3 + PixelCoordinates[1][0] * Transform4 + PixelCoordinates[1][1] * Transform5 - GeoCoordinates[1][1],
        Transform0 + PixelCoordinates[2][0] * Transform1 + PixelCoordinates[2][1] * Transform2 - GeoCoordinates[2][0],
        Transform3 + PixelCoordinates[2][0] * Transform4 + PixelCoordinates[2][1] * Transform5 - GeoCoordinates[2][1],
        Transform0 + PixelCoordinates[3][0] * Transform1 + PixelCoordinates[3][1] * Transform2 - GeoCoordinates[3][0],
        Transform3 + PixelCoordinates[3][0] * Transform4 + PixelCoordinates[3][1] * Transform5 - GeoCoordinates[3][1]]


#  最小二乘法求解
GeoTransform = leastsq(func, np.asarray((1, 1, 1, 1, 1, 1)))
print(GeoTransform)


#  获取数据时间
date = Metadata["RANGEBEGINNINGDATE"]

#  保存为tif
def array2raster(TifName, GeoTransform, array):
    cols = array.shape[1]  # 矩阵列数
    rows = array.shape[0]  # 矩阵行数
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(TifName, cols, rows, 1, gdal.GDT_Float32)
    # 括号中两个0表示起始像元的行列号从(0,0)开始
    outRaster.SetGeoTransform(tuple(GeoTransform))
    # 获取数据集第一个波段，是从1开始，不是从0开始
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    # 代码4326表示WGS84坐标
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

TifName = date + ".tif"
array2raster(TifName, GeoTransform[0], NDVI)

#tif重采样
__author__ = 'xbr'
__date__ = r'C:\Users\EDZ\Desktop\2\2\data\HDF\202106280700.hdf'

import os

import numpy as np
from osgeo import gdal

os.chdir(r'C:\Users\EDZ\Desktop\2\2\data\HDF\202106280700.hdf')

in_ds = gdal.Open('nat_color.tif')
out_rows = int(in_ds.RasterYSize / 2)
out_columns = int(in_ds.RasterXSize / 2)
num_bands = in_ds.RasterCount
gtiff_driver = gdal.GetDriverByName('GTiff')
out_ds = gtiff_driver.Create('nat_color_resampled.tif',
        out_columns, out_rows, num_bands)

out_ds.SetProjection(in_ds.GetProjection())
geotransform = list(in_ds.GetGeoTransform())
geotransform[1] *= 2
geotransform[5] *= 2
out_ds.SetGeoTran

#3、	基于shpfile的裁剪
import rasterio as rio

c
#投影转换
from rasterio.warp import (reproject,RESAMPLING, transform_bounds,calculate_default_transform as calcdt)

affine, width, height = calcdt(src.crs, dst_crs, src.width, src.height, *src.bounds)
kwargs = src.meta.copy()
kwargs.update({
    'crs': dst_crs,
    'transform': affine,
    'affine': affine,
 'width': width,
    'height': height,
    'geotransform':(0,1,0,0,0,-1) ,
    'driver': 'GTiff'
})
dst = rio.open(111, 'w', **kwargs)
     for i in range(1, src.count + 1):
    reproject(source = rio.band(src, i),
        destination = rio.band(dst, i),
        src_transform = src.affine,
        src_crs = src.crs,
        dst_transform = affine,
        dst_crs = dst_crs,
        dst_nodata = src.nodata,
        resampling = RESAMPLING.bilinear)

    #NDVI等植被指数的计算
    import os
    from PIL import Image
    import numpy as np
    from osgeo import gdal
    import glob
    import cv2

    list_tif = glob.glob('C:\Users\EDZ\Desktop\2\2\data\HDF\202106280700.hdf')
    out_path = 'C:\Users\EDZ\Desktop\2\2\data'

    for tif in list_tif:
        in_ds = gdal.Open(tif)
        # 获取文件所在路径以及不带后缀的文件名
        (filepath, fullname) = os.path.split(tif)
        (prename, suffix) = os.path.splitext(fullname)
        if in_ds is None:
            print('Could not open the file ' + tif)
        else:
            # 将MODIS原始数据类型转化为反射率
            red = in_ds.GetRasterBand(1).ReadAsArray() * 0.0001
            nir = in_ds.GetRasterBand(2).ReadAsArray() * 0.0001
            ndvi = (nir - red) / (nir + red)
            # 将NAN转化为0值
            nan_index = np.isnan(ndvi)
            ndvi[nan_index] = 0
            ndvi = ndvi.astype(np.float32)
            # 将计算好的NDVI保存为GeoTiff文件
            gtiff_driver = gdal.GetDriverByName('GTiff')
            # 将NDVI数据坐标投影设置为原始坐标投影
            out_ds.SetProjection(in_ds.GetProjection())
            out_ds.SetGeoTransform(in_ds.GetGeoTransform())
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(ndvi)
            out_band.FlushCache()

"""
============================
# -*- coding: utf-8 -*-
# @Time    : 2021/8/1 17:38
# @Author  : TQ
# @FileName: base2.py
# @Software: pycharm

===========================
"""
import numpy as np
import numpy
import h5py
from osgeo import osr
from osgeo import gdal_array
import gdal, osr
from osgeo import gdal
from osgeo import ogr
import pandas as pd
import os
import glob
import gdalconst


hdf转为tiff,波段分辨率不同，单独存储所需波段
def hdf_to_tiff(hdf_data, Output_folder):
  with h5py.File(hdf_data, 'r') as hdf_file:
    extend = hdf_file.attrs['extend']
    bandName = list(hdf_file.keys())

    for item in range(len(bandName)):
        if str(item) == '2' or '3' or '4': #存储计算NDVI和云检测所需波段
            data = hdf_file[bandName[item]][()]
            (m, n) = data.shape

            XSize = n
            YSize = m
            dt = str(202106280700) + '-B' + str(item+1)
            # 创建.tif文件
            driver = gdal.GetDriverByName('GTiff')
            tif_file = Output_folder + '\\' + dt + '.tif'
            out_ds = driver.Create(tif_file, XSize, YSize, 1, gdal.GDT_Float32)
            geoTrans = [extend[0], 0.005, 0, extend[3], 0, -0.005]
            sr = osr.SpatialReference()
            sr.ImportFromEPSG(4326)
            s = sr.ExportToWkt()
            out_ds.SetProjection(sr.ExportToWkt())
            out_ds.SetGeoTransform(geoTrans)
            out_ds.SetProjection(s)
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(data)
            del out_ds

#tiff 重采样
def tiff_resampling(tif_list, Output_folder2):
  referencefile = tif_list[4]

  for i in range(len(tif_list)-1):
      # 获取输出影像信息
      tiff_inputfile = tif_list[i]
      inputrasfile = gdal.Open(tiff_inputfile, gdal.GA_ReadOnly)
      inputProj = inputrasfile.GetProjection()
      # 获取参考影像信息
      referencefile2 = gdal.Open(referencefile, gdal.GA_ReadOnly)
      referencefileProj = referencefile2.GetProjection()
      referencefileTrans = referencefile2.GetGeoTransform()
      bandreferencefile = referencefile2.GetRasterBand(1)
      Width = referencefile2.RasterXSize
      Height = referencefile2.RasterYSize
      nbands = referencefile2.RasterCount
      # 创建重采样输出文件（设置投影及六参数）
      driver = gdal.GetDriverByName('GTiff')
      dt = str(tiff_inputfile[32:47])
      outputfilePath = Output_folder2 + '\\' + dt + '_res.tif'
      output = driver.Create(outputfilePath, Width, Height, nbands, bandreferencefile.DataType)
      output.SetGeoTransform(referencefileTrans)
      output.SetProjection(referencefileProj)
      # 参数说明 输入数据集、输出文件、输入投影、参考投影、重采样方法(最邻近内插\双线性内插\三次卷积等)、回调函数
      gdal.ReprojectImage(inputrasfile, output, inputProj, referencefileProj, gdalconst.GRA_Bilinear, 0.0, 0.0, )

##读取tiff
def readTif(fileName):
    dataset = gdal.Open(fileName)

    im_width = dataset.RasterXSize #栅格矩阵的列数
    im_height = dataset.RasterYSize #栅格矩阵的行数
    im_bands = dataset.RasterCount #波段数
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    im_data = dataset.ReadAsArray()
    return im_data, im_height, im_width, im_bands, im_geotrans, im_proj


def readShp(input_shp):
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")  # 为了支持中文路径，请添加
        gdal.SetConfigOption("SHAPE_ENCODING", "GBK")  # 为了使属性表字段支持中文，请添加
        ogr.RegisterAll()  # 注册所有的驱动
        driver = ogr.GetDriverByName("ESRI Shapefile")  # 数据格式的驱动
        ds = driver.Open(input_shp)


        layer = ds.GetLayer(0)
        extent = layer.GetExtent()

        return extent

##云检测
def clouddection(tif_list, tif_list2):
    B03_file = tif_list2[2]
    im_data, im_height, im_width, im_bands, im_geotrans, im_proj = readTif(B03_file)
    B03 = im_data
    B05_file = tif_list[4]
    im_data2, im_height, im_width, im_bands, im_geotrans, im_proj = readTif(B05_file)
    B05 = im_data2
    clouddata = np.zeros_like(B05)
    clouddata[np.logical_or(B03 > 1200, B05 > 2800)] = 1

    return clouddata


##计算NDVI
def NDVI_calculate(tif_list_2, clouddata):
    output_file = r'F:\homework\data2\data\data\result'
    B03_file = tif_list2[2]
    im_data, im_height, im_width, im_bands, im_geotrans, im_proj = readTif(B03_file)
    red_band = im_data
    B04_file = tif_list2[3]
    im_data, im_height, im_width, im_bands, im_geotrans, im_proj = readTif(B04_file)
    nir_band = im_data
    NDVI = (nir_band - red_band)/(nir_band + red_band)

    # 无效值剔除
    NDVI[red_band == 0] == -9999
    NDVI[nir_band == 0] == -9999


    # 云检测
    NDVI[np.where(clouddata == 1)] = 0
    NDVI = NDVI.astype(np.float32)


    driver = gdal.GetDriverByName('GTiff')
    target = output_file + '\\'+'NDVI' + '.tif'
    out_ds = driver.Create(target, im_width, im_height, 1, gdal.GDT_Float32)
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326)
    s = sr.ExportToWkt()
    out_ds.SetProjection(sr.ExportToWkt())
    out_ds.SetGeoTransform(im_geotrans)
    out_ds.SetProjection(s)
    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(NDVI)
    return out_ds

##基于shp裁剪tiff
def tiff_clip(input_shp, Output_folder3):
    tif = glob.glob(Output_folder3+ '\*.tif')
    outputPath = r'F:\homework\data2\data\data\HDF\clip'
    output_tif = outputPath + '\\'+'NDVI-clip' + '.tif'


    im_data, im_height, im_width, im_bands, im_geotrans, im_proj = readTif(tif[0])
    geoTrans = im_geotrans
    xRes = abs(geoTrans[1])
    yRes = abs(geoTrans[5])


    shpExtend = readShp(input_shp)  # 获取矢量经纬度范围

    bgValue = -9999
    outputBounds = (shpExtend[0], shpExtend[2], shpExtend[1], shpExtend[3])
    # 裁切结果与shp左、上相切，强制分辨率与原始保持一致
    ds = gdal.Warp(output_tif, tif, format='GTiff', outputBounds=outputBounds, dstNodata=bgValue,
                   cutlineDSName=input_shp, cropToCutline=True, xRes=xRes, yRes=yRes)
    return ds


if __name__ == '__main__':

    Input_folder = r'F:\homework\data2\data\data\HDF'
    Output_folder = r'F:\homework\data2\data\data\HDF'
    Output_folder2 = r'F:\homework\data2\data\data'
    Output_folder3 = r'F:\homework\data2\data\data\result'

    # 读取所有hdf数据
    data_list = glob.glob(Input_folder + '\*.hdf')

    for i in range(len(data_list)):
        hdf_data = data_list[i]
        hdf_to_tiff(hdf_data, Output_folder)
        print(hdf_data + '-----转tif成功')

    tif_list = glob.glob(Input_folder + '\*.tif')
    tiff_resampling(tif_list, Output_folder2)

    tif_list2 = glob.glob(Output_folder2 + '\*.tif')
    clouddata = clouddection(tif_list, tif_list2)

    input_shp = r'F:\homework\data2\data\data\SHP\CHN.shp'

    NDVI_calculate(tif_list2, clouddata)

    tiff_clip(input_shp, Output_folder3)

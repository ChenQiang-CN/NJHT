# -- coding: utf-8 --
"""
@author: SXG
@file: 基于H8_hdf的NDVI产品
@time: 20210809
"""
import os
import h5py
import osr
import ogr
from osgeo import gdal, gdalconst
from osgeo import gdal_array as ga
import numpy as np

# 1.读取H8_hdf数据
inputHdf_path = r"F:/Python/Train_induction/InputData/HDF/202106280700.hdf"
with h5py.File(inputHdf_path, 'r') as Hdf_File:

    # 四角经纬度、影像日期、波段名称、各波段内的数据
    extend = Hdf_File.attrs['extend']
    image_date = Hdf_File.attrs['file_time_UTC'][0:8]
    BandName = list(Hdf_File.keys())
    for i in range(0, len(BandName)):
        DataValue = Hdf_File[BandName[i]][()]

# 2.HDF的波段 To Tiff
    # 1) 创建一个Tiff
        gtiff_diver = gdal.GetDriverByName("GTiff")
        outputTiff_path = r'F:/Python/Train_induction/OutData/'
        tiff_file = outputTiff_path + image_date + "_" + BandName[i] + ".tiff"
        # 行列数
        Columns = DataValue.shape[0]
        Rows = DataValue.shape[1]
        outRaster = gtiff_diver.Create(tiff_file, Rows, Columns, 1, gdal.GDT_Float32)

    # 2) 根据B01~B04波段的resolution的不同，选择相应的resolution
        str1 = {BandName[0], BandName[1], BandName[3]}
        if BandName[i] in str1:
            resolution = 0.01
        elif BandName[i] == 'B03':
            resolution = 0.005
        else:
            resolution = 0.02

    # 3) 计算 仿射变化矩阵
        geoTrans = [extend[0], resolution, 0.0, extend[3], 0.0, -resolution]
        outRaster.SetGeoTransform(geoTrans)
        outBand = outRaster.GetRasterBand(1)
        outBand.WriteArray(DataValue)

    # 4) 赋投影信息 4326代表 WGS84坐标
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(4326)
        outRaster.SetProjection(sr.ExportToWkt())
        outBand.FlushCache()
        del outRaster
        del i

# 3.重采样 (针对B01~B04 四个波段，因为其他波段分辨率都是2Km)
    # 1) 读取B01~B04 四个波段的数据
    Tiffs = [i for i in os.listdir(outputTiff_path) if i.endswith(".tiff")]
    BandRes_Name = 5 * ['']
    BandRes_Name[4] = Tiffs[4]
    for k in range(0, 4):
        BandName_Tiff = Tiffs[k]
        BandName_Res = 'Resample_' + BandName_Tiff
        inputTiff_Path = outputTiff_path + BandName_Tiff
        outputRes_Path = outputTiff_path + BandName_Res
        ReferenceFile_Path = outputTiff_path + '20210628_B05.tiff'

    # 2) 采用gdal.Warp()方法进行重采样
        # 读tiff 获取影像信息如: 投影、行列、波段数
        inputTiff = gdal.Open(inputTiff_Path, gdal.GA_ReadOnly)
        inputProj =inputTiff.GetProjection()
        ReferenceFile = gdal.Open(ReferenceFile_Path, gdal.GA_ReadOnly)
        ReferenceFileProj = ReferenceFile.GetProjection()
        ReferenceFileTrans = ReferenceFile.GetGeoTransform()
        bandReferenceFile = ReferenceFile.GetRasterBand(1)
        X = ReferenceFile.RasterXSize
        Y = ReferenceFile.RasterYSize
        BandsNum = ReferenceFile.RasterCount

        # 创建重采样输出文件(设置投影等参数)
        driver = gdal.GetDriverByName('GTiff')
        output_Res = driver.Create(outputRes_Path, X, Y, BandsNum, bandReferenceFile.DataType)
        output_Res.SetGeoTransform(ReferenceFileTrans)
        output_Res.SetProjection(ReferenceFileProj)

        # 采用最近邻点法
        options = gdal.WarpOptions(srcSRS=inputProj, dstSRS=ReferenceFileProj, resampleAlg=gdalconst.GRA_Bilinear)
        gdal.Warp(output_Res, inputTiff_Path, options=options)

        # 保存这四个重采样后的tiff名称到一个事先创建好的数组中
        BandRes_Name[k] = BandName_Res
        del inputTiff

    # 3) 删除未重采样的 B01~B04 四个tiff文件 (视具体情况决定是否delete)
    for k in range(0, 4):
        filename_del = Tiffs[k]
        file_del = outputTiff_path + filename_del
        os.remove(file_del)
    del k

# 4.NDVI指数的计算
    # 1) 读取 重采样后的 BO3、BO4、B05 三个波段的tiff文件
    B3_path = outputTiff_path + BandRes_Name[2]
    B4_path = outputTiff_path + BandRes_Name[3]
    B5_path = outputTiff_path + BandRes_Name[4]

    # 2) Cloud_Detection 利用B05 和 B03
    # 读取数据
    Array_B3 = ga.LoadFile(B3_path)
    Array_B4 = ga.LoadFile(B4_path)
    Array_B5 = ga.LoadFile(B5_path)

    # 判断云像元
    resultCloud = np.zeros(Array_B3.shape)
    resultCloud[np.logical_or(Array_B3 > 1200, Array_B5 > 2800)] = -9999

    # 标记Red(B3)、Nir(B4)两波段中 云像元的Value为-9999
    Array_B3[resultCloud == -9999] = -9999
    Array_B4[resultCloud == -9999] = -9999

    # 3) 计算NDVI
    ga.numpy.seterr(all="ignore")
    NDVI_cal = (Array_B4 - Array_B3) / (Array_B4 + Array_B3)
    NDVI = ga.numpy.nan_to_num(NDVI_cal)

    # 4) 保存NDVI结果
    outputPath_NDVI = r'F:\Python\Train_induction\OutData\NDVI\NDVI_20210628_COOD_H8_AHIs.tiff'
    out = ga.SaveArray(NDVI, outputPath_NDVI, format="GTiff", prototype=B4_path)
    out = None

# 5.基于shp数据的裁剪
    # 1) 打开shp数据
    shp_path = r"F:\Python\Train_induction\InputData\SHP\CHN.shp"
    outputPath_Clip = r"F:\Python\Train_induction\OutData\Clip_byshp\NDVI_clip_20210628_COOD_H8_AHIs.tiff"
    ogr.RegisterAll()
    driver_shp = ogr.GetDriverByName("ESRI Shapefile")
    ds_shp = driver_shp.Open(shp_path)

    # 2) 读取shp相关信息，经纬度、分辨率等
    extend_shp = ds_shp.GetLayer().GetExtent()
    lonMin = extend_shp[0]
    lonMax = extend_shp[1]
    latMin = extend_shp[2]
    latMax = extend_shp[3]

    # 3) 裁切结果与shp左、上相切，输出裁剪结果
    outBounds = (extend_shp[0], extend_shp[2], extend_shp[1], extend_shp[3])
    ds_NDVI = gdal.Open(outputPath_NDVI, gdal.GA_ReadOnly)
    x_res = abs(ds_NDVI.GetGeoTransform()[1])
    y_res = abs(ds_NDVI.GetGeoTransform()[5])
    ds = gdal.Warp(outputPath_Clip, outputPath_NDVI, format='GTiff', outputBounds=outBounds, dstNodata=-9999,
                   cutlineDSName=shp_path, cropToCutline=False, xRes=x_res, yRes=y_res)


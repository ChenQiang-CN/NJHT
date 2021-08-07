# -*- coding:utf-8 -*-
# Created on 2021/7/31 by luren

import numpy as np
import os
import h5py
from osgeo import gdal
from osgeo import osr
from osgeo.gdal import gdalconst


# Q1: hdf到tiff数据的格式转换
def Data2Tiff(original_data, file_path, tiff_file, extend, reso):
    """
    :param original_data: hdf array of single band.
    :param file_path: direct of output file.
    :param tiff_file: name of output file.
    :param extend: extend of original data.
    :param reso: resolution (km).
    :return: raster band.
    """
    gtiff_driver = gdal.GetDriverByName('GTiff')
    cols = original_data.shape[1]
    rows = original_data.shape[0]
    # print(cols, rows)
    out_ds = gtiff_driver.Create(file_path + tiff_file, cols, rows, 1, gdal.GDT_Float32)
    geoTrans = [extend[0], reso / 100, 0, extend[3], 0, -reso / 100]
    # [left-top lon, lon step, z_twist0, left-top lat, lat step, z_twist1]
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326)  # Lon-lat equal projection
    out_ds.SetProjection(sr.ExportToWkt())
    out_ds.SetGeoTransform(geoTrans)
    out_band = out_ds.GetRasterBand(1)  # Starting from 1
    out_band.WriteArray(original_data)
    del out_ds

    return


def ImgRes(input_file, input_path, output_file, output_path, ResRatio):
    """
    :param input_file: data to transform.
    :param input_path: direct of input file.
    :param output_file: new data.
    :param output_path: direct of input file.
    :return
    """
    inFile = os.path.join(input_path, input_file)
    ds_in = gdal.Open(inFile, gdal.GA_ReadOnly)
    proj_in = ds_in.GetProjection()
    trans_in = ds_in.GetGeoTransform()
    width_in = ds_in.RasterXSize
    height_in = ds_in.RasterYSize
    band_in = ds_in.GetRasterBand(1)
    # nan_in = band_in.GetNoDataValue()

    width_out = int(width_in / ResRatio)
    height_out = int(height_in / ResRatio)
    trans_out = list(trans_in)
    trans_out[1] = trans_out[1] * ResRatio
    trans_out[5] = trans_out[5] * ResRatio
    driver_out = gdal.GetDriverByName('GTiff')
    ds_out = driver_out.Create(output_path + output_file, width_out, height_out, 1, band_in.DataType)
    ds_out.SetGeoTransform(trans_out)
    ds_out.SetProjection(proj_in)
    band_out = ds_out.GetRasterBand(1)
    # band_out.SetNoDataValue()
    gdal.ReprojectImage(ds_in, ds_out, proj_in, proj_in, gdalconst.GRA_Bilinear, 0.0, 0.0)

    return


file_path = 'exercise2_data/HDF/'
hdf_file = '202106280700.hdf'
resolution = [1, 1, 0.5, 1]
resolution.extend([2] * 12)

with h5py.File(file_path + hdf_file, 'r') as hdf_file:
    # print(hdf_file.attrs.keys())  # ['extend', 'file_time_UTC', 'version']
    extend = hdf_file.attrs['extend']  # [72, 136, 17, 55]
    # print(extend)
    band_name = list(hdf_file.keys())

    for i in range(len(band_name)):
        tiff_file = f'202106280700_{i + 1}.tiff'
        data = hdf_file[band_name[i]][:]
        # print(data.max(), data.min())
        Data2Tiff(data, file_path, tiff_file, extend, resolution[i])

        # Q2: tiff数据的重采样
        if not resolution[i] == 2:
            new_file = f'202106280700_{i + 1}_new.tiff'
            ratio = 2 / resolution[i]
            ImgRes(tiff_file, file_path, new_file, file_path, ratio)

        # Q3: tiff数据的裁剪
        # inputPath = os.path.join(file_path, f'202106280700_{i + 1}_raw.tiff')
        # outputPath = os.path.join(file_path, f'202106280700_{i + 1}.tiff')
        # shpPath = 'exercise2_data/SHP/CHN.shp'
        # ds_raw = gdal.Open(inputPath, gdal.GA_ReadOnly)
        # xRes = ds_raw.RasterXSize
        # yRes = ds_raw.RasterYSize
        # ds = gdal.Warp(outputPath, inputPath, format='GTiff', cutlineDSName=shpPath,
        #                cropToCutline=False, xRes=xRes, yRes=yRes)

















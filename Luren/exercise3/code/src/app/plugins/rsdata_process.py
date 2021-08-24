# -*- coding:utf-8 -*-
# Created on 2021/7/31 by luren

import numpy as np
import os
import h5py
from osgeo import gdal, osr, ogr


# Q1: hdf到tiff数据的格式转换
def hdf2tiff(input_hdf, tiff_path):
    """
    :param input_hdf:
    :param tiff_path:
    :return: dictionary of key=tiff name, value=tiff file
    """
    tiff_dict = {}
    with h5py.File(input_hdf, 'r') as hdf_file:
        extend = hdf_file.attrs['extend']  # 4个边界
        band_list = list(hdf_file.keys())  # 波段的名字
        for band_name in band_list:
            data = hdf_file[band_name][:]  # 二维数组
            gtiff_driver = gdal.GetDriverByName('GTiff')  # 创建Tiff
            tiff_name = band_name + '.tiff'
            out_path = os.path.join(tiff_path, tiff_name)
            tiff_dict[tiff_name] = out_path  # 将波段名称和对应文件存入字典
            cols = data.shape[1]
            rows = data.shape[0]
            out_ds = gtiff_driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)  # 注意row和column的顺序
            res_width = (extend[1] - extend[0]) / cols
            res_height = - (extend[3] - extend[2]) / rows
            geoTrans = [extend[0], res_width, 0, extend[3], 0, res_height]
            # [左上角经度，经度步长，z扭曲，左上角纬度，z扭曲，纬度步长]
            sr = osr.SpatialReference()
            sr.ImportFromEPSG(4326)
            out_ds.SetProjection(sr.ExportToWkt())
            out_ds.SetGeoTransform(geoTrans)
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(data)
            del out_ds
    return tiff_dict


# Q2: tiff数据的重采样
def tiff_resample(in_tif_path, cell_size, out_tif_path):
    """
    :param in_tif_path: 输入的 tif 路径
    :param out_tif_path: 输出的 tif 路径
    :param cell_size: 重采样之后的栅格单元的大小，单位和之前的单位保持一致，之前是用 度 现在还是用 度， 之前是 m 现在是 m
    :return: None
    """
    if isinstance(in_tif_path, gdal.Dataset):
        ds = in_tif_path
    else:
        ds = gdal.Open(in_tif_path)
    # 栅格单元长宽
    im_geotrans = ds.GetGeoTransform()
    pixel_width, pixel_height = im_geotrans[1], im_geotrans[5]
    # 长宽变化的倍数，5 代表 扩大五倍， 那么读取的行列要变为之前的 五分之一
    width_times = abs(cell_size / pixel_width)
    height_times = abs(cell_size / pixel_height)
    # 图像的长宽
    im_width = ds.RasterXSize  # 栅格矩阵的列数
    im_height = ds.RasterYSize  # 栅格矩阵的行数
    # 计算读取的图像的长宽栅格数目
    new_im_width = int(im_width / width_times)
    new_im_height = int(im_height / height_times)
    # 获取重采样之后的数据
    im_data = []
    for i in range(1, ds.RasterCount + 1):
        band_i = ds.GetRasterBand(i)
        data_i = band_i.ReadAsArray(buf_xsize=new_im_width, buf_ysize=new_im_height)
        im_data.append(data_i)
    # 多波段数据和单波段数据分开处理
    if len(im_data) == 1:
        im_data = np.array(im_data[0])
    else:
        im_data = np.array(im_data)
    # 获得新的 tif 的各个参数 GetGeoTransform
    new_im_geotrans = list(im_geotrans)
    new_im_geotrans[1] = cell_size
    new_im_geotrans[5] = -cell_size
    im_bands = ds.RasterCount
    im_proj = ds.GetProjection()  # 获取投影信息
    # 保存数据
    write_tiff(im_data, new_im_width, new_im_height, im_bands, new_im_geotrans, im_proj, out_path=out_tif_path)


# Q3: NDVI计算包含去云
def cal_ndvi(band_nir, band_red, band_five, band_three):
    """
    :param band_nir:近红外波段
    :param band_red:红光波段
    :param band_five:第五波段
    :param band_three:第三波段
    :return:
    """
    # 判断云像元
    cloud = np.zeros(band_five.shape)
    cloud[np.logical_or(band_three > 1200, band_five > 2800)] = -9999
    # 计算NDVI
    ndvi = (band_nir - band_red) / (band_nir + band_red)
    # 云像元赋值为-9999
    ndvi[cloud == -9999] = -9999
    return ndvi


# Q4: 裁剪矢量外边界
def clip_tiff(in_raster_file, shp_file, out_raster_file=None):
    """
    :param in_raster_file: string  in put shp file
    :param shp_file:CHN中国shp
    :param out_raster_file:裁剪后的tiff
    :return:
    """
    ds_raster = gdal.Open(in_raster_file)
    ds_shp = ogr.Open(shp_file)
    layer = ds_shp.GetLayer()
    extent = layer.GetExtent()  # 西，东，南，北
    output_bounds_args = (extent[0], extent[2], extent[1], extent[3])
    if out_raster_file is None:
        file_ary = os.path.splitext(in_raster_file)
        out_raster_file = file_ary[0] + "_clip" + file_ary[1]
    gdal.Warp(out_raster_file, ds_raster, format="GTiff", cutlineDSName=shp_file, outputBounds=output_bounds_args,
              cropToCutline=True, dstNodata=-9999)
    ds_shp.Destroy()
    del ds_raster
    return True


def read_tiff(path):
    """
    :param path
    :return: information of dataset
    """
    if isinstance(path, gdal.Dataset):
        dataset = path
    else:
        dataset = gdal.Open(path)

    if dataset:
        width = dataset.RasterXSize  # 栅格矩阵的列数
        height = dataset.RasterYSize  # 栅格矩阵的行数
        bands = dataset.RasterCount  # 波段数
        proj = dataset.GetProjection()  # 获取投影信息
        geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
        data = dataset.ReadAsArray(0, 0, width, height)  # 获取数据
        return data, width, height, bands, geotrans, proj
    else:
        print('fail')


def write_tiff(im_data, im_width, im_height, im_bands, im_geotrans, im_proj,
               out_path=None, nodata_value=None, return_mode='TIFF'):
    """
    :param im_data:
    :param im_width:
    :param im_height:
    :param im_bands:
    :param im_geotrans:
    :param im_proj:
    :param out_path:
    :param nodata_value: 无效值
    :param return_mode: TIFF（保存为本地文件）, MEMORY（保存为缓存）
    :return:
    """
    # 保存的数据类型
    if 'int8' in im_data.dtype.name or 'bool' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32
    # 处理为三维矩阵
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data], dtype=im_data.dtype)
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    # 根据存储类型的不同，获取不同的驱动
    if out_path:
        dataset = gdal.GetDriverByName('GTiff').Create(out_path, im_width, im_height, im_bands, datatype)
    else:
        dataset = gdal.GetDriverByName('MEM').Create('', im_width, im_height, im_bands, datatype)
    # 写入数据
    if dataset is not None:
        dataset.SetGeoTransform(im_geotrans)
        dataset.SetProjection(im_proj)
    # 写入矩阵
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
        # 写入无效值
        if nodata_value is not None:
            # 当每个图层有一个无效值的时候
            if isinstance(nodata_value, list) or isinstance(nodata_value, tuple):
                if nodata_value[i] is not None:
                    dataset.GetRasterBand(i + 1).SetNoDataValue(nodata_value[i])
            else:
                dataset.GetRasterBand(i + 1).SetNoDataValue(nodata_value)
    # 根据返回类型的不同，返回不同的值
    if return_mode.upper() == 'MEMORY':
        return dataset
    elif return_mode.upper == 'TIFF':
        del dataset
    return True


if __name__ == "__main__":
    hdf_path = r'/Users/luren/Documents/GitHub/NJHT/Luren/exercise2/exercise2_data/HDF/202106280700.hdf'
    tiff_folder = r'/Users/luren/Documents/GitHub/NJHT/Luren/exercise2/exercise2_data/HDF'
    shp_path = r'/Users/luren/Documents/GitHub/NJHT/Luren/exercise2/exercise2_data/SHP/CHN.shp'

    # Step 1
    tiff_dict = hdf2tiff(hdf_path, tiff_folder)

    # Step 2
    # B03
    b3_tif = tiff_dict['B03.tiff']
    b3_tif_res = os.path.join(tiff_folder, 'B03_res.tiff')
    tiff_resample(b3_tif, 0.02, b3_tif_res)
    b3_res_data, width, height, bands, geotrans, proj = read_tiff(b3_tif_res)
    # B04
    b4_tif = tiff_dict['B04.tiff']
    b4_tif_res = os.path.join(tiff_folder, 'B04_res.tiff')
    tiff_resample(b4_tif, 0.02, b4_tif_res)
    b4_res_data = read_tiff(b4_tif_res)[0]
    # B05
    b5_tif = tiff_dict['B05.tiff']
    b5_tif_res = os.path.join(tiff_folder, 'B05_res.tiff')
    tiff_resample(b5_tif, 0.02, b5_tif_res)
    b5_res_data = read_tiff(b5_tif_res)[0]

    # Step 3
    ndvi_path = os.path.join(tiff_folder, 'ndvi.tiff')
    ndvi_data = cal_ndvi(b4_res_data, b3_res_data, b5_res_data, b3_res_data)
    write_tiff(ndvi_data, width, height, bands, geotrans, proj, out_path=ndvi_path)
    # Process 4:tiff clip
    clip_path = os.path.join(tiff_folder, 'ndvi_clip.tiff')
    clip_tiff(ndvi_path, shp_path, out_raster_file=clip_path)
    print('success')




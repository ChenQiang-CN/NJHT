# @Time : 2021/8/8
# @Author : zhangtao

import h5py
import os
import re
import h5py
from osgeo import gdal, osr
import numpy as np
import shutil

def read_tif_form_hdf(path_hdf,path_tem):
    """
    根据hdf的文件路径（path_hdf）逐一读取tif文件保存到相应文件夹中（path_tem）
    """
    path_tiflist_tem = []
    with h5py.File(path_hdf,'r') as hdf_file:
        extend = hdf_file.attrs['extend']
        band_name = list(hdf_file.keys())
        #data = hdf_file[band_name[-1]][()]
        for i in band_name:
            data = hdf_file[i][()]
            gtiff_driver = gdal.GetDriverByName('GTiff')
            name_tif = i + '.tif'
            path_tif = os.path.join(path_tem,name_tif)
            path_tiflist_tem.append(path_tif)
            out_ds = gtiff_driver.Create(path_tif,data.shape[1],data.shape[0],1,gdal.GDT_Float32)
            a = (extend[1] - extend[0]) / data.shape[1]
            b = - (extend[3] - extend[2]) / data.shape[0]
            geoTrans = [extend[0],a,0,extend[3],0,b]
            sr = osr.SpatialReference()
            sr.ImportFromEPSG(4326)
            out_ds.SetProjection(sr.ExportToWkt())
            out_ds.SetGeoTransform(geoTrans)
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(data)
            del out_ds
    return path_tiflist_tem

def Resample_move(path_outputtif,path_tiflist_tem):
    """
    将列表path_tiflist_tem内的tif文件部分重采样，部分进行移动，目标文件夹为path_outputtif，返回目标文件夹下的各个tif的list
    """
    path_tiflist = []
    for i in path_tiflist_tem:
        tif_name = os.path.basename(i)
        path_tif = os.path.join(path_outputtif,tif_name)
        if tif_name in ['B01.tif','B02.tif','B03.tif','B04.tif']:
            _ =  gdal.Warp(path_tif,i,width = 3200,height = 1900,format="GTiff")
        else:
            _ = shutil.move(i,path_tif)
        path_tiflist.append(path_tif)
    return path_tiflist

def cut_by_shp(path_outputtif,path_tiflist,path_shp):
    """
    使用path_shp的shp文件对path_tiflist列表内的tif文件进行裁剪，裁剪结果保存到path_outputtif路径下，返回裁剪完的tif文件列表，名称以“_cut.tif”结尾
    """
    path_tif_cutlist = []
    for i in path_tiflist:
        tif_name_cut = os.path.basename(i).split(".")[0] + "_cut.tif"
        path_tif_cut = os.path.join(path_outputtif,tif_name_cut)
        ds = gdal.Open(i)
        _ = gdal.Warp(path_tif_cut,
                  ds,
                  format = 'GTiff',
                  cutlineDSName = path_shp,                  
                  dstNodata = 0) 
        path_tif_cutlist.append(path_tif_cut)
    return path_tif_cutlist

def cloud_identification(path_outputtif,path_tif_cutlist):
    """
    使用裁剪完tif列表path_tif_cutlist的第三、五个波段进行识别云，结果为tif文件保存到path_outputtif下并返回
    """
    tif_B03 = gdal.Open(path_tif_cutlist[2])
    im_width = tif_B03.RasterXSize
    im_height = tif_B03.RasterYSize
    data_B03 = tif_B03.ReadAsArray(0,0,im_width,im_height)
    tif_B05 = gdal.Open(path_tif_cutlist[4])
    im_width = tif_B05.RasterXSize
    im_height = tif_B05.RasterYSize
    data_B05 = tif_B05.ReadAsArray(0,0,im_width,im_height)
    data_B03 = np.where(data_B03>1200,1,0)
    data_B05 = np.where(data_B05>2800,1,0)
    cloud_data = data_B05 + data_B03
    cloud_data = np.where(cloud_data>0,1,0)

    #cloud_data = np.zeros((data_B03.shape))
    #cloud_data[np.where((data_B03>1200 or data_B05>2800))] = 1
    gtiff_driver = gdal.GetDriverByName('GTiff')
    path_cloud = os.path.join(path_outputtif,'cloud.tif')
    out_ds = gtiff_driver.Create(path_cloud,data_B03.shape[1],data_B03.shape[0],1,gdal.GDT_Float32)
    _ = out_ds.SetProjection(tif_B03.GetProjection())
    _ = out_ds.SetGeoTransform(tif_B03.GetGeoTransform())
    out_band = out_ds.GetRasterBand(1)
    _ = out_band.WriteArray(cloud_data)
    del out_ds
    return path_cloud

def NDVI_com(path_outputtif,path_tif_cutlist):
    """
    使用裁剪完tif列表path_tif_cutlist的第三、四个波段计算NDVI指数，结果为tif文件保存到path_outputtif下并返回
    """
    tif_red = gdal.Open(path_tif_cutlist[2])
    im_width = tif_red.RasterXSize
    im_height = tif_red.RasterYSize
    data_red = tif_red.ReadAsArray(0,0,im_width,im_height)

    tif_nir = gdal.Open(path_tif_cutlist[3])
    im_width = tif_nir.RasterXSize
    im_height = tif_nir.RasterYSize
    data_nir = tif_nir.ReadAsArray(0,0,im_width,im_height)

    NDVI_data = (data_nir - data_red)/(data_nir + data_red)
    gtiff_driver = gdal.GetDriverByName('GTiff')
    path_NDVI = os.path.join(path_outputtif,'NDVI.tif')
    out_ds = gtiff_driver.Create(path_NDVI,data_red.shape[1],data_red.shape[0],1,gdal.GDT_Float32)
    _ = out_ds.SetProjection(tif_red.GetProjection())
    _ = out_ds.SetGeoTransform(tif_red.GetGeoTransform())
    out_band = out_ds.GetRasterBand(1)
    _ = out_band.WriteArray(NDVI_data)
    del out_ds
    return path_NDVI

if __name__ == "__main__":
    path_hdf = "E:/zhangtao/exercise2/data/HDF/202106280700.hdf"
    path_outputtif = "E:/zhangtao/exercise2/output"
    path_tem = "E:/zhangtao/exercise2/output/tem"
    path_shp = "E:/zhangtao/exercise2/data/SHP/CHN.shp"
    path_tiflist_tem = read_tif_form_hdf(path_hdf,path_tem)
    path_tiflist = Resample_move(path_outputtif,path_tiflist_tem)
    path_tif_cutlist = cut_by_shp(path_outputtif,path_tiflist,path_shp)
    _ = cloud_identification(path_outputtif,path_tif_cutlist)
    _ = NDVI_com(path_outputtif,path_tif_cutlist)

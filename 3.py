<? xml版本= " 1.0 "编码= " UTF-8 " ?>
 < xml 标识= " NDVI " >
    < input des = "输入文件" identify = " inputFile " type = " string " >E:/wh/exercise3/data/H08_20210722_0400_MULT_geo_cor.tif</ input >
    < input des = "区域信息" identify = " areaID " type = " string " >QHS</ input >
    <输入 DES = “期次” 标识= “问题” 类型= “字符串” > 202107220000 </输入>
    < input des = "生命周期" identify = " cycle " type = " string " >COOD</ input >
 < output des = "输出目录" identify = " outFolder " type = " string " >E:\wh\exercise3\htht\output</ output >
 < output des = "输出xml路径" identify = " outXMLPath " type = " string " >E:\wh\exercise3\output\202002230000.xml</ output >
 < output des = "输出日志路径" identify = " outLogPath " type = " string " >E:\wh\exercise3\output\202002230000.log</ output >
 </ xml >
osge
from o import gdal
import os
import time
import numpy as np

img_root = "C:\Users\wh\Desktop\htht\data"
img_type = (".img", ".dat", "tiff")
driver = gdal.GetDriverByName('GTiff')
result_name_temp = "temp2.tiff"
start = time.clock()

result_path = os.path.join(img_root, result_name_temp)
# 文件存在则删除文件
if os.path.exists(result_path):
    os.remove(result_path)

rater_file = "C:\Users\wh\Desktop\htht\data\202002230000.img"


def get_ndvi(path):  # 计算某一影像的ndvi值，返回二维数组
    dataset = gdal.Open(path)
    cols = dataset.RasterXSize  # 列数
    rows = dataset.RasterYSize  # 行数

    band8 = dataset.GetRasterBand(8).ReadAsArray(0, 0, cols, rows)
    band4 = dataset.GetRasterBand(4).ReadAsArray(0, 0, cols, rows)
    molecule = band8 - band4
    denominator = band8 + band4
    del dataset
    band = molecule / denominator
    band[band > 1] = 9999  # 过滤异常值
    return band


def compute_band(file):
    dataset = gdal.Open(file)
    cols = dataset.RasterXSize  # 列数
    rows = dataset.RasterYSize  # 行数
    # 生成影像
    target_ds = gdal.GetDriverByName('GTiff').Create(result_path, xsize=cols, ysize=rows, bands=1,
                                                     eType=gdal.GDT_Float32)
    target_ds.SetGeoTransform(dataset.GetGeoTransform())
    target_ds.SetProjection(dataset.GetProjection())
    del dataset
    band = get_ndvi(file)
    target_ds.GetRasterBand(1).SetNoDataValue(9999)
    target_ds.GetRasterBand(1).WriteArray(band)
    target_ds.FlushCache()


compute_band(rater_file)
elapsed = (time.clock() - start)
print("计算ndvi耗时:", elapsed)
osge
from o import gdal
import os
import time
import numpy as np

img_root = "C:\Users\朱大漂亮\Desktop\htht\data"
img_type = (".img", ".dat", "tiff")
driver = gdal.GetDriverByName('GTiff')
result_name_temp = "temp2.tiff"
start = time.clock()

result_path = os.path.join(img_root, result_name_temp)
# 文件存在则删除文件
if os.path.exists(result_path):
    os.remove(result_path)

rater_file = "C:\Users\朱大漂亮\Desktop\htht\data\50smc_20190604t025551_b01.img"


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

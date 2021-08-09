import gdal
import h5py
import numpy as np
from osgeo import osr, ogr
#打开hdf文件，建立坐标系
with h5py.File(r'D:\study\data\HDF\202106280700.hdf', 'r') as file:
    key = list(file.keys())
    bandname = key[0:11]
    data = file[bandname[0]][()]
    content = file['B01'][:]
    extend =file.attrs['extend']
    Lon = int(extend[1]-extend[0])
    Lat = int(extend[3]-extend[2])
    xsize = int(Lon/0.005) #横坐标
    ysize = int(Lat/0.005) #纵坐标
    data1 = np.array(data)
#生成TIF文件
driver = gdal.GetDriverByName("GTiff")
out_tiff_name = '202106280700.tiff'
out_tiff = driver.Create(out_tiff_name, xsize, ysize, 1, gdal.GDT_Float32)
#设置图像范围
geotransform = [extend[0], 0.005, 0, extend[3], 0, -0.005] #分别对应西北角横坐标、水平方向分辨率、旋转参数、西北角y坐标、旋转参数、竖直方向分辨率
out_tiff.SetGeoTransform(geotransform)
#获取地理坐标信息
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326) #WG84
out_tiff.SetProjection(srs.ExportToWkt()) #设置投影信息
band = out_tiff.GetRasterBand(1)
band.WriteArray(data1)
out_tiff = None


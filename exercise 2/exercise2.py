from osgeo import gdal
import os
import arcpy

# hdf各波段数据to tiff转换
arcpy.env.overwriteOutput = 1
arcpy.CheckOutExtension("Spatial")
inPath='D:\_B学习资料\01遥感算法培训\课程2\data\HDF\202106280700.hdf'
outPath='D:\_B学习资料\01遥感算法培训\课程2\output'
arcpy.env.workspace = inPath
hdfList = arcpy.ListRasters('*','HDF')
for hdf in hdfList:
    Name = hdf[0:13] + ".tif"
    data = arcpy.ExtractSubDataset_management(hdf,outPath + Name, "0")
print "OK！"

# TIFF的重采样
path=r"D:\_B学习资料\01遥感算法培训\课程2\data\HDF"
os.chdir(path)
in_ds=gdal.Open("p047r027_7t20000730_z10_nn10.tif")
in_band=in_ds.GetRasterBand(1)
xsize=in_band.XSize
ysize=in_band.YSize
geotrans=list(in_ds.GetGeoTransform())
geotrans[1]/=2#像元宽度变为原来的0.5倍
geotrans[5]/=2#像元高度变为原来的0.5倍
#重采样后的影像
if os.path.exists('resampled.tif'):#如果已存在同名影像
    os.remove('resampled.tif')#则删除之
out_ds=in_ds.GetDriver().Create('resampled.tif',xsize*2,ysize*2,1,in_band.DataType)#创建一幅重采样后的影像的句柄，行列数都变成原来的2倍
out_ds.SetProjection(in_ds.GetProjection())#设置投影坐标
out_ds.SetGeoTransform(geotrans)#设置地理变换参数
data=in_band.ReadAsArray(buf_xsize=xsize*2, buf_ysize=ysize*2)#使用更大的缓冲读取影像，与重采样后影像行列对应
out_band=out_ds.GetRasterBand(1)
out_band.WriteArray(data)#写入数据到新影像中
out_band.FlushCache()
out_band.ComputeBandStats(False)#计算统计信息
out_ds.BuildOverviews('average',[1,2,4,8,16,32])#构建金字塔
del out_ds#删除句柄
del in_ds
print("This process has succeeded!")

# 基于shpfile的裁剪

clipfilename = 'D:\_B学习资料\01遥感算法培训\课程2\data\SHP'
outputfilename = 'D:\_B学习资料\01遥感算法培训\课程2\data\clipped'


def clip(inputfilename, clipfilename, outputfilename):
    '''
    usage: clip a layer through an input Methodlayer like ArcMAP clip tool\n
    parameters:
    inputfilename type str,
    clipfilename type str,
    outputfilename type str
    '''
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inputDataSource = driver.Open(inputfilename, 0)
    clipDataSource = driver.Open(clipfilename, 0)
    outputDataSource = driver.CreateDataSource(outputfilename)

    inputLayer = inputDataSource.GetLayer(0)
    clipLayer = clipDataSource.GetLayer(0)
    papszLCO = []
    outputLayer = outputDataSource.CreateLayer('clipped', None, ogr.wkbPoint, papszLCO)

    Defn = inputLayer.GetLayerDefn()
    for i in range(Defn.GetFieldCount()):
        outputLayer.CreateField(Defn.GetFieldDefn(i))
    outputLayer = outputDataSource.GetLayer(0)

    strFilter = "LAND_USE_T like '25%'"
    clipLayer.SetAttributeFilter(strFilter)
    inputLayer.Clip(clipLayer, outputLayer)

    outputDataSource.Release()
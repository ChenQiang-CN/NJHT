#hdf的各波段数据的to tiff转换
import arcpy
import os
try:
for dirpath, dirnames, filenames in os.walk("D:\\researchdata\\MODISdown\\MYD11A1\\LST2003-2017"):
for file in filenames :
if os.path.splitext(file)[1] == '.hdf':
arcpy.ExtractSubDataset_management("D:\\researchdata\\MODISdown\\MYD11A1\\LST2003-2017\\"+file, "D:\\researchdata\\MODISdown\\MYD11A1\\TIFF2003-2009\\"+os.path.splitext(file)[0]+".tif", "0")

break
except:
print "Extract Subdataset example failed."
print arcpy.GetMessages()

#基于python2.7和arcpy重采样tif文件
def Resample_modis(tif_path, out_path):
    # python2.7连接arcgis
    import sys
    arcpy_path = [r'C:\\Python27\\ArcGIS10.5\\lib\\site-packages',
                  r'C:\\Program Files (x86)\\ArcGIS\\Desktop10.5\\bin',
                  r'C:\\Program Files (x86)\\ArcGIS\\Desktop10.5\\ArcPy',
                  r'C:\\Program Files (x86)\\ArcGIS\\Desktop10.5\\ArcToolBox\\Scripts',
                  ]
    sys.path.extend(arcpy_path)
    # arcgis重采样
    import arcpy
    # 批量读取tif文件
    arcpy.env.workspace = tif_path  # 定义tif所在的文件夹
    NCfiles = arcpy.ListFiles("*.tif")  # 所有的tif
    # 90*90
    for i in NCfiles:
        print
        'resample_modis: resample file ' + i + ' to new resample'
        inNCfiles = arcpy.env.workspace + "/" + i
        fileroot = i[0:(len(i) - 4)]
        outfile = out_path
        outfilepath = outfile + '/' + fileroot + '.tif'
        arcpy.Resample_management(inNCfiles, outfilepath, "90 90", "NEAREST")

#基于shp数据对栅格影像进行裁剪
    #读取影像
        import rasterio as rio

        band = rio.open(path)

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

dst = rio.open(newtiffname, 'w', **kwargs)

for i in range(1, src.count + 1):
    reproject(
        source = rio.band(src, i),
        destination = rio.band(dst, i),
        src_transform = src.affine,
        src_crs = src.crs,
        dst_transform = affine,
        dst_crs = dst_crs,
        dst_nodata = src.nodata,
        resampling = RESAMPLING.bilinear)

    #切割
    from geopandas import GeoSeries

    features = [shpdata.geometry.__geo_interface__]
    from geopandas import GeoSeries
    features = [GeoSeries(shpdata.geometry[i]).__geo_interface__]

    import rasterio.mask

    out_image, out_transform = rio.mask.mask(src, features, crop=True, nodata=src.nodata)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    band_mask = rasterio.open(newtiffname, "w", **out_meta)
    band_mask.write(out_image)


#批量计算遥感图像NDVI
    from PIL import Image
    import numpy as np
    from osgeo import gdal
    import glob
    import cv2
    list_tif = glob.glob('H:/gdal/test-data/cut-test/*.tif')
    out_path = 'H:/gdal/test-data/ndvi-test/'
    for tif in list_tif:
    in_ds = gdal.Open(tif)


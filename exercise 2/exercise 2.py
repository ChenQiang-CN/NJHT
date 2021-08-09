#hdf文件转tiff格式
import os
import arcpy
from arcpy import env
 
sourceDir=u'C:\Users\Lenovo\Desktop\data' 
targetDir=u'C:\Users\Lenovo\Desktop\2' 
 
arcpy.CheckOutExtension("Spatial")
env.workspace = sourceDir
arcpy.env.scratchWorkspace = sourceDir
hdfList = arcpy.ListRasters('*','hdf')
for hdf in hdfList:
    print hdf
    eviName=os.path.basename(hdf).replace('hdf','tif')
    outname=targetDir+'\\'+eviName
    print outname
    data1=arcpy.ExtractSubDataset_management(hdf,outname, "Eight_Day_Snow_Cover") 
##	
print 'all done'

#tiff重采样
import arcpy
    arcpy.env.workspace = r"C:\Users\Lenovo\Desktop\2_tif"
    rasterList = arcpy.ListRasters("*","tif")
    output_path1 = "C:\Users\Lenovo\Desktop" 
    for raster in rasterList:
        print raster
        inRaster = raster	
        out = output_path1 + inRaster
        arcpy.Resample_management(inRaster, out, "0.5", "CUBIC")
 
 
 
import arcpy
    from arcpy import env
    from arcpy.sa import *
    arcpy.env.workspace = r"C:\Users\Lenovo\Desktop\resample"
    rasterList = arcpy.ListRasters("*","tif")
    for raster in rasterList:
        print raster
        inRaster = raster
        arcpy.CheckOutExtension("Spatial")
        outExtractByMask = ExtractByMask(inRaster,"xzq_project.shp")
        outExtractByMask.save("C:\Users\Lenovo\Desktop\2"+raster)

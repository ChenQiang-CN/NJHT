outputfilePath = 'D:/studyprojects/gdal/GdalStudy/Files/images/202106280700.tif'
inputfilePath='D:/studyprojects/gdal/GdalStudy/Files/images/202106280700.tif'
referencefilefilePath='D:/studyprojects/gdal/GdalStudy/Files/images/202106280700.tif'
def ReprojectImages():
    # 获取输出影像信息
    inputrasfile = gdal.Open(inputfilePath, gdal.GA_ReadOnly)
    inputProj = inputrasfile.GetProjection()
    # 获取参考影像信息
    referencefile = gdal.Open(referencefilefilePath, gdal.GA_ReadOnly)
    referencefileProj = referencefile.GetProjection()
    referencefileTrans = referencefile.GetGeoTransform()
    bandreferencefile = referencefile.GetRasterBand(1)
    Width= referencefile.RasterXSize
    Height = referencefile.RasterYSize
    nbands = referencefile.RasterCount
    # 创建重采样输出文件（设置投影及六参数）
    driver = gdal.GetDriverByName('GTiff')
    output = driver.Create(outputfilePath, Width,Height, nbands, bandreferencefile.DataType)
    output.SetGeoTransform(referencefileTrans)
    output.SetProjection(referencefileProj)
    # 参数说明 输入数据集、输出文件、输入投影、参考投影、重采样方法(最邻近内插\双线性内插\三次卷积等)、回调函数
    gdal.ReprojectImage(inputrasfile, output, inputProj, referencefileProj, gdalconst.GRA_Bilinear,0.0,0.0,)

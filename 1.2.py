import gdal
import numpy as np

if __name__ == '__main__':
    dataset = gdal.Open(r"D:\算法培训\tif\tif\true_color_3857.tif")
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_bands = dataset.RasterCount
    im_geotrans = dataset.GetGeoTransform()
    im_proj = dataset.GetProjection()
    print('行列数：',im_width,im_height,'\n波段数：',im_bands,'\n六参数：',im_geotrans,'\n投影信息：',im_proj)



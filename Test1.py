# -- coding: utf-8 --

import os
import gdal
import importlib_metadata
os.environ['PROJ_LIB'] = r'C:\Users\EDZ\miniconda3\Library\share\proj'

print('-------第三方库安装情况-------')
dists = importlib_metadata.distributions()
for dist in dists:
    name = dist.metadata["Name"]
    version = dist.version
    print(f'{name}=={version}')

print('-------栅格文件信息读取-------')
path = 'E:\\徐欢\\算法培训\\NJHT-main\\样例数据\\true_color_3857.tif'
dataset = gdal.Open(path)
im_width = dataset.RasterXSize     # 栅格矩阵的列数
im_height = dataset.RasterYSize    # 栅格矩阵的行数
im_proj = dataset.GetProjection()  # 获取投影信息
print('栅格列数：', im_width, '； 栅格行数：', im_height, '； 投影信息：', im_proj)

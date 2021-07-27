# -- coding: utf-8 --
"""
@author: YZQ
@file: Exercise1.py
@time: 20210723
"""
import os
import sys
import gdal

# 1.输出当前Python环境中的第三方库及相应版本
result = os.popen('pip list').readlines()
for i in result:
    print(i, end='')

# 2.读取样例栅格数据，输出其行列数、投影信息
# 1)读取
FilePath = r"F:\Python\Train_induction\InputData\true_color_3857.tif"
DataSet = gdal.Open(FilePath, gdal.GA_ReadOnly)

# 2)判断文件路径是否正确
if DataSet is None:
    print(f"Destination file not found!\nPlease check the FilePath:{FilePath} ")
    sys.exit(1)
else:
    print(f"The FilePath is:\n{FilePath}\n")

# 3)读取行列数、波段数、投影信息
Rows = DataSet.RasterYSize
Cols = DataSet.RasterXSize
Band = DataSet.RasterCount
Project = DataSet.GetProjection()

# 4)输出结果
print(f'The image size is :\n{Rows} rows x {Cols} colums\n')
print(f'The projection of image is :\n{Project}')

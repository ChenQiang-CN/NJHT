#-*- coding: UTF-8 -*-                                                                  #识别中文
'''
这篇代码是针对MODIS的Snowcover数据，将Hdf多波段数据输出为Tif文件
'''

import arcpy
import glob
import os
import xlrd

arcpy.env.overwriteOutput = 1                                                           #输出文件夹里面已经有内容的，就覆盖掉
arcpy.CheckOutExtension("Spatial")                                                      #检查ArcGIS扩展模块是否可用
inPath='F:\\MODIS_Snow_Cover\\Snow_Cover_Hdf\\'

ls = os.listdir(inPath)                                                                 #读取路径中所有文件，以ls来表示，常用file
#print(ls)                                                                              #输出文件名用于检查
print(len(ls))                                                                          #输出文件总数

for i in ls:                                                                            #遍历ls中的文件
	arcpy.env.workspace = 'F:\\MODIS_Snow_Cover\\Snow_Cover_Hdf\\'+ i
	#脚本中最为常用的环境变量设置就是arcpy.env.workspace，该变量用于定义当前脚本的工作目录（或者称为工作空间）
	# print(arcpy.env.workspace)
	arcpy.env.scratchWorkspace = 'F:\\MODIS_Snow_Cover\\Snow_Cover_Hdf\\'+ i            #（为什么定义临时空间变量作用暂不明）
	hdfList = arcpy.ListRasters('*','HDF')                                              #按名称和栅格类型返回工作空间中的栅格列表(遍历指定类型的文件)，需先设置工作空间环境

	#判断存储最终图像的文件夹是否存在，是则存储，否则创建并存储；注意if和else后一定要加冒号，格式要对齐
	if os.path.exists(r"F:\\MODIS_Snow_Cover\\Snow_Cover_Tif\\"+i):
		for hdf in hdfList:
			#此Hdf文件有两个波段，全部输出，相应的ExtractSubDataset_management 中也要提取对应波段
			for number in range(0,1):
				#将i（i是一串数字）转为字符串，最后两道斜杠一定要，不然不会存进该文件夹中，而是上一级文件夹中
				outPath = 'F:\\MODIS_Snow_Cover\\Snow_Cover_Tif\\'+str(i)+'\\'
				#根据对 HDF 数据集创建新栅格数据集,语法 ExtractSubDataset(in_raster, out_raster, {subdataset_index})
				out = arcpy.ExtractSubDataset_management(hdf,outPath + hdf[0:15] + str(number) + ".tif", number)
	else:
		os.makedirs(r"F:\\MODIS_Snow_Cover\\Snow_Cover_Tif\\"+i)
		for hdf in hdfList:
			for number in range(0,1):
				outPath = 'F:\\MODIS_Snow_Cover\\Snow_Cover_Tif\\'+str(i)+'\\'
				out = arcpy.ExtractSubDataset_management(hdf,outPath + hdf[0:15] + str(number) + ".tif", number)
	print(outPath)
	# print(i)
print "完成"
————————————————
版权声明：本文为CSDN博主「JontyHan」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/qq_38882446/article/details/103461759
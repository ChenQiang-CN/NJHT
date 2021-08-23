import os
import sys
import pandas as pd
import pickle
import h5py
from osgeo import gdal, osr
import numpy as np
import shutil

from src.common.process.ProcessBase import BaseProcess
from src.common.utils.GdalUtils.GeoTiffFile import GdalBase, GdalTools
from src.common.utils.GdalUtils.GdalUtil import GdalUtil
from src.common.utils.BaseUtils.BaseUtil import BaseUtil
from src.common.utils.SysUtil import SysUtil
from src.common.Function.ZonalStatistics import ZonalStatistics
from src.common.Function.ExcelUtilNew import AddWorkBookUtil
from src.common.Function.WordUtil import WordUtil
from src.common.utils.GdalUtils.ShapeFile import ShapeFile

class NDVI(BaseProcess):
    def __init__(self, pluginParam):
        super().__init__(pluginParam)
        self.issue = self.pluginParam.getIssue()
        self.base_name = r"VGT_NDVI_{0}CUR_{1}_COOD_H8_AHI"
        outputdir = self.pluginParam.getOutDir()
        outpath = os.path.join(outputdir,self.name,self.issue[0:6],self.issue+'_COAM')
        self.outpath = outpath
        
        
        self.cols_use_sheet1 = ['name','0-0.1','0.1-0.2','0.2-0.3','0.3-0.4','0.4-0.5','0.5-0.6','0.6-0.7','0.7-0.8','0.8-1.0',]
        self.cols_use_sheet2 = ['name','0-0.1%','0.1-0.2%','0.2-0.3%','0.3-0.4%','0.4-0.5%','0.5-0.6%','0.6-0.7%','0.7-0.8%','0.8-1.0%',]
        self.cols_use_sheet3 = ['name','SUM','MAX','MIN','MEAN']

        self.excel_title_sheet1 = ['面积（平方公里）','0-0.1','0.1-0.2','0.2-0.3','0.3-0.4','0.4-0.5','0.5-0.6','0.6-0.7','0.7-0.8','0.8-1.0',]
        self.excel_title_sheet2 = ['面积比例（%）','0-0.1','0.1-0.2','0.2-0.3','0.3-0.4','0.4-0.5','0.5-0.6','0.6-0.7','0.7-0.8','0.8-1.0',]
        self.excel_title_sheet3 = ['地区','SUM','MAX','MIN','MEAN']
        self.name_sheet = ['面积','比例','特征值']

    def NDVI_com(self,inputpath,outputpath):
        ds = gdal.Open(inputpath)
        data_tif = []
        band_3 = ds.GetRasterBand(3)

        band_4 = ds.GetRasterBand(4)
        band_5 = ds.GetRasterBand(5)

        data_3 = band_3.ReadAsArray()
        data_4 = band_4.ReadAsArray()
        data_5 = band_5.ReadAsArray()

        mask_3 = np.where(data_3 > 1200,1,0)
        mask_5 = np.where(data_5 > 2500,1,0)
        mask_cloud = mask_3 + mask_5
        mask_cloud = np.where(mask_cloud>0,True,False)


        data_3[mask_cloud] = 0
        data_4[mask_cloud] = 0
        NDVI_data = (data_4 - data_3) / (data_4 + data_3) * 10000
        gtiff_driver = gdal.GetDriverByName('GTiff')

        path_NDVI = os.path.join(outputpath,'NDVI.tif')
        out_ds = gtiff_driver.Create(path_NDVI,data_3.shape[1],data_3.shape[0],1,gdal.GDT_Float32)
        _ = out_ds.SetProjection(ds.GetProjection())
        _ = out_ds.SetGeoTransform(ds.GetGeoTransform())
        out_band = out_ds.GetRasterBand(1)
        _ = out_band.WriteArray(NDVI_data)
        return path_NDVI




    def areaClipTif(self, tifPath, areaList):
        """按照行政区划裁切"""
        try:
            dependDir = self.pluginParam.getDependDir()
            shpDir = os.path.join(dependDir, "shp", "SubShpAlbers")

            for regionId in areaList:
                shpPath = os.path.join(shpDir, regionId + ".shp")
                if not BaseUtil.isFile(shpPath):
                    print("未找到裁切文件:", shpPath)
                    continue

                outTifName = self.base_name.format("R", self.issue) + regionId + ".tif"
                # 九段码，将region ID改为行政编码ABB
                # ABB = self.curAreaInfo.getAreaByID(regionId).getAreaABB()
                # outTifName = BaseUtil.fileName(tifPath, ext=False) + "_" + ABB + ".tif"
                # outputdir = self.pluginParam.getOutDir()
                # outTifDir = os.path.join(outputdir,self.name,self.issue[0:6],self.issue+'_COAM')
                
                outTifDir = os.path.join(self.outpath, regionId)
                outTifPath = os.path.join(outTifDir, outTifName)
                BaseUtil.mkDir(outTifDir)
                GdalUtil.rasterClipByShp(tifPath, outTifPath, shpPath)
                if not BaseUtil.isFile(outTifPath):  # 判断一下裁切是否成功
                    print("裁切文件： " + outTifPath + " 失败")
                    continue
                # 最高行政区划TIF复制到GeoServer指定目录下
                if regionId == self.pluginParam.getAreaID():
                    self.tif_add_arcsever(outTifPath)
                    self.tif_add_geoserver(outTifPath)

                # 添加outputXML信息
                if regionId in self.outFileMap:
                    self.outFileMap[regionId].append({"type": ".tif", "file": outTifPath})
                else:
                    self.outFileMap[regionId] = []
                    self.outFileMap[regionId].append({"type": ".tif", "file": outTifPath})
            return True
        except Exception as e:
            self.logObj.error(e)
            return False

    def add_merge_info(self,table_copy):
        """
        设置excel表格的表头消息
        :param table_copy:
        :return: 返回字典列表，字典中有两个属性，merge_value是要写入表格的信息内容，merge_range为写入这个信息的具体位置和范围
        """
        data_merge = []
        for i in range(len(table_copy[0])):
            data_merge.append({'merge_value':table_copy[0][i],
                               'merge_range':(0,1,i,i+1)})
        return data_merge

    def getStaInfoToExcel(self):
        """
              获取统计信息并进行规整
              :return:
        """
        name = [self.curAreaInfo.getAreaByID(i).getAreaName() for i in self.staReClass.index]
        removeQHS_list = self.staReClass.index.to_list()
        removeQHS_list.remove("QHS")

        id_list = [i if i[:1] == "R" or i[:1] == "O" else i[:1] + "00000" for i in removeQHS_list]
        cname = [self.curAreaInfo.getAreaByID(i).getAreaName() for i in id_list]
        cname.insert(0, "青海省")
        self.staReClass['name'] = name
        self.staReClass['cname'] = cname

        staReClass_col = self.staReClass.columns.to_list()
        self.staReClass["all"] = 0
        self.staReClPer["all"] = 0
        for item in staReClass_col[1:5]:
            self.staReClass["all"] = self.staReClass["all"] + self.staReClass[item]
            self.staReClPer["all"] = self.staReClPer["all"] + self.staReClPer[item]

        self.staReClPer.columns = [i + "%" for i in self.staReClPer.columns.to_list()]
        sta_df = pd.concat([self.staReClass, self.staReClPer,self.staCharact], axis=1)
        # 去除 QHS
        need_index = [i for i in sta_df.index if i != 'QHS']
        mean_df_re = sta_df.loc[need_index]
        mean_df_re = mean_df_re.sort_index()
        # 第一行插入QHS信息
        qhs_df = sta_df.loc['QHS'].to_frame().T
        con_df = pd.concat([qhs_df, mean_df_re], axis=0)
        con_df.loc[con_df["cname"] == con_df["name"], "cname"] = "合计"
        return con_df

    def pdToExcel(self, mean_sub_df, area_id):
        """
        将具体的数据写入到excel中
        pd to excel
        :param mean_sub_df:
        :return:
        """
        #根据属性proexcelcols来找出需要导出的具体列，并将数值限定到小数点两位数
        
        for item in self.cols_use_sheet1[1:]:
            mean_sub_df[item] = mean_sub_df[item].map(lambda x: ("%.2f") % x)
        for item in self.cols_use_sheet2[1:]:
            mean_sub_df[item] = mean_sub_df[item].map(lambda x: ("%.2f") % x)
        for item in self.cols_use_sheet3[1:]:
            mean_sub_df[item] = mean_sub_df[item].map(lambda x: ("%.2f") % x)
        
        #excel保存路径
        basename = self.base_name.format("X",self.issue) + '_' + area_id + '.xls'
        #basename = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'XCUR')
        excelPath = os.path.join(self.outpath,area_id, basename)
        excelPath = excelPath.format(id=area_id)
        #重构数据类型为lsit，并将表头信息写入到文件中
        data_sheet1 = mean_sub_df[self.cols_use_sheet1].copy()
        data_sheet2 = mean_sub_df[self.cols_use_sheet2].copy()
        data_sheet3 = mean_sub_df[self.cols_use_sheet3].copy()
        #sheet1
        exc_header = self.excel_title_sheet1
        indexs = mean_sub_df.index.tolist()
        indexs.insert(0, '表头')
        #table_copy = mean_sub_df[exc_cols]
        items = data_sheet1.columns.tolist()
        items = pd.Series({items[i]:exc_header[i] for i in range(len(items))},name="表头")
        data_sheet1 = (data_sheet1.append(items))
        data_sheet1 = data_sheet1.reindex(index=indexs)
        data_sheet1 = list(map(lambda x: list(x),data_sheet1.values))
        #sheet2
        exc_header = self.excel_title_sheet2
        indexs = mean_sub_df.index.tolist()
        indexs.insert(0, '表头')
        #table_copy = mean_sub_df[exc_cols]
        items = data_sheet2.columns.tolist()
        items = pd.Series({items[i]:exc_header[i] for i in range(len(items))},name="表头")
        data_sheet2 = (data_sheet2.append(items))
        data_sheet2 = data_sheet2.reindex(index=indexs)
        data_sheet2 = list(map(lambda x: list(x),data_sheet2.values))

        ###
        exc_header = self.excel_title_sheet3
        indexs = mean_sub_df.index.tolist()
        indexs.insert(0, '表头')
        #table_copy = mean_sub_df[exc_cols]
        items = data_sheet3.columns.tolist()
        items = pd.Series({items[i]:exc_header[i] for i in range(len(items))},name="表头")
        data_sheet3 = (data_sheet3.append(items))
        data_sheet3 = data_sheet3.reindex(index=indexs)
        data_sheet3 = list(map(lambda x: list(x),data_sheet3.values))        
        #将数据写入到excel中
        excel = AddWorkBookUtil()
        merge_info_class_sheet1 = self.add_merge_info(data_sheet1)
        merge_info_class_sheet2 = self.add_merge_info(data_sheet2)
        merge_info_class_sheet3 = self.add_merge_info(data_sheet3)
        excel.add_sheet(data_sheet1, merge_info=merge_info_class_sheet1, sheet_name=self.name_sheet[0], width_adaptation=False)
        excel.add_sheet(data_sheet2, merge_info=merge_info_class_sheet2, sheet_name=self.name_sheet[1], width_adaptation=False)
        excel.add_sheet(data_sheet3, merge_info=merge_info_class_sheet3, sheet_name=self.name_sheet[2], width_adaptation=False)
        if os.path.exists(excelPath):
            os.remove(excelPath)
        excel.save_to_book(excelPath)

        return excelPath

    def getChildAreaList(self,id):
        """
        获取子行政区划信息    县级保留乡级id，省、市级保留到县级id
        :param id:
        :return:
        """
        sub_id = self.curAreaInfo.getAreaByID(id).getAllSubArea()

        if self.curAreaInfo.getAreaByID(id).getLevel() == 20:
            sub_list = sub_id
        else:
            sub_list = [i for i in sub_id if i[-3:] == '000']
        return sub_list

    def exportExcel(self, areaList):
        """
        获得araeLiat中
        :param areaList:
        :return:
        """
        con_df = self.getStaInfoToExcel()


        #con_df = self.getStaInfoToExcel()
        for area_id in areaList:
            need_list = [area_id]  # 当前行政区
            need_list.extend(self.getChildAreaList(area_id))  # 所有下级行政区
            mean_sub_df = con_df.loc[need_list]
            try:
                #修改pdToExcel函数，使其可以接收两个sheet的内容
                excelPath = self.pdToExcel(mean_sub_df,area_id)
                #excelPath = self.pdToExcel(mean_sub_df,area_id)
            except:
                print("Fail to {0} Excel".format(area_id))
                self.logObj.error("Fail to {0} Excel".format(area_id))
                excelPath = ""

            if area_id in self.outFileMap:
                self.outFileMap[area_id].append({"type": ".xlsx", "file": excelPath})
            else:
                self.outFileMap[area_id] = []
                self.outFileMap[area_id].append({"type": ".xlsx", "file": excelPath})

        return True

    def mappingReplaceText(self):
        """出图模块 替换文字信息"""
        issue = self.pluginParam.getIssue()
        #num_of_years = self.pluginParam.getInputInfoByKey("num_of_years")
        ele_dict = {"title": {"yyyy": issue[0:4], "MM": issue[4:6], "dd": issue[6:8]},
                    "date": {"yyyy": issue[0:4], "MM": issue[4:6], "dd": issue[6:8]}}
        return ele_dict

    def mappingReplaceLyr(self, tifPath):
        """出图模块 替换图层"""
        ComShpDir = os.path.join(self.pluginParam.getDependDir(), 'shp', 'CompShpAlbers')
        DRY_HSDir = os.path.join(self.pluginParam.getDependDir(), 'shp', 'landuse')

        Glacier = os.path.join(self.pluginParam.getDependDir(), 'shp', 'glacier', "Glacier_QH.shp")
        Water = os.path.join(DRY_HSDir, "LakesXXXX_P00000_XXXXX_AEA_20100000.shp")
        AreaCity = os.path.join(ComShpDir, "AreaCity.shp")
        AreaCounty = os.path.join(ComShpDir, "AreaCounty.shp")
        AreaXiang = os.path.join(ComShpDir, "AreaXiang.shp")
        AreaProvince = os.path.join(ComShpDir, "AreaProvince.shp")
        lyr_dict = {"tifFile": tifPath,
                    "water": Water,
                    "city": AreaCity,
                    "county": AreaCounty,
                    "xiang": AreaXiang,
                    "province": AreaProvince,
                    "Glacier": Glacier
                    }
        return lyr_dict

    def ExportPic_init(self, tifPath):

        mxdRegionList = ['Province.mxd', 'City.mxd', 'County.mxd']
        pluginName = self.pluginParam.getPluginName()
        mxdDir = os.path.join(self.pluginParam.getDependDir(), 'mxd', pluginName)
        mxdPath = [os.path.join(mxdDir, i) for i in mxdRegionList]

        basename = self.base_name.format("Z", self.issue)
        outPath = os.path.join(self.outpath,'{id}',basename + '_{id}.jpg')
        #outPath = os.path.join(self.curProdDir, '{id}', basename + '_{id}.jpg')
        isDrivenPage = True
        dpi = 300
        outType = '.jpg'

        Pic_dic = {'mxds': mxdPath, 'outPath': outPath, 'isDrivenPage': isDrivenPage, 'dpi': dpi, 'outType': outType}

        return Pic_dic

    def doOthers(self):
        """出功能区图"""
        self.tifPath_alber = self.tifProjChange(self.rsOutMap["OUTFILEPATH"])

        # 生态功能区出专题图
        areaList = self.curAreaInfo.searchArea([11, 21])
        areaList.remove('QHS')
        flagProcess = self.ecoExportPic(self.tifPath_alber, 'Eco.mxd', areaList)

        return flagProcess

    def doInnerPy(self):
        path_hdf = self.pluginParam.getInputInfoByKey('inputFile')
        path_output = self.pluginParam.getInputInfoByKey('outFolder')

        path_NDVI = self.NDVI_com(path_hdf,path_output)

        dependDir = self.pluginParam.getDependDir()
        province_shp = os.path.join(dependDir,'shp','CompShpAlbers','AreaProvince.shp')

        albers_tif = path_NDVI.replace('.tif', '_albers.tif')
        outtif_albers = '{0}/{1}'.format(self.tempDir, os.path.basename(albers_tif))
        GdalUtil.rasterProjection(path_NDVI, outtif_albers, '+proj=aea +ellps=WGS84 +lon_0=96 +lat_0=36 +lat_1=25 +lat_2=47 +datum=WGS84')
            # 裁切
        qhs_tif = path_NDVI.replace('.tif', '_QHS.tif')
        outtif_qhs = '{0}/{1}'.format(self.curProdDir, os.path.basename(qhs_tif))
        GdalUtil.rasterClipByShp(outtif_albers, outtif_qhs, province_shp, bgValue=-9999, mode='GTiff', clipByShp=True) 
        self.rsOutMap["OUTFILEPATH"] = outtif_qhs

    
    def doAnalysis(self):
        #对距平tif文件进行分析
        tifPath = self.rsOutMap["OUTFILEPATH"]
        self.logObj.info("--开始产量计算分析算法文件:{0}".format(tifPath))

        # <栅格投影转换>
        tifPath_alber = self.tifProjChange(tifPath)
        if not tifPath_alber:
            flagProcess = False
            self.logObj.error("--栅格投影转换失败.")
            return flagProcess
        self.logObj.info("--栅格投影转换成功.")
        self.rsOutMap["OUTFILEPATH"] = tifPath_alber

        # <分析区域列表>
        areaList = self.areaList()
        if len(areaList) == 0:
            flagProcess = False
            self.logObj.error("--初始化区域列表失败.")
            return flagProcess
        self.logObj.info("--初始化区域列表成功.")

        # <裁切>
        flagProcess = self.areaClipTif(tifPath_alber, areaList)
        if not flagProcess:
            self.logObj.error("--裁切模块执行失败.")
            return flagProcess
        self.logObj.info("--裁切模块执行成功.")

        # <统计>
        flagProcess = self.areaStatis(tifPath_alber, areaList)
        if not flagProcess:
            self.logObj.error("--统计模块执行失败.")
            return flagProcess
        self.logObj.info("--统计模块执行成功.")

        # <表格>
        flagProcess = self.exportExcel(areaList)
        if not flagProcess:
            self.logObj.error("--excel模块执行失败.")
            return flagProcess
        self.logObj.info("--excel模块执行成功.")

        #出报告
        #flagProcess = self.exportWord(areaList)
        #if not flagProcess:
        #    self.logObj.error("--word模块执行失败.")
        #    return flagProcess
        #self.logObj.info("--word模块执行成功.")

        #出图
        pic_dic = self.ExportPic_init(tifPath_alber)
        flagProcess = self.areaExportPic(tifPath_alber, pic_dic, areaList)
        if not flagProcess:
            self.logObj.error("--出图模块执行失败.")
            return flagProcess
        self.logObj.info("--出图模块执行成功.")

        flagProcess = self.doOthers()
        if not flagProcess:
            self.logObj.error("--出生态功能区图模块执行失败.")
            return flagProcess
        self.logObj.info("--出生态功能区图模块执行成功.")

        return flagProcess

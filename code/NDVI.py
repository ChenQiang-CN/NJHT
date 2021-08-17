"""
============================
# -*- coding: utf-8 -*-
# @Time    : 2021/8/11 10:42
# @Author  : TQ
# @FileName: NDVI.py
# @Software: pycharm

===========================
"""

import os
import platform
import copy
import numpy as np
import pandas as pd
from ...common.process.ProcessBase import BaseProcess
from ...common.utils.GdalUtils.GeoTiffFile import GeoTiffFile
from ...common.utils.GdalUtils.GdalUtil import GdalUtil
from ...common.utils.BaseUtils.BaseUtil import BaseUtil
from src.common.Function.ExcelUtilNew import AddWorkBookUtil
from src.common.Function.WordUtil import WordUtil


os.environ['SHAPE_ENCODING'] = "utf-8"
if platform.system().lower() == 'linux':
    os.environ['GDAL_DATA'] = "/miniconda3/envs/py37_ja/share/gdal"
    os.environ['PROJ_LIB'] = "/miniconda3/envs/py37_ja/lib/python3.7/site-packages/osgeo"
else:
    os.environ['PROJ_LIB'] = r"F:\homework\exercise3\QingHai_py37\Lib\site-packages\osgeo\data\proj"


class NDVI(BaseProcess):
    """归一化植被指数"""

    def __init__(self, pluginParam):
        BaseProcess.__init__(self, pluginParam)
        self.processType = 3
        self.processOther = False
        self.staInitInfo = {}  # 统计初始化信息
        self.depend_dir = self.pluginParam.getDependDir()
        # self.specel_depend_dir = os.path.join(self.depend_dir, "aux_data/Stock_Capacity")
        self.base_name = r"Stock_Capacity_{0}CUR_{1}_COOD_NPP_CIMISS"
        self.issue = self.pluginParam.getIssue()
        self.table_title = "{0}年NDVI".format(self.issue[:4])
        self.excel_title = [["地区", "", "合计", "STD", "MEAN", "MIN", "MAX"]]
        self.proexcelcols = [["name", "cname", "SUM", "STD", "MEAN", "MIN", "MAX"]]


    def doAnalysis(self):

        tifPath = self.rsOutMap["OUTFILEPATH"]
        self.logObj.info("--开始分析算法文件:{0}".format(tifPath))

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

        # # <裁切>
        # flagProcess = self.areaClipTif(tifPath_alber, areaList)
        # if not flagProcess:
        #     self.logObj.error("--裁切模块执行失败.")
        #     return flagProcess
        # self.logObj.info("--裁切模块执行成功.")

        # <统计>
        flagProcess = self.areaStatis(tifPath_alber, areaList)
        if not flagProcess:
            self.logObj.error("--统计模块执行失败.")
            return flagProcess
        self.logObj.info("--统计模块执行成功.")

        # <出图>
        pic_dic = self.ExportPic_init(tifPath_alber)
        flagProcess = self.areaExportPic(tifPath_alber, pic_dic, areaList)
        if not flagProcess:
            self.logObj.error("--出图模块执行失败.")
            return flagProcess
        self.logObj.info("--出图模块执行成功.")
        #
        # # <其他需求>
        # flagProcess = self.doOthers()
        # if not flagProcess:
        #     self.logObj.error("--出生态功能区图模块执行失败.")
        #     return flagProcess
        # self.logObj.info("--出生态功能区图模块执行成功.")

        # <表格>
        flagProcess = self.exportExcel(areaList)
        if not flagProcess:
            self.logObj.error("--excel模块执行失败.")
            return flagProcess
        self.logObj.info("--excel模块执行成功.")

        # 出报告
        flagProcess = self.exportWord(areaList)
        if not flagProcess:
            self.logObj.error("--word模块执行失败.")
            return flagProcess
        self.logObj.info("--word模块执行成功.")

        return flagProcess


    def doInnerPy(self):
        try:
            inputFile = self.pluginParam.getInputFile()
            if inputFile is None or len(inputFile) < 1:
                return None

            # 获取信息
            inputFile = self.pluginParam.getInputInfoByKey("inputFile")
            self.dependDir = self.pluginParam.getDependDir()
            self.cycle = self.pluginParam.getInputInfoByKey("cycle")
            self.issue = self.pluginParam.getInputInfoByKey("issue")
            self.logPath = self.pluginParam.getInputInfoByKey("outLogPath")
            self.month_cur = self.issue[4:6]  # 当前月份
            self.hour_cur = self.issue[8:10]  # 当前小时
            satelliteInfo = self.pluginParam.getPluginName().split("_")[1]
            sensorInfo = self.pluginParam.getPluginName().split("_")[2]
            productName = self.pluginParam.getPluginName().split("_")[0]
            self.satSenStr = satelliteInfo + "_" + sensorInfo
            outputName = 'VGT_NDVI_RCUR_{0}_{1}_{2}.tif'.format(self.issue, self.cycle, self.satSenStr)

            if not os.path.exists(self.curProdDir):
                BaseUtil.mkDir(self.curProdDir)
            self.outputFile = os.path.join(self.curProdDir, outputName)

            # 判断文件是否存在
            if not os.path.exists(inputFile):
                self.logObj.error('--输入文件{0}不存在'.format(inputFile))
                return

            # 转投影为WGS84
            projected_name = os.path.basename(inputFile)[:-4] + '_WGS84.tif'
            projected_path = os.path.join(self.tempDir, projected_name)
            prj = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
            GdalUtil.rasterProjection(inputFile, projected_path, prj)
            projected_path = projected_path.replace('\\', '/')

            # # 裁剪shp
            # Rrs_clip_name = 'VGT_NDVI_{0}_{1}_{2}_clip.tif'.format(self.issue, self.cycle,
            #                                                  self.satSenStr)
            # Rrs_clip_name = os.path.join(self.tempDir, Rrs_clip_name)
            #
            #
            # buffer_shp = os.path.join(self.dependDir, "shp", "NDVI",  "AreaProvince.shp")
            # buffer_shp = buffer_shp.replace('\\', '/')  # 反斜杠替换
            # GdalUtil.rasterClipByShp(projected_path, Rrs_clip_name, buffer_shp, bgValue=-9999)  # 注意此时背景值改为了-9999


            red_band_raw, width, height, proj, Geotrans = GeoTiffFile.read_tif(projected_path, 3)
            red_band = red_band_raw * 1000
            nir_band = GeoTiffFile.read_tif(projected_path, 4)[0] * 1000

            # cloudData = CloudDection.remove_clouds(projected_path)

            # (2)计算植被指数
            NDVI = self.calculate_NDVI(red_band, nir_band)

            # 获取有效值范围
            value_min, value_max = self.pluginParam.getStatisticInfo()['ValueRange']
            NDVI = np.where((NDVI >= value_min) & (NDVI <= value_max), NDVI, -9999)

            # 保存NDVI
            GeoTiffFile.write_tif(NDVI, 1, width, height, proj, Geotrans, self.outputFile)
            self.rsOutMap["OUTFILEPATH"] = self.outputFile

        except:

            return None


    # # ##云检测
    # @staticmethod
    # def clouddection(red_band, nir_band):
    #     clouddata = np.zeros_like(red_band)
    #     clouddata[np.logical_or(red_band > 1200, T12 > 2800)] = 1
    #     return clouddata


    ##calculate NDVI
    @staticmethod
    def calculate_NDVI(red_band, nir_band):
        """
        计算NDVI
        :param red_band: 红光反射率
        :param nir_band: 近红外反射率
        :parameter cloudData: 云检测的结果
        :return: NDVI
        """
        NDVI = (nir_band - red_band) / (nir_band + red_band)
        NDVI[red_band == 0] = -9999

        # NDVI阈值在-1 - 1之间 无效值剔除
        NDVI[np.where((NDVI < -1) | (NDVI > 1))] = -9999
        nan_index = np.isnan(NDVI)
        NDVI[nan_index] = -9999
        NDVI = NDVI.astype(np.float32)

        # # 云检测
        # NDVI[clouddata == 1] = -9999

        return NDVI

    def doOthers(self):
        """出功能区图"""
        self.tifPath_alber = self.tifProjChange(self.rsOutMap["OUTFILEPATH"])

        # 生态功能区出专题图
        areaList = self.curAreaInfo.searchArea([11, 21])
        areaList.remove('QHS')
        flagProcess = self.ecoExportPic(self.tifPath_alber, 'Province.mxd', areaList)

        return flagProcess

    def mappingReplaceText(self):
        """出图模块 替换文本信息"""
        issue = self.pluginParam.getIssue()
        ele_dict =  {"title":{"yyyy": issue[0:4], "MM": issue[4:6], "dd": issue[6:8]},
            "date": {"yyyy": issue[0:4], "MM": issue[4:6], "dd": issue[6:8]}}
        return ele_dict

    def mappingReplaceLyr(self, tifPath):
        """出图模块 替换mxd图层lyr"""
        ComShpDir = os.path.join(self.pluginParam.getDependDir(), 'shp', 'CompShpAlbers')
        DRY_HSDir = os.path.join(self.pluginParam.getDependDir(), 'shp', 'landuse')

        Glacier = os.path.join(self.pluginParam.getDependDir(), 'shp', 'glacier', "Glacier_QH.shp")
        Water = os.path.join(DRY_HSDir, "LakesXXXX_P00000_XXXXX_AEA_20100000.shp")
        AreaCity = os.path.join(ComShpDir, "AreaCity.shp")
        AreaCounty = os.path.join(ComShpDir, "AreaCounty.shp")
        AreaXiang = os.path.join(ComShpDir, "AreaXiang.shp")
        AreaProvince= os.path.join(ComShpDir, "AreaProvince.shp")
        lyr_dict = {"tifFile": tifPath,
                    "water": Water,
                    "city": AreaCity,
                    "county": AreaCounty,
                    "xiang": AreaXiang,
                    "province": AreaProvince,
                    "Glacier": Glacier
        }
        return lyr_dict

    def getChildAreaList(self, id):
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

    def add_merge_info(self, table_copy, exc_header):
        """excel合并区域"""
        return [
            {'merge_value': table_copy[0][0], 'merge_range': (0, 1, 0, len(exc_header))},
            {'merge_value': table_copy[1][0], 'merge_range': (1, 2, 0, 2)},
            {'merge_value': table_copy[1][2], 'merge_range': (1, 2, 2, 3)},
        ]


    #特征值
    def pdToExcel(self, mean_sub_df, area_id):
        """
        pd to excel
        :param mean_sub_df:
        :return:
        """
        exc_cols1 = self.proexcelcols[0]

        for item in exc_cols1[2:]:
            mean_sub_df[item] = mean_sub_df[item].map(lambda x: ("%.2f") % x)

        basename = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'XCUR')
        # excelPath = os.path.join(self.curProdDir, '{id}', basename + '_{id}.xls')
        excelPath = os.path.join(self.curProdDir, basename + '.xls')
        excelPath = excelPath.format(id=area_id)
        exc_header1 = self.excel_title[0]

        indexs = mean_sub_df.index.tolist()
        indexs.insert(0, '表头')

        class_table_copy = mean_sub_df[exc_cols1]

        items = class_table_copy.columns.tolist()
        items = pd.Series({items[i]: exc_header1[i] for i in range(len(items))}, name="表头")
        class_table_copy = (class_table_copy.append(items))
        class_table_copy = class_table_copy.reindex(index=indexs)

        class_table_copy = list(map(lambda x: list(x), class_table_copy.values))
        class_table_copy.insert(0, [self.table_title]*len(exc_header1))
        # 写excel
        excel = AddWorkBookUtil()
        merge_info_class = self.add_merge_info(class_table_copy, exc_header1)
        excel.add_sheet(class_table_copy, merge_info=merge_info_class, sheet_name='特征值', width_adaptation=False)

        if os.path.exists(excelPath):
            os.remove(excelPath)
        excel.save_to_book(excelPath)

        return excelPath


    def exportExcel(self, areaList):
        """生成表格"""
        con_df = self.getStaInfoToExcel()
        for area_id in areaList[0:1]:
            need_list = [area_id]  # 当前行政区
            need_list.extend(self.getChildAreaList(area_id))  # 所有下级行政区
            mean_sub_df = con_df.loc[need_list]
            try:
                excelPath = self.pdToExcel(mean_sub_df, area_id)

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

    def getStaInfoToExcel(self):
        """
              获取统计信息并进行规整
              :return:
        """
        name = [self.curAreaInfo.getAreaByID(i).getAreaName() for i in self.staCharact.index]
        removeQHS_list = self.staCharact.index.to_list()
        removeQHS_list.remove("QHS")

        id_list = [i if i[:1] == "R" or i[:1] == "O" else i[:1] + "00000" for i in removeQHS_list]
        cname = [self.curAreaInfo.getAreaByID(i).getAreaName() for i in id_list]
        cname.insert(0, "青海省")
        self.staCharact['name'] = name
        self.staCharact['cname'] = cname
        sta_df = self.staCharact[:]

        # 去除 QHS
        need_index = [i for i in sta_df.index if i != 'QHS']
        mean_df_re = sta_df.loc[need_index]
        mean_df_re = mean_df_re.sort_index()
        # 第一行插入QHS信息
        qhs_df = sta_df.loc['QHS'].to_frame().T
        con_df = pd.concat([qhs_df, mean_df_re], axis=0)
        con_df.loc[con_df["cname"] == con_df["name"], "cname"] = "合计"

        return con_df



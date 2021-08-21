# !/usr/bin/python3.7
# -- coding: utf-8 --
#@Time : 2021/8/20-14:45
#@Author : xuhuan
#@File : NDVI_H8.py
#@Software : PyCharm

import os
import copy
import numpy as np
import pandas as pd

from src.common.process.ProcessBase import BaseProcess
from src.common.utils.GdalUtils.GeoTiffFile import GdalBase
from src.common.utils.BaseUtils.BaseUtil import BaseUtil
from src.common.Function.ExcelUtilNew import AddWorkBookUtil
from src.common.Function.WordUtil import WordUtil

class NDVI_H8(BaseProcess):
    """
    NDVI产品
    input：H8的预处理结果
    output: tif,jpg,xls,docx
    """
    def __init__(self, pluginParam):
        BaseProcess.__init__(self, pluginParam)
        self.processType = 3
        self.processOther = False
        self.staInitInfo = {}  # 统计初始化信息
        self.depend_dir = self.pluginParam.getDependDir()
        self.specel_depend_dir = os.path.join(self.depend_dir,"aux_data/Stock_Capacity")
        self.base_name = r"VGT_NDVI_{0}CUR_{1}_COOD_H8_AHI"
        self.issue = self.pluginParam.getIssue()
        self.excel_title = [["地区","", "SUM","MIN", "MAX", "MEAN"]]
        self.excel_title1 = [['面积(km2)', "","<0",'0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1']]
        self.excel_title2 = [['面积比例(%)', "","<0",'0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1']]
        self.table_title = "{0}年NDVI".format(self.issue[:4])
        self.table_title1 = "{0}年NDVI面积".format(self.issue[:4])
        self.table_title2 = "{0}年NDVI面积比例".format(self.issue[:4])

        self.proexcelcols = [["name", "cname", "SUM", "MIN", "MAX", "MEAN"]]
        self.proexcelcols1 = [["name", "cname", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]]
        self.prowordcols = [["name", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]]

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

        # <出图>
        pic_dic = self.ExportPic_init(tifPath_alber)
        flagProcess = self.areaExportPic(tifPath_alber, pic_dic, areaList)
        if not flagProcess:
            self.logObj.error("--出图模块执行失败.")
            return flagProcess
        self.logObj.info("--出图模块执行成功.")

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
        """
        NDVI计算模型
        :return: .tif
        """
        input_file = self.pluginParam.getInputFile()    # 输入H8的预处理结果

        # 判断输入数据是否存在
        if not os.path.exists(input_file) :
            self.logObj.error("输入数据缺失: not exists input data {0}".format(input_file))
            return False

        data, im_width, im_height, im_bands, im_geotrans, im_proj = GdalBase.read_tiff(input_file)
        band_nir = data[3]
        band_red = data[2]
        band_five = data[4]
        band_three =data[2]
        # 判断云像元
        cloud = np.zeros(band_five.shape)
        cloud[np.logical_or(band_three > 1200, band_five > 2800)] = -9999
        # 计算NDVI
        ndvi = (band_nir - band_red) / (band_nir + band_red)
        # 云像元赋值为-9999
        ndvi[cloud == -9999] = -9999

        NDVI_path = os.path.join(self.tempDir, self.base_name.format("R", self.issue) + ".tif")

        GdalBase.write_tiff(ndvi, im_width, im_height, 1, im_geotrans, im_proj, NDVI_path)
        self.rsOutMap["OUTFILEPATH"] = NDVI_path

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
                    "Glacier":Glacier
        }
        return lyr_dict

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

    def add_merge_info(self, table_copy, exc_header):
        """excel合并区域"""
        return [
            {'merge_value': table_copy[0][0], 'merge_range': (0, 1, 0, len(exc_header))},
            {'merge_value': table_copy[1][0], 'merge_range': (1, 2, 0, 2)},
        ]

    def pdToExcel(self, mean_sub_df,mean_sub_are,mean_sub_per,area_id):
        """
        pd to excel
        :param mean_sub_df:
        :return:
        """
        exc_cols1 = self.proexcelcols[0]
        exc_cols2 = self.proexcelcols1[0]

        for item in exc_cols1[2:]:
            mean_sub_df[item] = mean_sub_df[item].map(lambda x: ("%.2f") % x)
        for item in exc_cols2[2:]:
            mean_sub_are[item] = mean_sub_are[item].map(lambda x: ("%.2f") % x)
            mean_sub_per[item] = mean_sub_per[item].map(lambda x: ("%.2f") % x)

        basename = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'XCUR')
        excelPath = os.path.join(self.curProdDir, '{id}', basename + '_{id}.xls')
        excelPath = excelPath.format(id=area_id)
        exc_header1 = self.excel_title[0]
        exc_header2 = self.excel_title1[0]
        exc_header3 = self.excel_title2[0]

        indexs = mean_sub_df.index.tolist()
        indexs.insert(0, '表头')

        class_table_copy = mean_sub_df[exc_cols1]
        area_table_copy = mean_sub_are[exc_cols2]
        per_table_copy = mean_sub_per[exc_cols2]
        # 特征值
        items = class_table_copy.columns.tolist()
        items = pd.Series({items[i]: exc_header1[i] for i in range(len(items))}, name="表头")
        class_table_copy = (class_table_copy.append(items))
        class_table_copy = class_table_copy.reindex(index=indexs)

        class_table_copy = list(map(lambda x: list(x), class_table_copy.values))
        class_table_copy.insert(0, [self.table_title]*len(exc_header1))
        # 面积
        items = area_table_copy.columns.tolist()
        items = pd.Series({items[i]: exc_header2[i] for i in range(len(items))}, name="表头")
        area_table_copy = (area_table_copy.append(items))
        area_table_copy = area_table_copy.reindex(index=indexs)

        area_table_copy = list(map(lambda x: list(x), area_table_copy.values))
        area_table_copy.insert(0, [self.table_title1] * len(exc_header2))
        # 比例
        items = per_table_copy.columns.tolist()
        items = pd.Series({items[i]: exc_header3[i] for i in range(len(items))}, name="表头")
        per_table_copy = (per_table_copy.append(items))
        per_table_copy = per_table_copy.reindex(index=indexs)

        per_table_copy = list(map(lambda x: list(x), per_table_copy.values))
        per_table_copy.insert(0, [self.table_title2] * len(exc_header3))

        # 写excel
        excel = AddWorkBookUtil()
        merge_info_class = self.add_merge_info(class_table_copy,exc_header1)
        excel.add_sheet(class_table_copy,merge_info=merge_info_class, sheet_name='特征值', width_adaptation=False)

        merge_info_class1 = self.add_merge_info(area_table_copy, exc_header2)
        excel.add_sheet(area_table_copy, merge_info=merge_info_class1, sheet_name='面积', width_adaptation=False)

        merge_info_class2 = self.add_merge_info(per_table_copy, exc_header3)
        excel.add_sheet(per_table_copy, merge_info=merge_info_class2, sheet_name='比例', width_adaptation=False)

        if os.path.exists(excelPath):
            os.remove(excelPath)
        excel.save_to_book(excelPath)

        return excelPath

    def exportExcel(self, areaList):
        """生成表格"""
        con_df, con_are, con_per = self.getStaInfoToExcel()
        for area_id in areaList:
            need_list = [area_id]  # 当前行政区
            need_list.extend(self.getChildAreaList(area_id)[0:53])  # 所有下级行政区
            mean_sub_df = con_df.loc[need_list]
            mean_sub_are = con_are.loc[need_list]
            mean_sub_per = con_per.loc[need_list]
            try:
                excelPath = self.pdToExcel(mean_sub_df, mean_sub_are, mean_sub_per,area_id)
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

        self.staReClass['name'] = name
        self.staReClass['cname'] = cname
        cla_df = self.staReClass[:]

        self.staReClPer['name'] = name
        self.staReClPer['cname'] = cname
        pre_df = self.staReClPer[:]

        # 去除 QHS
        need_index = [i for i in sta_df.index if i != 'QHS']
        mean_df_re = sta_df.loc[need_index]
        mean_df_re = mean_df_re.sort_index()

        cla_df_re = cla_df.loc[need_index]
        cla1_df_re = cla_df_re.sort_index()

        pre_df_re = pre_df.loc[need_index]
        pre1_df_re = pre_df_re.sort_index()

        # 第一行插入QHS信息
        qhs_df = sta_df.loc['QHS'].to_frame().T
        con_df = pd.concat([qhs_df, mean_df_re], axis=0)

        qhs_df1 = cla_df.loc['QHS'].to_frame().T
        con_are = pd.concat([qhs_df1, cla1_df_re], axis=0)

        qhs_df2 = pre_df.loc['QHS'].to_frame().T
        con_per = pd.concat([qhs_df2, pre1_df_re], axis=0)

        con_df.loc[con_df["cname"] == con_df["name"], "cname"] = "合计"

        return con_df, con_are, con_per

    def getReplaceWords(self,each,mean_sub_df,area_copy_are,area_copy_pre,sonlevel):
        """文档所需替换字段计算"""
        makeTime = self.issue[:4] + "年" + self.issue[4:6] + "月" + self.issue[6:8] + "日"
        version = "1"  # 版本号，一期未见有相关代码
        regionName = self.curAreaInfo.getAreaByID(each).getAreaName()  # 当前区域名称

        RegionAreaTotal = 0
        preQuyuName = 0
        for i in range(5):
            RegionAreaTotal = RegionAreaTotal + np.float(area_copy_are[['7', '8', '9', '10', '11']].loc[each][i])
            preQuyuName = preQuyuName + np.float(area_copy_pre[['7', '8', '9', '10', '11']].loc[each][i])

        sonLevelIDList = self.curAreaInfo.getAreaByID(each).searchArea([sonlevel]) # 子级行政区域信息
        sonLevelIDList.remove(each) # 移除当前区域

        nextAreaName = []
        for id in sonLevelIDList:
            nextAreaName.append(self.curAreaInfo.getAreaByID(id).getAreaName())

        nextArea = []
        nextPre = []
        for id in sonLevelIDList:
            Area = 0
            pre = 0
            for i in range(5):
                Area = Area + float(area_copy_are[['7', '8', '9', '10', '11']].loc[id][i])
                pre = pre + float(area_copy_pre[['7', '8', '9', '10', '11']].loc[id][i])
            nextArea.append(str(np.round(Area,2)))
            nextPre.append(str(np.round(pre, 2)) + '%')

        AreaName = []
        for i in range(3):  # 前三
            AreaName.append(self.curAreaInfo.getAreaByID(mean_sub_df[['SUM', 'name']].loc[sonLevelIDList]['SUM'].sort_values(ascending=False).index[i]).getAreaName())

        level = ['0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5', '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']

        cols = self.prowordcols[0][1:]
        mainlevel_start = (int(area_copy_are[cols].head(1).max().idxmax()) - 2) / 10
        mainlevel = str(mainlevel_start) + '-' + str(mainlevel_start + 0.1)

        levelarea = []
        levelpre = []
        for id in sonLevelIDList:
            levelarea_son = []
            levelpre_son = []
            for i in range(10):
                levelarea_son.append(area_copy_are[cols].loc[id][i] + '平方公里')
                levelpre_son.append(area_copy_pre[cols].loc[id][i] + '%')
            levelarea_son = self.curAreaInfo.getAreaByID(id).getAreaName() + '、'.join(levelarea_son)
            levelpre_son = self.curAreaInfo.getAreaByID(id).getAreaName() + '、'.join(levelpre_son)
            levelarea.append(levelarea_son)
            levelpre.append(levelpre_son)

        result_dict = {
            'year': self.issue[:4],
            'month': self.issue[4:6],
            'version': version,
            'makeTime': makeTime,
            'quyuName': regionName,
            'quyuTotal': RegionAreaTotal,
            'preQuyuName': str(np.round(preQuyuName,2)) + '%',
            'AreaName': addHE(AreaName),
            'nextAreaName': addHE(nextAreaName),
            'nextArea': addHE(nextArea),
            'nextPre': addHE(nextPre),
            'mainlevel': mainlevel,
            'level': addHE(level),
            'levelarea': addHE(levelarea),
            'levelpre': addHE(levelpre),
        }
        return result_dict

    def pdToWord(self,each,mean_sub_df,mean_sub_are,mean_sub_per,DocTemplate,save_path,sonlevel,lines_loc):
        """生成word"""
        exc_cols = self.prowordcols[0]
        # 格式化表格数据
        for item in exc_cols[1:]:
            mean_sub_are[item] = mean_sub_are[item].map(lambda x: ("%.2f") % x)
            mean_sub_per[item] = mean_sub_per[item].map(lambda x: ("%.2f") % x)

        class_table_are = mean_sub_are[exc_cols]
        class_table_per = mean_sub_per[exc_cols]

        replace_dict = {'pics': {}, 'words': {}, 'tables': {}}
        area_copy_are = copy.deepcopy(class_table_are)
        area_copy_pre = copy.deepcopy(class_table_per)

        # 获取替换图片路径
        temp_path = os.path.join(self.pluginParam.getDependDir(), "word\{0}\pic\image001.jpg".format(self.name))
        basename = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'ZCUR')
        pic_path = os.path.join(self.curProdDir, each, basename + '_{0}.jpg'.format(each))
        replace_dict['pics'] = {temp_path: pic_path}
        replace_dict['words'] = self.getReplaceWords(each,mean_sub_df,area_copy_are,area_copy_pre,sonlevel)

        area_copy_are['0-0.2'] = np.sum([[float(x) for x in area_copy_are['2'].to_list()], [float(x) for x in area_copy_are['3'].to_list()]], axis=0).tolist()
        area_copy_are['0.2-0.4'] = np.sum([[float(x) for x in area_copy_are['4'].to_list()], [float(x) for x in area_copy_are['5'].to_list()]], axis=0).tolist()
        area_copy_are['0.4-0.6'] = np.sum([[float(x) for x in area_copy_are['6'].to_list()], [float(x) for x in area_copy_are['7'].to_list()]], axis=0).tolist()
        area_copy_are['0.6-0.8'] = np.sum([[float(x) for x in area_copy_are['8'].to_list()], [float(x) for x in area_copy_are['9'].to_list()]], axis=0).tolist()
        area_copy_are['0.8-1'] = np.sum([[float(x) for x in area_copy_are['10'].to_list()], [float(x) for x in area_copy_are['11'].to_list()]], axis=0).tolist()

        area_copy_pre['0-0.2'] = np.sum([[float(x) for x in area_copy_pre['2'].to_list()], [float(x) for x in area_copy_pre['3'].to_list()]], axis=0).tolist()
        area_copy_pre['0.2-0.4'] = np.sum([[float(x) for x in area_copy_pre['4'].to_list()], [float(x) for x in area_copy_pre['5'].to_list()]], axis=0).tolist()
        area_copy_pre['0.4-0.6'] = np.sum([[float(x) for x in area_copy_pre['6'].to_list()], [float(x) for x in area_copy_pre['7'].to_list()]], axis=0).tolist()
        area_copy_pre['0.6-0.8'] = np.sum([[float(x) for x in area_copy_pre['8'].to_list()], [float(x) for x in area_copy_pre['9'].to_list()]], axis=0).tolist()
        area_copy_pre['0.8-1'] = np.sum([[float(x) for x in area_copy_pre['10'].to_list()], [float(x) for x in area_copy_pre['11'].to_list()]], axis=0).tolist()

        newlevel = ['name', '0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1']
        for item in newlevel[1:]:
            area_copy_are[item] = area_copy_are[item].map(lambda x: ("%.2f") % x)
            area_copy_pre[item] = area_copy_pre[item].map(lambda x: ("%.2f") % x)

        area_copy_are_tail = area_copy_are[newlevel].tail(-1)
        area_copy_are_head = area_copy_are[newlevel].head(1)
        area_list1 = np.array(pd.concat([area_copy_are_tail, area_copy_are_head], axis=0)).tolist()

        area_copy_pre_tail = area_copy_pre[newlevel].tail(-1)
        area_copy_pre_head = area_copy_pre[newlevel].head(1)
        area_list2 = np.array(pd.concat([area_copy_pre_tail, area_copy_pre_head], axis=0)).tolist()

        replace_dict['tables'] = [{'mode': 'add_row', 'num': 0, 'value': area_list1},
                                  {'mode': 'add_row', 'num': 1, 'value': area_list2}]

        a = WordUtil(DocTemplate, replace_dict, save_path)
        a.do_process(lines_loc)

    def getStaInfoToWord(self):
        """
        获取统计信息并进行规整
        :return:
        """
        name = [self.curAreaInfo.getAreaByID(i).getAreaName() for i in self.staCharact.index]
        self.staCharact['name'] = name
        self.staReClass['name'] = name
        self.staReClPer['name'] = name
        sta_df = self.staCharact[:]
        sta_are = self.staReClass[:]
        sta_per = self.staReClPer[:]

        need_index = [i for i in sta_df.index if i != 'QHS']
        mean_df_re = sta_df.loc[need_index]
        mean_df_re = mean_df_re.sort_index()
        qhs_df = sta_df.loc['QHS'].to_frame().T
        con_df = pd.concat([mean_df_re, qhs_df], axis=0)

        mean_are_re = sta_are.loc[need_index]
        mean_are_re = mean_are_re.sort_index()
        qhs_are = sta_are.loc['QHS'].to_frame().T
        con_are = pd.concat([mean_are_re, qhs_are], axis=0)

        mean_per_re = sta_per.loc[need_index]
        mean_per_re = mean_per_re.sort_index()
        qhs_per = sta_per.loc['QHS'].to_frame().T
        con_per = pd.concat([mean_per_re, qhs_per], axis=0)

        return con_df, con_are, con_per

    def exportWord(self,areaList):
        """生成文档"""
        docDir = os.path.join(self.pluginParam.getDependDir(), 'word/NDVI_H8/')
        DocTemplate = os.path.join(docDir, self.name + '.docx')
        con_df, con_are, con_per = self.getStaInfoToWord()
        for each in areaList:
            # 当前行政区
            need_list = [each]
            need_list.extend(self.getChildAreaList(each)[0:53])
            mean_sub_df = con_df.loc[need_list]  # 过滤非当前行政区划信息
            mean_sub_are = con_are.loc[need_list]  # 过滤非当前行政区划信息
            mean_sub_per = con_per.loc[need_list]  # 过滤非当前行政区划信息
            print("准备制作{}报告：".format(each))
            level = self.curAreaInfo.getAreaByID(each).getLevel()
            if level == 00:  # 省级
                sonlevel = 10
                docName = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'WCUR') + "_" + each +".docx"
                save_path = os.path.join(self.curProdDir, each, docName)
                lines_loc = [(1, 0),  (9, 0), (16, 0), (21, 0), (26, 0), (32, 0), (39, 0), (46, 0), (54, 0)]  # word中表格的加粗位置
            elif level == 10:  # 市级
                sonlevel = 20
                docName = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'WCUR') + "_" + each + ".docx"
                save_path = os.path.join(self.curProdDir, each, docName)
                lines_loc = [(1, 0)]
            elif level == 20:  # 县级
                sonlevel = 30
                docName = BaseUtil.filePathInfo(self.rsOutMap["OUTFILEPATH"])[1].replace('RCUR', 'WCUR') + "_" + each + ".docx"
                save_path = os.path.join(self.curProdDir, each, docName)
                lines_loc = [(1, 0)]
            elif level == 11:  # 生态功能区
                continue
            elif level == 21:  # 生态功能子区
                continue

            try:
                self.pdToWord(each,mean_sub_df,mean_sub_are,mean_sub_per,DocTemplate,save_path,sonlevel,lines_loc)
            except:
                print("Fail to {0} Word".format(each))
                self.logObj.error("Fail to {0} Word".format(each))
            if each in self.outFileMap:
                self.outFileMap[each].append({"type": ".docx", "file": save_path})
            else:
                self.outFileMap[each] = []
                self.outFileMap[each].append({"type": ".docx", "file": save_path})
        return True

def addHE(diclist):
    if len(diclist) > 1:
        str = '、'.join(diclist[:-1]) + '和' + diclist[-1]
    else:
        str = diclist[0]

    return str



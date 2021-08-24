import os
import numpy as np
from osgeo import gdal
import glob
import time

class NDVI(BaseProcess):
    """
    NDVI指数
    input: .tif
    output: tif,jpg,xls,docx
    """

    def __init__(self, pluginParam):
        BaseProcess.__init__(self, pluginParam)
        self.processType = 3
        self.processOther = False
        self.staInitInfo = {}  # 统计初始化信息
        self.depend_dir = self.pluginParam.getDependDir()
        self.issue = self.pluginParam.getIssue()
        self.prowordcols = [["name", "cname", "sum"]]

    def doAnalysis(self):

        tifPath = self.rsOutMap["OUTFILEPATH"]
        self.logObj.info("--开始分析算法文件:{0}".format(tifPath))


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

        # # <出图>
        # pic_dic = self.ExportPic_init(tifPath_alber)
        # flagProcess = self.areaExportPic(tifPath_alber, pic_dic, areaList)
        # if not flagProcess:
        #     self.logObj.error("--出图模块执行失败.")
        #     return flagProcess
        # self.logObj.info("--出图模块执行成功.")
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


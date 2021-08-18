import os
import sys
import pandas as pd
import numpy as np
import h5py
import datatime

from src.common.utils.GdalUtils.GeoTiffFile import GdalBase, GdalTools
from src.common.process.ProcessBase import BaseProcess
from src.common.utils.GdalUtils.GdalUtil import GdalUtil
from src.common.Function.WordUtil import WordUtil
from src.common.Function.ExcelUtilNew import AddWorkBookUtil
from src.common.utils.BaseUtils.BaseUtil import BaseUtil
from src.common.utils.SysUtil import SysUtil
from src.common.utils.GdalUtils.ShapeFile import ShapeFile
from src.common.Function.ZonalStatistics import ZonalStatistics

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

        #  <裁切>
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

         # <其他需求>
         flagProcess = self.doOthers()
         if not flagProcess:
             self.logObj.error("--出生态功能区图模块执行失败.")
             return flagProcess
         self.logObj.info("--出生态功能区图模块执行成功.")

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
        NDVI模型
        ：return:.tif
        """
        try:
            inputFile = self.pluginParam.getInputFile()
        #读取文件信息
            self.cycle = self.pluginParam.getInputInfoByKey("cycle")
            self.issue = self.pluginParam.getInputInfoByKey("issue")
            self.logPath = self.pluginParam.getInputInfoByKey("outLogPath")
            self.SatName = self.pluginParam.getPluginName().split("_")[1]
            outputName = 'VGT_NDVI_RCUR_{0}_{1}_{2}.tif'.format(self.issue, self.cycle, self.SatName)
            self.outputFile = os.path.join(self.curProdDir, outputName)

        #波段信息
            blue_band_raw, width, height, proj, Geotrans = GeoTiffFile.read_tif(inputFile, 0)
            blue_band = blue_band_raw
            green_band = GeoTiffFile.read_tif(inputFile, 1)[0]
            red_band = GeoTiffFile.read_tif(inputFile, 2)[0]
            nir_band = GeoTiffFile.read_tif(inputFile, 3)[0]

        #植被指数NDVI
            NDVI = self.calculate_NDVI(red_band, nir_band)

        #裁剪
            CLIP = 'CLIP_{0}_{1}_{2}.tif'.format(self.issue, self.cycle, self.SatName)
            CLIP_PATH = os.path.join(self.tempDir, CLIP)
            CLIP_PATH = CLIP_PATH.replace('\\', '/')
            GeoTiffFile.write_tif(NDVI, 1, width, height, proj, Geotrans, CLIP_PATH)
            GdalUtil.rasterClipByShp(CLIP_PATH, self.outputFile, shpPath, bgValue=-9999)
            self.rsOutMap["OUTFILEPATH"] = self.outputFile

         except:
            return None

        ##############后面生成的东西实在不会了，等讲解
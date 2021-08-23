# -- coding: utf-8 --

from ...common.process.PluginFactory import PluginFactory
from .Stock_Capacity import Stock_Capacity


class PluginFactoryIns(PluginFactory):

    """具体项目产品算法插件工厂"""

    def __init__(self): 
        PluginFactory.__init__(self)
        self.name = "PluginFactoryIns"

    def getPlugin(self, pluginInfo):
        """获取算法对象"""

        try:     
            if pluginInfo is None:
                return
            
            pluginObj = None
            pluginName = pluginInfo.getPluginName().upper()

            if pluginName == "STOCK_CAPACITY":
                pluginObj = Stock_Capacity(pluginInfo)
            if pluginName == "NDVI":
                pluginObj = NDVI(pluginInfo)
            return pluginObj
        except Exception as e:
            print(e)
            return None
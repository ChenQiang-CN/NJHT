#time 2021/7/26
#by zhangtao

import sys
import os
import importlib
import warnings
warnings.filterwarnings("ignore")



def read_package():
    """
    通过当前环境安装包的路径遍历全部文件并尝试导入，不出错的输出即为已经安装的包
    """
    for i in sys.path:
        if 'site-packages' in i:
            package_path = i
    list_name = os.listdir(package_path)

    name = []
    v = []
    for i in list_name:
        try:
            package = importlib.import_module(i)

            v.append(package.__version__)
            name.append(package.__name__)
        except:
            pass
        continue
    print('安装的包有{}\n版本分别为{}'.format(name,v))
    return 1

def read_tif(path):
    """
    使用gdal库来读取指定路径下的tif栅格文件
    """
    ds = gdal.Open(path)
    im_width = ds.RasterXSize
    im_height = ds.RasterYSize
    im_data = ds.ReadAsArray(0,0,im_width,im_height)
    im_gt = ds.GetGeoTransform()
    im_proj = ds.GetProjection()
    print('该栅格的行列大小为{},{}\n投影信息为{}'.format(im_width,im_height,im_proj))
    return 1

if __name__ == '__main__':
    print('----------Question_1--------- ')
    read_package()
    import gdal
    path = "C:/Users/EDZ/Documents/WeChat Files/wxid_qoicsv9i7hm822/FileStorage/File/2021-07/tif/true_color_3857.tif"
    print('----------Question_2----------')
    read_tif(path)



#test
#import importlib
#a = 'numpy'
#package = importlib.import_module(a)
#package.__version__
#package.__name__


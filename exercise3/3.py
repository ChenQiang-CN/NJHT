import h5py
import gdal
import os
import ogr
import numpy as np
import osr


def read_tiff(r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif"):
    """
    读取 TIFF 文件
    :param path: str，unicode，dataset
    :return:
    """
    # 参数类型检查
    if isinstance(r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif", gdal.Dataset):
        dataset = path
    else:
        dataset = gdal.Open(r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif")

    if dataset:
        im_width = dataset.RasterXSize  # 栅格矩阵的列数
        im_height = dataset.RasterYSize  # 栅格矩阵的行数
        im_bands = dataset.RasterCount  # 波段数
        im_proj = dataset.GetProjection()  # 获取投影信息
        im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
        im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
        return im_data, im_width, im_height, im_bands, im_geotrans, im_proj
    else:
        print('fail')

def write_tiff(im_data, im_width, im_height, im_bands, im_geotrans, im_proj, out_path=None,
               no_data_value=None, return_mode='TIFF'):
    """
    写dataset（需要一个更好的名字）
    :param im_data: 输入的矩阵
    :param im_width: 宽
    :param im_height: 高
    :param im_bands: 波段数
    :param im_geotrans: 仿射矩阵
    :param im_proj: 坐标系
    :param out_path: 输出路径，str，None
    :param no_data_value: 无效值 ；num_list ，num
    :param return_mode: TIFF : 保存为本地文件， MEMORY：保存为缓存
    :return: 当保存为缓存的时候，输出为 dataset
    """
    # 保存类型选择
    if 'int8' in im_data.dtype.name or 'bool' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32
    # 矩阵波段识别
    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        # 统一处理为三维矩阵
        im_data = np.array([im_data], dtype=im_data.dtype)
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
    # 根据存储类型的不同，获取不同的驱动
    if out_path:
        dataset = gdal.GetDriverByName('GTiff').Create(out_path, im_width, im_height, im_bands, datatype)
    else:
        dataset = gdal.GetDriverByName('MEM').Create('', im_width, im_height, im_bands, datatype)
    # 写入数据
    if dataset is not None:
        dataset.SetGeoTransform(im_geotrans)
        dataset.SetProjection(im_proj)
    # 写入矩阵
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
        # 写入无效值
        if no_data_value is not None:
            # 当每个图层有一个无效值的时候
            if isinstance(no_data_value, list) or isinstance(no_data_value, tuple):
                if no_data_value[i] is not None:
                    dataset.GetRasterBand(i + 1).SetNoDataValue(no_data_value[i])
            else:
                dataset.GetRasterBand(i + 1).SetNoDataValue(no_data_value)
    # 根据返回类型的不同，返回不同的值
    if return_mode.upper() == 'MEMORY':
        return dataset
    elif return_mode.upper == 'TIFF':
        del dataset
    return True


if __name__ == "__main__":
    # hdf path
    hdf_path = r"C:\Users\EDZ\Desktop\HDF\202106280700.hdf"
    # tif_folder
    tiff_folder = r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif"
    # shp path
    shp_path = r"C:\Users\EDZ\Desktop\htht\code\depend\shp\CompShpAlbers\AreaCity.shp"
    # Process 1:hdf to tiff
    tif_dict = to_tiff_from_hdf(hdf_path, tiff_folder)
    # Process 2:tiff resampling\read tiff
    # B03
    b3_tif = tif_dict['B03.tif']
    b3_tif_res = os.path.join(tiff_folder, 'B03_res.tif')
    resample_tiff(b3_tif, 0.02, b3_tif_res)
    b3_res_data, width, height, bands, geotrans, proj = read_tiff(b3_tif_res)
    # B04
    b4_tif = tif_dict['B04.tif']
    b4_tif_res = os.path.join(tiff_folder, 'B04_res.tif')
    resample_tiff(b4_tif, 0.02, b4_tif_res)
    b4_res_data = read_tiff(b4_tif_res)[0]
    # B05
    b5_tif = tif_dict['B05.tif']
    b5_tif_res = os.path.join(tiff_folder, 'B05_res.tif')
    resample_tiff(b5_tif, 0.02, b5_tif_res)
    b5_res_data = read_tiff(b5_tif_res)[0]
    # Process 3:calculate ndvi, calculate cloud
    ndvi_path = os.path.join(tiff_folder, 'ndvi.tif')
    ndvi_data = cal_ndvi(b4_res_data, b3_res_data, b5_res_data, b3_res_data)
    write_tiff(ndvi_data, width, height, bands, geotrans, proj, out_path=ndvi_path)
    # Process 4:tiff clip
    clip_path = os.path.join(tiff_folder, 'ndvi_clip.tif')
    clip_tiff(ndvi_path, shp_path, out_raster_file=clip_path)
    print('success')

    if __name__ == "__main__":
        #    # =====================================单个区域出图代码示例=================================================== #
        #
        #     # pmd模板路径
        pmd_path = r"C:\Users\EDZ\Desktop\htht\code\depend\pmd\NDVI\NDVI_province.pmd"
        #     # 省界图层
        province_path = r"C:\Users\EDZ\Desktop\htht\code\depend\shp\CompShpAlbers\AreaProvince.shp"
        #     # 产品文件路径
        tif_path = r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif"
        #     # 市界图层
        city_path = r"C:\Users\EDZ\Desktop\htht\code\depend\shp\CompShpAlbers\AreaCity.shp"
        #     # 县界图层
        county_path = r"C:\Users\EDZ\Desktop\htht\code\depend\shp\CompShpAlbers\AreaCounty.shp"
        #     # 背景图层
        background_path = r"C:\Users\EDZ\Desktop\htht\data\VGT_NPP_RCUR_2020010100000000_COAY_CIMISS_QHS.tif"
        #     # 创建mapping对象
        mapping_obj = Mapping(pmd_path)
        #     # 设置临时文件夹路径
        mapping_obj.set_tempdir(temp_dir)
        #
        #     # 创建各图层对象
        tif_layer = Layer("tif", Layer.TIFF_SINGLE_BAND, tif_path, tif_rander)
        province_layer = Layer("province", Layer.SHAPE_POLYGON, province_path, province_rander)
        city_layer = Layer("city", Layer.SHAPE_POLYGON, city_path, city_rander)
        county_layer = Layer("county", Layer.SHAPE_POLYGON, county_path, county_rander)
        background_layer = Layer("rgb", Layer.TIFF_MUL_BAND, background_path, background_rander)
        #
        #     # 添加图层信息
        #     # add_layer会将图层往一个列表中添加，所以要注意添加顺序
        #     # 最先添加的会在最底层，最后添加的会在最上层
        mapping_obj.add_layer(background_layer)
    mapping_obj.add_layer(tif_layer)
    mapping_obj.add_layer(province_layer)
    mapping_obj.add_layer(city_layer)
    mapping_obj.add_layer(county_layer)
    #
    #     # 添加替换文本信息
    replace_text = {"title": {"yyyy": "2020", "MM": "04", "dd": "21", "HH": "18", "mm": "07", "regionName": "青海省"},
                    "date": {"yyyy": "2020", "MM": "04", "dd": "21"},
                    "info": {"SAT": "FY3C", "SEN": "VIRR", "RES": "500"}}
    mapping_obj.set_replace_text(replace_text)
    #
    #     # [可选]设置数据框范围
    #     # 若不设置则以模板设置数据框范围为准
    #     # TODO 这里要先获取到当前的数据框经纬度范围
    mapping_obj.set_extent(89.401, 103.07, 31.6007, 39.2126)
    #
    #     # [可选]设置数据框缩放百分比，数值越大数据框范围越大
    mapping_obj.set_extent_percentage(105)
    #
    #     # 专题图输出路径
    out_pic_path = r"C:\Users\wangbin\Desktop\piemapping\outpic\output_pic1.png"
    mapping_obj.export_pic(out_pic_path, 300)


import rasterio as rio

band = rio.open(path)
from rasterio.warp import (reproject,RESAMPLING, transform_bounds,calculate_default_transform as calcdt)

affine, width, height = calcdt(src.crs, dst_crs, src.width, src.height, *src.bounds)
kwargs = src.meta.copy()
kwargs.update({
    'crs': dst_crs,
    'transform': affine,
    'affine': affine,
    'width': width,
    'height': height,
    'geotransform':(0,1,0,0,0,-1) ,
    'driver': 'GTiff'
})

dst = rio.open(newtiffname, 'w', **kwargs)

for i in range(1, src.count + 1):
    reproject(
        source = rio.band(src, i),
        destination = rio.band(dst, i),
        src_transform = src.affine,
        src_crs = src.crs,
        dst_transform = affine,
        dst_crs = dst_crs,
        dst_nodata = src.nodata,
        resampling = RESAMPLING.bilinear)
    from geopandas import GeoSeries

    features = [shpdata.geometry.__geo_interface__]
    from geopandas import GeoSeries

    features = [GeoSeries(shpdata.geometry[i]).__geo_interface__]
    import rasterio.mask

    out_image, out_transform = rio.mask.mask(src, features, crop=True, nodata=src.nodata)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    band_mask = rasterio.open(newtiffname, "w", **out_meta)
    band_mask.write(out_image)
import os
from osgeo import gdal, ogr, osr
import numpy as np

gdal.UseExceptions()  

def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def erase_raster_with_shapefile(raster_path, shapefile_path, output_path):
    try:
        print(f"Processing raster: {raster_path}")

        raster_ds = gdal.Open(raster_path, gdal.GA_Update)
        if raster_ds is None:
            raise Exception(f"无法打开栅格文件: {raster_path}")


        raster_proj = raster_ds.GetProjection()
        raster_geotrans = raster_ds.GetGeoTransform()
        x_min = raster_geotrans[0]
        y_max = raster_geotrans[3]
        x_res = raster_ds.RasterXSize
        y_res = raster_ds.RasterYSize
        x_max = x_min + x_res * raster_geotrans[1]
        y_min = y_max + y_res * raster_geotrans[5]

        
        shapefile_ds = ogr.Open(shapefile_path)
        if shapefile_ds is None:
            raise Exception(f"无法打开矢量文件: {shapefile_path}")
        shapefile_layer = shapefile_ds.GetLayer()

       
        shapefile_proj = shapefile_layer.GetSpatialRef()
        raster_proj_ref = osr.SpatialReference(wkt=raster_proj)
        if not shapefile_proj.IsSame(raster_proj_ref):
            raise Exception("栅格数据和矢量数据的投影不一致")


        mask = np.zeros((y_res, x_res), dtype=np.uint8)


        print("Rasterizing shapefile to create mask...")
        temp_ds = gdal.GetDriverByName('MEM').Create('', x_res, y_res, 1, gdal.GDT_Byte)
        temp_ds.SetProjection(raster_proj)
        temp_ds.SetGeoTransform(raster_geotrans)
        gdal.RasterizeLayer(temp_ds, [1], shapefile_layer, burn_values=[1])
        mask = temp_ds.GetRasterBand(1).ReadAsArray()

        print("Applying mask to raster data...")
        for band_index in range(1, raster_ds.RasterCount + 1):
            band = raster_ds.GetRasterBand(band_index)
            data = band.ReadAsArray()
            data[mask == 1] = band.GetNoDataValue()
            band.WriteArray(data)


        print(f"Saving result to {output_path}")
        gdal.GetDriverByName('GTiff').CreateCopy(output_path, raster_ds)
        raster_ds.FlushCache()


        raster_ds = None
        shapefile_ds = None
        temp_ds = None
        print(f"Processing completed for raster: {raster_path}")

    except Exception as e:
        print(f"Error processing raster {raster_path}: {e}")

if __name__ == "__main__":
    input_folder = r"E:\2024年工作\水质反演-重庆三峡\数据\三峡\res"
    shapefile_path = r"E:\2024年工作\水质反演-重庆三峡\水质反演后裁剪矢量\0721.shp"
    output_folder = r"E:\2024年工作\水质反演-重庆三峡\数据\三峡\res\result_cut"


    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    print("Output folder created successfully.")


    for file_name in os.listdir(input_folder):
        print(file_name)
        if file_name.endswith('.tif'):
            input_raster_path = os.path.join(input_folder, file_name)
            output_raster_path = os.path.join(output_folder, file_name)
            erase_raster_with_shapefile(input_raster_path, shapefile_path, output_raster_path)
            print(f"Processed: {file_name}")

    print("All files processed successfully.")

import geopandas

from app.image_code.utils.Vectorizator import Vectorizator
from app.image_code.BinaryGeoTiffImage import BinaryGeoTiffImage

img = BinaryGeoTiffImage(file_path="src/base_img_L1_NE_L2_NE_L3_SW.tif",
                         # min_threshold=10,
                         # max_threshold=12,
                         )


vectorizer = Vectorizator(binary_geotiff_image=img)

vectorizer.calculate_with_pixel_count()
gjson = vectorizer.geojson_data

gdf = geopandas.GeoDataFrame.from_features(gjson)
print(gdf)

vectorizer.save_geojson(f"{img.image_name}.geojson")

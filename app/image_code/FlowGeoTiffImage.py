from app.image_code.GeoTiffImage import GeoTiffImage
import numpy as np
import rasterio


class FlowGeoTiffImage(GeoTiffImage):

    def __init__(self, file_path, level=0):
        super(FlowGeoTiffImage, self).__init__(file_path, level)

    def _load_image(self):
        """Загружает данные и метаданные изображения, заменяя отрицательные значения на 0.0"""
        super()._load_image()

        # Заменяем все отрицательные значения на 0.0
        if self.data is not None:
            self.data = np.where(self.data < 0, 0.0, self.data)

            # Обновляем информацию о nodata, если она была отрицательной
            if self.meta.get('nodata') is not None and self.meta['nodata'] < 0:
                self.meta['nodata'] = 0.0

if __name__ == "__main__":
    img = FlowGeoTiffImage(file_path="../../src/base_img_L1_NE_L2_NE_L3_SW.tif")
    img.print_info()
    img.show()
    print(img.data[0])
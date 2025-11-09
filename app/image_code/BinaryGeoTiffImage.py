import os

from app.image_code.utils.ImageBinarizer import ImageBinarizer
from app.image_code.GeoTiffImage import GeoTiffImage


class BinaryGeoTiffImage(GeoTiffImage):

    def __init__(self, file_path, level=0, min_threshold=0, max_threshold=None):
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.bin_stats = None
        super(BinaryGeoTiffImage, self).__init__(file_path, level)


    def _load_image(self):
        """Загружает данные и метаданные изображения, заменяя отрицательные значения на 0.0"""
        super()._load_image()

        binarizer = ImageBinarizer(self)
        if self.min_threshold is None and self.max_threshold is None:
            bin_img = binarizer.binary_default()
        elif self.min_threshold is not None:
            threshold = 1e-9 if self.min_threshold == 0 else self.min_threshold
            bin_img = binarizer.binary_threshold(threshold=threshold)
        elif self.max_threshold is not None:
            bin_img = binarizer.binary_range(min_threshold=self.min_threshold,
                                             max_threshold=self.max_threshold)
        else:
            raise ValueError("min_threshold or max_threshold must be specified")
        self.data = bin_img.data
        self.meta = bin_img.meta
        self.image_name = f"{self.image_name}_BIN_{self.min_threshold}-{self.max_threshold}"
        self.file_path = os.path.join(self.image_dir, f"{self.image_name}.tif")
        self.bin_stats = binarizer.get_statistics()

    @classmethod
    def create_from_geotiff_image(cls, geotiff_image: GeoTiffImage, min_threshold=0, max_threshold=None):
        level = geotiff_image.image_dir
        file_path = geotiff_image.file_path
        return cls(file_path, level=level, min_threshold=min_threshold, max_threshold=max_threshold)

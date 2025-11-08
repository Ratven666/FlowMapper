import os

import rasterio

from app.image_code.ImageSplitter import ImageSplitter
from app.image_code.plotters.MPLImagePlotter import MPLImagePlotter


class GeoTiffImage:
    """
    Класс для работы с GeoTIFF изображениями и управления иерархией разбиения
    """

    def __init__(self, file_path, level=0):
        self.file_path = file_path
        self.image_name = os.path.basename(file_path).split(".")[0]
        self.level = level

        self.data = None
        self.meta = None
        self.crs = None
        self.bounds = None
        self.transform = None
        self.count = None
        self.width = None
        self.height = None
        self._load_image()

    def _load_image(self):
        """Загружает данные и метаданные изображения"""
        with rasterio.open(self.file_path) as src:
            self.data = src.read()
            self.meta = src.meta.copy()
            self.crs = src.crs
            self.bounds = src.bounds
            self.transform = src.transform
            self.count = src.count
            self.width = src.width
            self.height = src.height
        # Если уровень не передан явно, определяем из имени файла
        if self.level == 0:
            self._get_image_level_and_corner()

    def _get_image_level_and_corner(self):
        """
        Определяет уровень и угол для формата: {name}_L{level}_{corner}.tif
        """
        parts = self.image_name.split('_')

        # Минимально должно быть 3 части: name, L{level}, corner
        if len(parts) < 3:
            self.level = 0
            self.corner = None
            return

        # Предпоследняя часть должна быть уровнем (формат L{number})
        level_part = parts[-2] if len(parts) >= 2 else None
        # Последняя часть должна быть углом
        corner_part = parts[-1] if len(parts) >= 1 else None

        # Парсим уровень
        if level_part and level_part.startswith('L') and level_part[1:].isdigit():
            self.level = int(level_part[1:])
        else:
            self.level = 0

        # Парсим угол
        if corner_part and corner_part.upper() in ["NW", "NE", "SW", "SE"]:
            self.corner = corner_part.upper()
        else:
            self.corner = None

    def split_image(self, max_level=1, save_dir=None, splitter=ImageSplitter):
        if save_dir is None:
            save_dir = os.path.dirname(os.path.abspath(self.file_path))
            save_dir = os.path.join(save_dir, self.image_name)
        splitter().recursive_split(geotiff_image=self,
                                 max_level=max_level,
                                 save_dir=save_dir)


    def show(self, plotter=MPLImagePlotter, *args, **kwargs):
        """Отображает изображение с использованием указанного плоттера"""
        plotter = plotter(self, *args, **kwargs)
        plotter.plot()

    def print_info(self, include_children=False):
        """Выводит информацию об изображении"""
        file_size = os.path.getsize(self.file_path) / (1024 * 1024) if os.path.exists(self.file_path) else 0
        print(f"Image Name: {self.image_name}")
        print(f"Image Level: {self.level}")
        print(f"File Size: {file_size:.2f}Mb")
        print(f"CRS: {self.crs}")
        print(f"Bounds: {self.bounds}")
        print(f"Count: {self.count}")
        print(f"Size: {self.width}x{self.height}")

    def __repr__(self):
        return f"GeoTiffImage(level={self.level}, size={self.width}x{self.height}, file='{self.image_name}')"



if __name__ == "__main__":
    img = GeoTiffImage(file_path="../../src/base_img.tif")
    img.print_info()
    img.split_image(max_level=2)

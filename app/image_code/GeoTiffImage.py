from datetime import datetime
import os

import rasterio

from app.image_code.utils.ImageSplitter import ImageSplitter
from app.image_code.plotters.MPLImagePlotter import MPLImagePlotter


class GeoTiffImage:
    """
    Класс для работы с GeoTIFF изображениями и управления иерархией разбиения
    """

    def __init__(self, file_path, level=0):
        self.file_path = file_path
        self.image_dir = os.path.dirname(file_path)
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
        images = splitter().recursive_split(geotiff_image=self,
                                            max_level=max_level,
                                            save_dir=save_dir)
        return images

    def show(self, plotter=MPLImagePlotter, *args, **kwargs):
        """Отображает изображение с использованием указанного плоттера"""
        plotter = plotter(self, *args, **kwargs)
        plotter.plot()

    def _prepare_output_path(self, output_path):
        """
        Подготавливает путь для сохранения файла

        Args:
            output_path (str): Путь для сохранения

        Returns:
            str: Подготовленный путь к файлу
        """
        if output_path is None:
            output_path = os.path.dirname(os.path.abspath(self.file_path))

        # Если путь является директорией, создаем имя файла автоматически
        if os.path.isdir(output_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_path, f"{self.image_name}_{timestamp}.tif")

        # Убеждаемся, что расширение .tif
        if not output_path.lower().endswith(('.tif', '.tiff')):
            output_path += '.tif'

        return output_path

    def save(self, output_path=".", **kwargs):
        """
        Сохраняет изображение в GeoTIFF файл

        Args:
            output_path (str): Путь для сохранения файла. Если None, используется оригинальный путь.
            **kwargs: Дополнительные параметры для метаданных:
                - dtype: тип данных (например, 'float32', 'uint8')
                - compress: сжатие (например, 'DEFLATE', 'LZW')
                - nodata: значение для no data
                - crs: система координат
                - transform: трансформация

        Returns:
            str: Путь к сохраненному файлу
        """
        # Подготавливаем путь
        output_path = self._prepare_output_path(output_path)

        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Подготавливаем метаданные
        meta = self.meta.copy()

        # Обновляем метаданные из kwargs
        if 'dtype' in kwargs:
            meta['dtype'] = kwargs['dtype']
        if 'compress' in kwargs:
            meta['compress'] = kwargs['compress']
        if 'nodata' in kwargs:
            meta['nodata'] = kwargs['nodata']
        if 'crs' in kwargs:
            meta['crs'] = kwargs['crs']
        if 'transform' in kwargs:
            meta['transform'] = kwargs['transform']

        # Обновляем размеры на основе текущих данных
        if self.data is not None:
            if len(self.data.shape) == 2:
                meta.update({
                    'count': 1,
                    'height': self.data.shape[0],
                    'width': self.data.shape[1]
                })
            else:
                meta.update({
                    'count': self.data.shape[0],
                    'height': self.data.shape[1],
                    'width': self.data.shape[2]
                })

        # Сохраняем данные
        with rasterio.open(output_path, 'w', **meta) as dst:
            if self.data is not None:
                dst.write(self.data)

        # Обновляем путь файла если он изменился
        if output_path != self.file_path:
            self.file_path = output_path
            self.image_name = os.path.basename(output_path).split(".")[0]

        print(f"Изображение сохранено: {output_path}")
        return output_path


    def print_info(self, include_children=False):
        """Выводит информацию об изображении"""
        file_size = os.path.getsize(self.file_path) / (1024 * 1024) if os.path.exists(self.file_path) else 0
        print(f"Image Dir: {self.image_dir}")
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

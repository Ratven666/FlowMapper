import os

import rasterio
import numpy as np
from rasterio.transform import from_bounds


class ImageSplitter:
    """
    Класс для рекурсивного разделения изображений на квадранты
    """

    def __init__(self):
        self.split_statistics = {
            'total_splits': 0,
            'files_created': 0,
            'temp_files_created': 0,
            'levels_created': 0
        }

    def split_image_into_quadrants(self, geotiff_image, save_dir=None, save_prefix=None):
        """
        Разбивает изображение на 4 квадранта (NW, NE, SW, SE)
        """
        self.split_statistics['total_splits'] += 1

        if geotiff_image.count > 1:
            print("Warning: Multi-band images will be processed band by band")

        quadrants = {}

        # Вычисляем середину изображения
        mid_x = geotiff_image.width // 2
        mid_y = geotiff_image.height // 2

        # Определяем границы для каждого квадранта
        bounds_nw = (geotiff_image.bounds.left,
                     geotiff_image.bounds.top - (geotiff_image.bounds.top - geotiff_image.bounds.bottom) / 2,
                     geotiff_image.bounds.left + (geotiff_image.bounds.right - geotiff_image.bounds.left) / 2,
                     geotiff_image.bounds.top)

        bounds_ne = (geotiff_image.bounds.left + (geotiff_image.bounds.right - geotiff_image.bounds.left) / 2,
                     geotiff_image.bounds.top - (geotiff_image.bounds.top - geotiff_image.bounds.bottom) / 2,
                     geotiff_image.bounds.right,
                     geotiff_image.bounds.top)

        bounds_sw = (geotiff_image.bounds.left,
                     geotiff_image.bounds.bottom,
                     geotiff_image.bounds.left + (geotiff_image.bounds.right - geotiff_image.bounds.left) / 2,
                     geotiff_image.bounds.bottom + (geotiff_image.bounds.top - geotiff_image.bounds.bottom) / 2)

        bounds_se = (geotiff_image.bounds.left + (geotiff_image.bounds.right - geotiff_image.bounds.left) / 2,
                     geotiff_image.bounds.bottom,
                     geotiff_image.bounds.right,
                     geotiff_image.bounds.bottom + (geotiff_image.bounds.top - geotiff_image.bounds.bottom) / 2)

        # Определяем размеры и координаты для каждого квадранта
        quadrant_specs = [
            {
                'corner': 'NW',
                'bounds': bounds_nw,
                'x_slice': slice(0, mid_x),
                'y_slice': slice(0, mid_y),
                'width': mid_x,
                'height': mid_y
            },
            {
                'corner': 'NE',
                'bounds': bounds_ne,
                'x_slice': slice(mid_x, geotiff_image.width),
                'y_slice': slice(0, mid_y),
                'width': geotiff_image.width - mid_x,
                'height': mid_y
            },
            {
                'corner': 'SW',
                'bounds': bounds_sw,
                'x_slice': slice(0, mid_x),
                'y_slice': slice(mid_y, geotiff_image.height),
                'width': mid_x,
                'height': geotiff_image.height - mid_y
            },
            {
                'corner': 'SE',
                'bounds': bounds_se,
                'x_slice': slice(mid_x, geotiff_image.width),
                'y_slice': slice(mid_y, geotiff_image.height),
                'width': geotiff_image.width - mid_x,
                'height': geotiff_image.height - mid_y
            }
        ]

        # Создаем директорию для сохранения, если указана
        if save_dir:
            self._ensure_directory_exists(save_dir)

        for spec in quadrant_specs:
            corner = spec['corner']
            bounds = spec['bounds']
            x_slice = spec['x_slice']
            y_slice = spec['y_slice']
            width = spec['width']
            height = spec['height']

            # Извлекаем данные для квадранта
            quadrant_data = np.zeros((geotiff_image.count, height, width), dtype=geotiff_image.data.dtype)

            for band in range(geotiff_image.count):
                band_data = geotiff_image.data[band]
                quadrant_data[band] = band_data[y_slice, x_slice]

            # Создаем метаданные для нового изображения
            new_meta = geotiff_image.meta.copy()
            new_meta.update({
                'width': width,
                'height': height,
                'transform': from_bounds(*bounds, width=width, height=height)
            })
            new_meta.update({
                'compress': 'lzw',
                'predictor': 2 if geotiff_image.data.dtype == np.uint16 else 1,
                'tiled': True,
                'blockxsize': 256,
                'blockysize': 256
            })

            # Создаем дочернее изображение
            child_image = self._create_quadrant_image(
                geotiff_image, quadrant_data, new_meta, corner,
                save_dir, save_prefix
            )

            if child_image:
                quadrants[corner] = child_image

        return quadrants

    def _create_quadrant_image(self, parent_image, quadrant_data, meta, corner, save_dir, save_prefix):
        """Создает дочернее изображение квадранта"""
        from app.image_code.GeoTiffImage import GeoTiffImage
        file_path = None

        try:
            if save_dir and save_prefix:
                # Сохраняем в файл
                filename = f"{save_prefix}_{corner}.tif"
                file_path = os.path.join(save_dir, filename)

                with rasterio.open(file_path, 'w', **meta) as dst:
                    dst.write(quadrant_data)

                self.split_statistics['files_created'] += 1
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                print(f"Created quadrant: {corner} - {meta['width']}x{meta['height']} - {file_size:.1f} MB")
            else:
                # Работа только в памяти (не реализована в этой версии)
                raise ValueError("In-memory only mode not implemented")
            # Создаем объект GeoTiffImage
            child_image = GeoTiffImage(
                file_path=file_path,
                level=parent_image.level + 1
            )


            return child_image

        except Exception as e:
            print(f"Error creating quadrant {corner}: {e}")
            # Удаляем файл в случае ошибки
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            return None

    def recursive_split(self, geotiff_image, max_level, save_dir=None, current_level=0):
        """
        Рекурсивно разбивает изображение до указанного уровня
        """
        if current_level >= max_level:
            return {}

        print(f"\n--- Splitting level {current_level} ---")

        # Создаем поддиректорию для текущего уровня
        level_save_dir = None
        if save_dir:
            level_save_dir = os.path.join(save_dir, f"level_{current_level + 1}")
            self._ensure_directory_exists(level_save_dir)

        save_prefix = f"{geotiff_image.image_name}_L{current_level + 1}"
        quadrants = self.split_image_into_quadrants(geotiff_image, level_save_dir, save_prefix)

        self.split_statistics['levels_created'] += 1

        # Рекурсивно разбиваем дочерние изображения
        all_children = quadrants.copy()
        if current_level + 1 < max_level:
            for corner, child in quadrants.items():
                if child:
                    print(f"Recursively splitting {corner} quadrant...")
                    child_quadrants = self.recursive_split(child, max_level, save_dir, current_level + 1)
                    all_children.update(child_quadrants)

        return all_children

    @staticmethod
    def _ensure_directory_exists(directory):
        """Создает директорию, если она не существует"""
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")

    def print_statistics(self):
        """Выводит статистику разделения"""
        print("\n--- Split Statistics ---")
        print(f"Total splits: {self.split_statistics['total_splits']}")
        print(f"Files created: {self.split_statistics['files_created']}")
        print(f"Temp files created: {self.split_statistics['temp_files_created']}")
        print(f"Levels created: {self.split_statistics['levels_created']}")


if __name__ == "__main__":
    from app.image_code.GeoTiffImage import GeoTiffImage

    img = GeoTiffImage(file_path="../../../src/base_img.tif")
    img.print_info()

    print("\n--- Using ImageSplitter ---")

    # Создаем сплиттер с настройками
    splitter = ImageSplitter()

    # Выполняем рекурсивное разделение
    save_directory = "../../src/split_images"
    # splitter._ensure_directory_exists(save_directory)

    all_images = splitter.recursive_split(img, max_level=3, save_dir=save_directory)

    # Выводим статистику
    splitter.print_statistics()

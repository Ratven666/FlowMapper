import json
import numpy as np
from rasterio import features
from shapely.geometry import shape
from app.image_code.BinaryGeoTiffImage import BinaryGeoTiffImage


class Vectorizator:

    def __init__(self, binary_geotiff_image: BinaryGeoTiffImage):
        self.base_image = binary_geotiff_image
        self._geojson_data = None

    @property
    def geojson_data(self):
        if self._geojson_data is None:
            self._calculate_geojson()
        return self._geojson_data

    def _calculate_geojson(self):
        """
        Конвертирует GeoTiffImage в GeoJSON с полигонами для значений 1
        и подсчитывает количество пикселей в каждом полигоне
        """
        # Используем данные из объекта GeoTiffImage
        data = self.base_image.data[0]  # Первый канал
        transform = self.base_image.transform

        # Получаем маску для значений 1
        mask = data == 1

        # Извлекаем полигоны из растра
        shapes = features.shapes(data, mask=mask, transform=transform)

        # Создаем GeoJSON структуру
        self._geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }
        # Добавляем полигоны в GeoJSON с подсчетом пикселей
        for geom, value in shapes:

            feature = {
                "type": "Feature",
                "properties": {
                    "value": int(value),
                },
                "geometry": geom
            }
            self._geojson_data["features"].append(feature)
        return self._geojson_data

    def calculate_with_pixel_count(self):
        """
        Конвертирует GeoTiffImage в GeoJSON с полигонами для значений 1
        и подсчитывает количество пикселей в каждом полигоне
        """
        # Используем данные из объекта GeoTiffImage
        data = self.base_image.data[0]  # Первый канал
        transform = self.base_image.transform

        # Получаем маску для значений 1
        mask = data == 1

        # Извлекаем полигоны из растра
        shapes = features.shapes(data, mask=mask, transform=transform)

        # Создаем GeoJSON структуру
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        # Добавляем полигоны в GeoJSON с подсчетом пикселей
        for geom, value in shapes:
            # Подсчитываем количество пикселей в полигоне
            pixel_count = self._count_pixels_in_polygon(geom, data, transform)

            feature = {
                "type": "Feature",
                "properties": {
                    "value": int(value),
                    "pixel_count": pixel_count
                },
                "geometry": geom
            }
            geojson_data["features"].append(feature)

        self._geojson_data = geojson_data
        return geojson_data

    @staticmethod
    def _count_pixels_in_polygon(geometry, data, transform):
        """
        Подсчитывает количество пикселей в полигоне

        Args:
            geometry: геометрия полигона в GeoJSON формате
            data: данные изображения
            transform: трансформация растра

        Returns:
            int: количество пикселей в полигоне
        """
        try:
            # Создаем маску для текущего полигона
            polygon_mask = features.geometry_mask(
                [geometry],
                out_shape=data.shape,
                transform=transform,
                invert=True  # invert=True означает, что полигон будет True, а фон False
            )

            # Применяем исходную маску (только значения 1)
            value_mask = data == 1

            # Комбинируем маски: пиксели должны быть и в полигоне и иметь значение 1
            combined_mask = polygon_mask & value_mask

            # Подсчитываем количество пикселей
            pixel_count = np.sum(combined_mask)

            return int(pixel_count)

        except Exception as e:
            print(f"Ошибка при подсчете пикселей: {e}")
            return 0

    def save_geojson(self, file_path):
        """Сохраняет GeoJSON в файл"""
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.geojson_data, f, indent=2, ensure_ascii=False)

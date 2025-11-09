import numpy as np
import rasterio
import os
import tempfile

class ImageBinarizer:
    """
    Класс для бинаризации данных FlowGeoTiffImage
    """

    def __init__(self, flow_image):
        """
        Инициализация бинаризатора

        Args:
            flow_image: объект FlowGeoTiffImage
        """
        self.flow_image = flow_image
        self.data = flow_image.data

    def binary_threshold(self, threshold=0.0, output_path=None):
        """
        Бинаризация с одним порогом

        Args:
            threshold: пороговое значение (ниже - 0, выше или равно - 1)
            output_path: путь для сохранения результата (если None - создается временный файл)

        Returns:
            GeoTiffImage: объект с бинаризированными данными
        """
        # Бинаризация: значения >= threshold -> 1, значения < threshold -> 0
        binary_data = np.where(self.data >= threshold, 1.0, 0.0)

        return self._create_binary_geotiff(binary_data, output_path,
                                           f"binary_threshold_{threshold}")

    def binary_range(self, min_threshold, max_threshold, output_path=None):
        """
        Бинаризация с диапазоном

        Args:
            min_threshold: минимальный порог
            max_threshold: максимальный порог
            output_path: путь для сохранения результата (если None - создается временный файл)

        Returns:
            GeoTiffImage: объект с бинаризированными данными
        """
        if min_threshold >= max_threshold:
            raise ValueError("min_threshold должен быть меньше max_threshold")

        # Бинаризация: значения в диапазоне [min_threshold, max_threshold] -> 1, остальные -> 0
        binary_data = np.where((self.data >= min_threshold) & (self.data <= max_threshold), 1.0, 0.0)

        return self._create_binary_geotiff(binary_data, output_path,
                                           f"binary_range_{min_threshold}_{max_threshold}")

    def binary_default(self, output_path=None):
        """
        Бинаризация по умолчанию: нули -> 0, не нули -> 1

        Args:
            output_path: путь для сохранения результата (если None - создается временный файл)

        Returns:
            GeoTiffImage: объект с бинаризированными данными
        """
        # Бинаризация: значения != 0 -> 1, значения == 0 -> 0
        binary_data = np.where(self.data != 0.0, 1.0, 0.0)

        return self._create_binary_geotiff(binary_data, output_path, "binary_default")

    def _create_binary_geotiff(self, binary_data, output_path, method_name):
        """
        Создает GeoTiffImage с бинаризированными данными

        Args:
            binary_data: бинаризированные данные
            output_path: путь для сохранения
            method_name: название метода для имени файла

        Returns:
            GeoTiffImage: объект с бинаризированными данными
        """
        if output_path is None:
            # Создаем временный файл
            temp_dir = tempfile.gettempdir()
            base_name = f"{self.flow_image.image_name}_{method_name}"
            output_path = os.path.join(temp_dir, f"{base_name}.tif")

        # Обновляем метаданные для бинаризированного изображения
        meta = self.flow_image.meta.copy()
        meta.update({
            'dtype': 'float32',
            'count': 1,  # Бинаризированное изображение обычно одноканальное
            'nodata': 0.0
        })

        # Подготавливаем данные для записи
        if len(binary_data.shape) == 2:
            # 2D данные: (height, width) -> преобразуем в (1, height, width)
            write_data = binary_data.reshape((1, binary_data.shape[0], binary_data.shape[1]))
        elif len(binary_data.shape) == 3:
            # 3D данные: (count, height, width)
            if binary_data.shape[0] > 1:
                # Для многоканальных изображений используем первый канал
                # или можно изменить логику на усреднение по каналам
                write_data = binary_data[0:1]  # Берем только первый канал
            else:
                write_data = binary_data
        else:
            raise ValueError(f"Неожиданная форма данных: {binary_data.shape}")

        # Убеждаемся, что данные имеют правильную форму (1, height, width)
        if write_data.shape[0] != 1:
            write_data = write_data[0:1]

        # Сохраняем бинаризированные данные в GeoTIFF файл
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(write_data.astype('float32'))

        # Создаем объект GeoTiffImage
        from app.image_code.GeoTiffImage import GeoTiffImage
        binary_geotiff = GeoTiffImage(output_path)

        return binary_geotiff

    def get_statistics(self):
        """
        Возвращает статистику данных для помощи в выборе порогов

        Returns:
            dict: словарь со статистикой
        """
        if self.data is not None:
            # Игнорируем нулевые значения для статистики
            non_zero_data = self.data[self.data != 0.0]

            stats = {
                'min': np.min(self.data),
                'max': np.max(self.data),
                'mean': np.mean(self.data),
                'median': np.median(self.data),
                'std': np.std(self.data),
                'non_zero_min': np.min(non_zero_data) if len(non_zero_data) > 0 else 0,
                'non_zero_max': np.max(non_zero_data) if len(non_zero_data) > 0 else 0,
                'non_zero_mean': np.mean(non_zero_data) if len(non_zero_data) > 0 else 0,
                'zero_count': np.sum(self.data == 0.0),
                'non_zero_count': np.sum(self.data != 0.0)
            }
            return stats
        return {}


# Пример использования
if __name__ == "__main__":
    from app.image_code.FlowGeoTiffImage import FlowGeoTiffImage
    # Создаем FlowGeoTiffImage
    flow_img = FlowGeoTiffImage(file_path="../../../src/base_img_L1_NE_L2_NE_L3_SW.tif")

    # Создаем бинаризатор
    binarizer = ImageBinarizer(flow_img)

    # Получаем статистику для выбора порогов
    stats = binarizer.get_statistics()
    print("Статистика данных:", stats)

    # Бинаризация по умолчанию (нули -> 0, не нули -> 1)
    binary_default = binarizer.binary_default()
    # binary_default.show()
    # print(binary_default.data[0])
    #

    # # Бинаризация с одним порогом
    binary_threshold = binarizer.binary_threshold(threshold=0.000000001)
    # binary_threshold.show()
    #
    # # Бинаризация с диапазоном
    binary_range = binarizer.binary_range(min_threshold=0.1, max_threshold=0.9)
    # binary_range.show()
    #
    # # Проверяем результаты
    binary_default.print_info()
    binary_threshold.print_info()
    binary_range.print_info()
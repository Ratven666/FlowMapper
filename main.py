import os

from app.image_code.utils.Vectorizator import Vectorizator
from app.image_code.BinaryGeoTiffImage import BinaryGeoTiffImage

from tqdm import tqdm
import os


def process_image(file_path, split_level=3, calculate_pixels=False):
    base_image = BinaryGeoTiffImage(file_path=file_path)
    base_image.split_image(max_level=split_level)
    print(f"Processing {base_image.image_name}")

    deepest_dir = os.path.join(os.path.dirname(file_path), base_image.image_name, f"level_{split_level}")
    result_dir_path = os.path.join(os.path.dirname(file_path), base_image.image_name, "GeoJSONs")
    os.makedirs(result_dir_path, exist_ok=True)

    tiff_files = [f for f in os.listdir(deepest_dir) if f.endswith((".tif", ".tiff"))]

    # Прогресс-бар с дополнительными параметрами
    with tqdm(total=len(tiff_files),
              desc="Векторизация",
              unit="файл",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

        for filename in tiff_files:
            current_file_path = os.path.join(deepest_dir, filename)
            # Обновляем описание с текущим файлом
            pbar.set_postfix(file=filename[:20])  # Показываем первые 20 символов имени
            current_img = BinaryGeoTiffImage(file_path=current_file_path)
            vectorizer = Vectorizator(binary_geotiff_image=current_img)
            if calculate_pixels:
                vectorizer.calculate_with_pixel_count()
            file_path_for_gjson = os.path.join(result_dir_path, f"{current_img.image_name}.geojson")
            vectorizer.save_geojson(file_path=file_path_for_gjson)
            # Обновляем прогресс
            pbar.update(1)


if __name__ == "__main__":
    file_path = "src/ID132_N60_E20_RP100_depth.tif"

    process_image(file_path=file_path, calculate_pixels=False)

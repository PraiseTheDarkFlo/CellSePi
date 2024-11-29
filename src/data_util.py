import os
import pathlib
import shutil

import numpy as np
from PIL import Image
from readlif.reader import LifFile


def listdir(directory):
    dir_list = [directory / elem for elem in os.listdir(directory)]
    return dir_list


def organize_files(files, channel_prefix, mask_suffix=""):
    id_to_file = {}
    for file in files:
        if channel_prefix in file.name:
            image_id, channel_id = file.stem.replace(mask_suffix, "").split(channel_prefix)
            channel_id = int(channel_id)
            if image_id not in id_to_file:
                id_to_file[image_id] = {}

            if channel_id in id_to_file[image_id]:
                raise Exception(
                    f"""The directory already includes a file with the same image and channel ids.
                                Image Id: {image_id}
                                Channel Id: {channel_id}
                                Path: {file}""")
            id_to_file[image_id][channel_id] = file

    return id_to_file


def load_directory(directory, bright_field_channel=None, channel_prefix=None, mask_suffix=None):
    assert directory is not None

    if bright_field_channel is None:
        bright_field_channel = 1

    if channel_prefix is None:
        channel_prefix = "c"

    if mask_suffix is None:
        mask_suffix = "_seg"


    names = os.listdir(directory)
    paths = [directory / name for name in names]

    file_paths = [path for path in paths if path.is_file()]

    tiff_files = [path for path in file_paths if path.suffix == ".tif" or path.suffix == ".tiff"]
    # lif_files = [path for path in file_paths if path.suffix == ".lif"]
    mask_files = [path for path in file_paths if path.suffix == ".npy" and path.stem.endswith(mask_suffix)]

    #    if len(lif_files) > 0:
    #        raise Exception("Lif Files are currently not supported.")

    # image_ids = [(file.stem.split(channel_prefix)[0], file) for file in tiff_files]

    id_to_image = organize_files(tiff_files, channel_prefix=channel_prefix)
    id_to_mask = organize_files(mask_files, channel_prefix=channel_prefix, mask_suffix=mask_suffix)

    return id_to_image, id_to_mask
    # raise Exception("Not Implemented Yet")

def copy_files_between_directories(source_dir, target_dir, file_types = None):
    file_filter = lambda file_path: file_path.is_file() and (True if file_types is None else file_path.suffix in file_types)


    files = listdir(source_dir)
    files_to_copy = [file for file in files if file_filter(file)]

    for file in files_to_copy:
        src_path = file
        target_path = target_dir / file.name
        shutil.copyfile(src_path, target_path)




def extract_from_lif_file(lif_path, target_dir):
    # lif_path = "/Users/erik/Documents/Promotion/Projekte/Anjas_Stuff/_data/Segmentation Training Data/28-06-2024/HEK293_mTagBFP_mNeonGreen_CellMaskDR_01.lif"
    # target_dir = lif_path.parent / "output/"

    lif_path = pathlib.Path(lif_path)

    lif = LifFile(lif_path)

    os.makedirs(target_dir, exist_ok=True)

    for series in lif.get_iter_image():
        img_id = series.info["name"]
        n_channels = series.channels
        for channel_id in range(n_channels):
            img = series.get_frame(c=channel_id)
            img.save(target_dir / f"{img_id}c{channel_id + 1}.tif")
            pass


def load_image_to_numpy(path):
    im = Image.open(path)
    array = np.array(im)
    return array


def write_numpy_to_image(array, path):
    im = Image.fromarray(array)
    im.save(path)
    pass


def remove_gradient(img):
    top = np.median(img[100:200, 400: -400])
    bottom = np.median(img[-200:-100, 400: -400])

    left = np.median(img[400:-400, 100: 200])
    right = np.median(img[400:-400, -200: -100])

    median = np.median(img[200:-200, 200:-200])

    max_val = np.max([top, bottom, left, right])

    row_count = img.shape[0]

    X = np.arange(row_count) / (row_count - 1)
    b = bottom
    a = top - bottom
    Y_v = a * X + b
    Y_v -= median

    b = right
    a = left - right
    Y_h = a * X + b
    Y_h -= median

    correction_v = np.tile(Y_v, (row_count, 1)).transpose()
    correction_h = np.tile(Y_h, (row_count, 1))
    correction = correction_h + correction_v

    corrected_img = img + correction
    return corrected_img

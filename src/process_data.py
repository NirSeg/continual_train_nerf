import copy
import os
import shutil
import json
import re
from pathlib import Path
import subprocess


def colmap_process(source_dir: str | os.PathLike | Path, num_sets: int):
    temp_dir = source_dir.joinpath('temp')
    if not temp_dir.joinpath('transforms.json').exists() and temp_dir.exists():
        process_data_cmd = ['ns-process-data', 'images', '--data', temp_dir.joinpath('images'), '--output-dir',
                            temp_dir]
        subprocess.check_call(process_data_cmd)
        create_image_sets(temp_dir, source_dir, num_sets)


def create_image_sets(source_dir, destination_dir, num_sets):
    # ceate the destination folder if it doesn't exist (set_0, set_1, ...)
    for i in range(num_sets):
        set_folder = os.path.join(f"{destination_dir}/set_{i}", "images")
        set_folder_2 = os.path.join(f"{destination_dir}/set_{i}", "images_2")
        set_folder_4 = os.path.join(f"{destination_dir}/set_{i}", "images_4")
        set_folder_8 = os.path.join(f"{destination_dir}/set_{i}", "images_8")
        os.makedirs(set_folder, exist_ok=True)
        os.makedirs(set_folder_2, exist_ok=True)
        os.makedirs(set_folder_4, exist_ok=True)
        os.makedirs(set_folder_8, exist_ok=True)

    # create a list of all the images in the source folder
    image_files = [f for f in os.listdir(f"{source_dir}/images")]
    image_files_2 = [f for f in os.listdir(f"{source_dir}/images_2")]
    image_files_4 = [f for f in os.listdir(f"{source_dir}/images_4")]
    image_files_8 = [f for f in os.listdir(f"{source_dir}/images_8")]
    num_images = len(image_files)

    with open(source_dir.joinpath('transforms.json'), 'r') as json_file:
        data = json.load(json_file)

    # we assume that the number of images in each set should be equal
    set_size = num_images // num_sets
    num_frames = len(data['frames'])

    image_files_all = [image_files, image_files_2, image_files_4, image_files_8]
    folders = ["images", "images_2", "images_4", "images_8"]

    # copy the images to the destination folders
    for folder in folders:
        current_set = 0
        image_index = 0
        image_files = image_files_all[folders.index(folder)]

        for image_file in image_files:
            source_path = os.path.join(f"{source_dir}/{folder}", image_file)
            destination_path = os.path.join(destination_dir, f"set_{current_set}/{folder}", image_file)
            shutil.copyfile(source_path, destination_path)
            image_index += 1
            if image_index == set_size:
                current_set += 1
                image_index = 0

    # create the transforms.json file for each set
    for i in range(num_sets):
        set_data = copy.deepcopy(data)
        set_data['frames'] = []
        # set_data = {'frames': []}
        for j in range(num_frames):
            frame_number = int(re.search(r'frame_(\d+)', data['frames'][j]['file_path']).group(1))
            if frame_number < set_size * (i + 1) + 1 and frame_number >= set_size * i + 1:
                set_data['frames'].append(data['frames'][j])
        sorted_frames = sorted(set_data['frames'],
                               key=lambda frame: int(frame['file_path'].split('_')[-1].split('.')[0]))
        set_data['frames'] = sorted_frames

        set_folder = f"{destination_dir}/set_{i}"
        os.makedirs(set_folder, exist_ok=True)

        with open(f"{set_folder}/transforms.json", 'w') as outfile:
            json.dump(set_data, outfile, indent=4)



from numpy import ndarray
import os
from pathlib import Path
import json
import re
import cv2
import shutil


class Masks:
    def __init__(self, images_dir: str | os.PathLike | Path, rendered_images_dir: str | os.PathLike | Path):
        self.images_dir = Path(images_dir)
        self.rendered_images_dir = Path(rendered_images_dir)
        self.masks_dir = Path(os.path.dirname(images_dir)).joinpath('masks')
        self._images = None
        self._rendered_images = None
        self._masks = None

    @property
    def get_images(self):
        if self._images is None:
            self._images = []
            image_files = [file for file in os.listdir(self.images_dir) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
            for image_file in image_files:
                image_path = self.images_dir.joinpath(image_file)
                self._images.append(cv2.imread(image_path))
        return self._images

    @property
    def get_rendered_images(self):
        if self._rendered_images is None:
            self._rendered_images = []
            image_files = [file for file in os.listdir(self.rendered_images_dir) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
            for image_file in image_files:
                image_path = self.images_dir.joinpath(image_file)
                self._rendered_images.append(cv2.imread(image_path))
        return self._rendered_images

    @property
    def get_masks(self):
        self.get_images()
        self.get_rendered_images()
        if self._masks is None:
            self._masks = []
            for idx, _ in enumerate(self._images):
                self.get_mask(idx=idx)

    def get_mask(self, idx: int):
        image = self._images[idx]
        rendered_image = self._rendered_images[idx]



def add_masks_path(directory_path):
    masks_path = f"{directory_path}/masks"
    transforms_path = f"{directory_path}/transforms.json"

    if os.path.exists(masks_path) != True:
        print("masks folder does not exist")

    with open(transforms_path, 'r') as json_file:
        data = json.load(json_file)

    for i in range(len(data['frames'])):
        frame_number = int(re.search(r'frame_(\d+)', data['frames'][i]['file_path']).group(1))
        if os.path.exists(f"{masks_path}/mask000{frame_number}.png") != True:
            print(f"mask000{frame_number}.jpg does not exist")
            print("function stopped")
            return None
        data['frames'][i]['masks_path'] = f"masks/mask000{frame_number}.png"

    with open(transforms_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    # need to change the directory path for each set
    directory_path = 'C:/Users/avish/OneDrive/Documents/project/temp/Sets/Set_1'
    add_masks_path(directory_path)
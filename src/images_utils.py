import os
import cv2
from pathlib import Path


class ImagesData:
    def __init__(self, path_to_data: str | os.PathLike | Path):
        self._path = path_to_data
        self._num_sets = sum(1 for entry in os.scandir(self._path) if entry.is_dir())
        self._frames = []
        self._num_frames_per_set = []
        for i in range(self._num_sets):
            path_to_cur_images = self._path.joinpath(f'set_{i}/images')
            images = []
            for filename in os.listdir(path_to_cur_images):
                if filename.endswith(('.JPG', '.jpg', 'jpeg', '.png')):
                    image_path = path_to_cur_images.joinpath(filename)
                    images.append(cv2.imread(str(image_path)))
            self._num_frames_per_set.append(len(images))
            self._frames.append(images)
        self._height = None
        self._width = None

    @property
    def num_sets(self):
        return self._num_sets

    @property
    def num_frames_per_set(self):
        return self._num_frames_per_set

    def frame_count(self, num_set: int) -> int:
        return len(self._frames[num_set])

    @property
    def width(self) -> int:
        if self._width is None:
            self._width = self._frames[0][0].shape[1]
        return int(self._width)

    @property
    def height(self) -> int:
        if self._height is None:
            self._height = self._frames[0][0].shape[0]
        return int(self._height)

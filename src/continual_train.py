import os
from images_utils import ImagesData
from pathlib import Path
from argparse import ArgumentParser
import subprocess
import re
import time
from typing import Callable
from src.file_manager import FileManager
import shutil
import math
from process_data import colmap_process


def path(s):
    p = Path(s)
    return p


def parsed_args():
    parser = ArgumentParser('Continual_NeRF', description='NeRF for continual scene.',
                            epilog="Flow: 1. Process images (COLMAP). 2. Train NeRF model on set 0. "
                                   "3. render images on cameras extrinsic of the current set. "
                                   "4. build masks for the current set. "
                                   "5. retrain the model on the current set with the mask we built. "
                                   "6. repeat phases 3-5 according to the number of the sets (not including set 0)")
    parser.add_argument('-d', '--data-path', type=path, required=True,
                        help="Path to the data directory to process.")
    parser.add_argument('--skip-init-train', action='store_true',
                        help="Skip training of set 0, model was trained ahead of time.")
    parser.add_argument('--skip-train', action='store_true',
                        help="Skip training, model was trained ahead of time.")
    parser.add_argument('-n', '--num-sets', type=int, help="number of the sets")
    parser.add_argument('--train-from-checkpoint', action='store_true',
                        help="Continue training from checkpoint")
    args = parser.parse_args()
    if args.skip_train and args.train_from_checkpoint:
        parser.error('Can not use \'--skip-train\' and \'--train-from-checkpoint\' simultaneously!')
    return args


def process_data(processed_dir: os.PathLike, num_frames_per_set: list[int]):
    i = 0


def get_last_trained_model(trained_dir) -> Path:
    cmd_get_last_file = f'ls -lrt {trained_dir}  | tail -n1 | awk \'{{ print $9 }}\''
    last_trained_config_dir = Path(subprocess.check_output(cmd_get_last_file, shell=True).decode('utf-8').strip())
    return last_trained_config_dir


def kill_init_train_cond(s: str):
    match = re.search(r'.*100\.\d{1,2}%.*', s)
    if match:
        time.sleep(20)
        return True
    return False


def execute_and_track_output(cmd: list[str], kill_proc_cond: Callable[[str], bool] = None):
    """
    Execute command and return the output in live.
    :param cmd: Command to execute.
    :param kill_proc_cond: A condition that the process output satisfies that triggers terminate signal(ctrl+c).
    :raises StopIteration: In case on a failure in child process.
    :raises CalledProcessError: In case on a failure in child process.
    :return: A generator object with the subprocess output
    """
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        if kill_proc_cond is not None and kill_proc_cond(stdout_line):
            popen.stdout.close()
            popen.terminate()
            return 'Kill prompt detected, terminated child process.'
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def init_train(processed_dir: str | os.PathLike | Path, project_name: str, skip_init_train: bool,
               train_from_checkpoint: bool):
    output_dir = Path(f'/workspace/outputs/{project_name}')
    train_cmd = ['ns-train', 'nerfacto', '--data', processed_dir.joinpath('set_0'), '--output-dir', output_dir,
                 '--pipeline.datamanager.camera-optimizer.mode', 'off']
    if skip_init_train:
        print('Training model skipped.')
    # elif train_from_checkpoint:
    #     path_to_latest_checkpoint = trained_dir.joinpath(get_last_trained_model(trained_dir)).joinpath('nerfstudio_models')
    #     if path_to_latest_checkpoint is :
    #         print('Training model from checkpoint...')
    #         train_cmd.extend(['--load-dir', path_to_latest_checkpoint])
    #     else:
    #         skip_init_train = True
    else:
        print(f'Going to train NeRF model on COLMAP data, with command:')

    if not skip_init_train:
        for line in execute_and_track_output(train_cmd, kill_proc_cond=kill_init_train_cond):
            print(line, end='')


def train(processed_dir: str | os.PathLike | Path, project_name: str, num_set: int):
    output_dir = Path(f'/workspace/outputs/{project_name}')
    train_cmd = ['ns-train', 'nerfacto', '--data', processed_dir.joinpath(f'set_{num_set}'), '--output_dir', output_dir,
                 '--pipeline.datamanager.camera-optimizer.mode', 'off']
    trained_dir = Path(f'/workspace/outputs/{project_name}/set_{num_set - 1}/nerfacto')
    path_to_latest_checkpoint = trained_dir.joinpath(get_last_trained_model(trained_dir)).joinpath('nerfstudio_models')
    train_cmd.extend(['--load-dir', path_to_latest_checkpoint])
    print(f'trains on set{num_set}')
    for line in execute_and_track_output(train_cmd, kill_proc_cond=kill_init_train_cond):
        print(line, end='')


# def get_cameras_extrinsic(set_name):


def render_next_images(images_data: ImagesData, trained_dir: str | os.PathLike | Path):
    last_trained_config_dir = get_last_trained_model(trained_dir)
    fm = FileManager(trained_dir.joinpath(last_trained_config_dir).joinpath('config.yml'))
    cameras_extrinsic = fm.viewer_next_poses(all_poses=True, update_poses=True)

    x = 'horizontal' if images_data.height > images_data.width else 'vertical'
    focal_length = fm.load_transforms_file().intrinsics.fl_y if x == 'horizontal' else fm.load_transforms_file().intrinsics.fl_x
    front_edge = images_data.height
    fov = 2 * math.atan(front_edge / (2 * focal_length)) * 180 / math.pi
    cam_path_filename = 'camera_path'
    fps = 1
    full_cam_path = fm.generate_cam_path_file(cam_path_filename, fps=fps, fov=int(fov + 0.5),
                                              look_at_cameras=cameras_extrinsic)

    shutil.rmtree(fm.last_render_dir)
    os.makedirs(fm.last_render_dir)
    render_cmd = ['ns-render', 'camera-path', '--output-format', 'images',
                  '--load-config', str(fm.config_path),
                  '--output-path', str(fm.last_render_dir),
                  '--camera-path-filename', str(full_cam_path)]
    print(f'Synthesizing frames with cmd:\n{render_cmd}')

    try:
        subprocess.check_call(render_cmd)
    except subprocess.CalledProcessError as e:
        print(f'Command:\n{render_cmd}\n,Failed with return code:{e.returncode}.')
        exit(-1)
    print('Done!')


def continual_train(args):
    # ---------------------------------------  Preprocess via COLMAP  --------------------------------------------
    colmap_process(args.data_path, args.num_sets)
    # ---------------------------------------  Preprocess images metadata  ----------------------------------------
    images_data = ImagesData(args.data_path)
    processed_dir = Path(args.data_path)
    # ---------------------------------------  Train the model on set 0  ----------------------------
    project_name = processed_dir.name
    init_train(processed_dir, project_name, args.skip_init_train, args.train_from_checkpoint)

    for i in range(1, images_data.num_sets):
        processed_dir_cur_set = processed_dir.joinpath(f'set_{i}')
        trained_dir = Path(f'/workspace/outputs/{project_name}/set_{i - 1}/nerfacto')
        # ---------------------------------------  render new images from cameras extrinsic of set i  ------------------
        render_next_images(images_data, trained_dir)
        # ---------------------------------------  build masks for set i  ----------------------------------------
        j = 0
        # ---------------------------------------  retrain the model on set i  ----------------------------------------
        train(processed_dir, project_name, i)


def run_viewer(args):
    project_name = args.data_path.name
    config_path = Path(f'/workspace/outputs/{project_name}/set_0/nerfacto')
    config_path = config_path.joinpath(get_last_trained_model(config_path)).joinpath('config.yml')

    viewer_cmd = ['ns-viewer', '--load-config', config_path]
    subprocess.check_call(viewer_cmd)


if __name__ == '__main__':
    args = parsed_args()
    if args.skip_train:
        i = 0
        run_viewer(args)
    else:
        continual_train(args)

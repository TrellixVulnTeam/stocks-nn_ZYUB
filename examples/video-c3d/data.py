# ----------------------------------------------------------------------------
# Copyright 2016 Nervana Systems Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

import os
import numpy as np
from neon.data.aeon_shim import AeonDataLoader
from neon.data.dataloader_transformers import OneHot, TypeCast
from neon.util.persist import get_data_cache_or_nothing


def common_config(manifest_file, manifest_root, batch_size):
    cache_root = get_data_cache_or_nothing('ucf-cache/')
    return {
               'manifest_filename': manifest_file,
               'manifest_root': manifest_root,
               'minibatch_size': batch_size,
               'macrobatch_size': batch_size * 12,
               'type': 'video,label',
               'cache_directory': cache_root,
               'video': {'max_frame_count': 16,
                         'frame': {'height': 112,
                                   'width': 112,
                                   'scale': [0.875, 0.875]}},
               'label': {'binary': False}
            }


def make_test_loader(manifest_file, manifest_root, backend_obj, subset_pct=100):
    aeon_config = common_config(manifest_file, manifest_root, backend_obj.bsz)
    aeon_config['subset_fraction'] = float(subset_pct/100.0)
    dl = AeonDataLoader(aeon_config, backend_obj)
    dl = OneHot(dl, index=1, nclasses=101)
    dl = TypeCast(dl, index=0, dtype=np.float32)
    return dl


def make_train_loader(manifest_file, manifest_root, backend_obj, subset_pct=100, random_seed=0):
    aeon_config = common_config(manifest_file, manifest_root, backend_obj.bsz)
    aeon_config['subset_fraction'] = float(subset_pct/100.0)
    aeon_config['shuffle_manifest'] = True
    aeon_config['shuffle_every_epoch'] = True
    aeon_config['random_seed'] = random_seed

    aeon_config['video']['frame']['center'] = False
    aeon_config['video']['frame']['flip_enable'] = True

    dl = AeonDataLoader(aeon_config, backend_obj)
    dl = OneHot(dl, index=1, nclasses=101)
    dl = TypeCast(dl, index=0, dtype=np.float32)
    return dl


def make_inference_loader(manifest_file, backend_obj):
    manifest_root = ""  # This is used for demo script which generates abs path manifest
    aeon_config = common_config(manifest_file, manifest_root, backend_obj.bsz)
    aeon_config['type'] = 'video'  # No labels provided
    aeon_config.pop('label', None)
    dl = AeonDataLoader(aeon_config, backend_obj)
    dl = TypeCast(dl, index=0, dtype=np.float32)
    return dl


def accumulate_video_pred(manifest_file, manifest_root, clip_preds):
    #  Index file will look like:
    #  video_clip_file,label_file
    #  video_clip_file will be video_path/v_WritingOnBoard_g05,
    #  where WritingOnBoard_g05 is the video name
    video_pred = {}
    clip_files = np.genfromtxt(manifest_file, dtype=None, delimiter=',', usecols=(0))
    for clip_file, pred in zip(clip_files, clip_preds):
        clip_file_abs = os.path.join(manifest_root, clip_file)
        video_name = '_'.join(os.path.basename(clip_file_abs).split('_')[1:-2])
        category = os.path.split(os.path.dirname(clip_file_abs))[-1]
        video_pred.setdefault(video_name, (category, [])).__getitem__(1).append(pred)

    return video_pred

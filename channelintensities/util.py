import json
import skimage.io, skimage.transform, skimage.util
import numpy as np
import pandas as pd
import os

def load_json(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)

    for i, bbox in enumerate(data['bboxs']):
        data['bboxs'][i] = [(point[0], point[1]) for point in bbox]
    
    return data

def load_data(json_info=None, 
              path=None, 
              tiff_dim=None, 
              angle=None, 
              frames_to_skip=None, 
              dim_order=None,
              fl_channel=None,
              path_fl=None,
              path_bf=None,):


    any_other_input_provided = path or tiff_dim or angle or frames_to_skip or dim_order or fl_channel or path_fl or path_bf
    if json_info is not None:
        angle = json_info['angle']
        frames_to_skip = json_info['frames_to_skip']
        tiff_dim = json_info['tiff_dim']
        dim_order = json_info['dim_order']
        path = json_info['path']
        fl_channel = json_info['fl_channel']
        path_fl = json_info['path_fl']
        path_bf = json_info['path_bf']

    if fl_channel == 'normal':
        bf_channel = 1
        fl_channel = 0
    elif fl_channel == 'switched':
        bf_channel = 0
        fl_channel = 1

    if any_other_input_provided and json_info:
        raise ValueError("You can't provide both a json file and other inputs")
    
    if (path_bf and not path_fl) or (path_fl and not path_bf):
        raise ValueError("You need to provide both a path for the brightfield and the fluorescence images")
    if path_bf and path:
        raise ValueError("You can't provide both a path for the tiff file and paths for the brightfield and fluorescence images")

    desired_dim_order = ['channels', 'time', 'x', 'y']
    if tiff_dim == 4:
        if not os.path.isfile(path):
            raise ValueError("The path provided is not valid")
        data = skimage.io.imread(path)

    elif tiff_dim == 3:
        if os.path.isfile(path_bf) and os.path.isfile(path_fl):
            bf = skimage.io.imread(path_bf)
            fl = skimage.io.imread(path_fl)
            data = np.array([bf, fl])
            new_dim = ['channels']
            dim_order  = new_dim + dim_order       
        else:
            raise ValueError("The paths provided are not valid")
        
        if not os.path.isfile(path):
            tiff_files = [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.tif') or file.endswith('.tiff')]
            tiff_files.sort()
            data = [skimage.io.imread(file) for file in tiff_files]
            data = np.array(data)
            new_dim = ['time']
            dim_order = new_dim + dim_order

    elif tiff_dim == 2:
        bf_files = [os.path.join(path_bf, file) for file in os.listdir(path_bf) if file.endswith('.tif') or file.endswith('.tiff')]
        fl_files = [os.path.join(path_fl, file) for file in os.listdir(path_fl) if file.endswith('.tif') or file.endswith('.tiff')]

        bf_files.sort()
        fl_files.sort()

        bf = [skimage.io.imread(file) for file in bf_files]
        fl = [skimage.io.imread(file) for file in fl_files]

        data = np.array([bf, fl])

        new_dims = ['channels', 'time']
        dim_order = new_dims + dim_order
    
    dim_number = len(data.shape)
    if dim_number != 4:
        raise ValueError("The TIFF file must have 4 dimensions if single tiff is selected")

    dim_map = [dim_order.index(dim) for dim in desired_dim_order]

    # Rearrange the dimensions using numpy.transpose
    sorted_data = np.transpose(data, dim_map)
    bf = sorted_data[bf_channel]
    fl = sorted_data[fl_channel]

    bf = [skimage.util.img_as_float(img) for img in bf]
    fl = [skimage.util.img_as_float(img) for img in fl]

    if angle:
        bf = [skimage.transform.rotate(img, angle) for img in bf]
        fl = [skimage.transform.rotate(img, angle) for img in fl]
    if frames_to_skip:
        bf = [bf[i] for i in range(len(bf)) if i not in frames_to_skip]
        fl = [fl[i] for i in range(len(fl)) if i not in frames_to_skip]

    bf = np.array(bf)
    fl = np.array(fl)
    return bf, fl

def save_json(data):
    experiment_name = data['experiment_name']
    path = data['path']
    directory = os.path.dirname(path)
    json_path = os.path.join(directory, f"{experiment_name}.json")
    json_keys = ['experiment_name', 
                 'path', 
                 'angle', 
                 'bboxs', 
                 "weight_maps_path", 
                 "frames_to_skip",
                 "tiff_dim",
                 "dim_order",
                 "fl_channel",
                 "path_fl",
                 "path_bf",
                 "rows",
                 "frames_per_second",
                 "length_per_pixel"
                 ]
    data_json = data.copy()
    for key, value in data.items():
        if key not in json_keys:
            del data_json[key]
        if isinstance(value, np.ndarray):
            data_json[key] = value.tolist()
    
    for json_key in json_keys:
        if json_key not in data_json:
            data_json[json_key] = None

    with open(json_path, 'w') as f:
        json.dump(data_json, f, indent=4)

def save_res_json(path, experiment_name, bboxi, res_dict):
    directory = os.path.dirname(path)
    json_path = os.path.join(directory, f"{experiment_name}_bbox{bboxi}_res.json")
    with open(json_path, 'w') as f:
        json.dump(res_dict, f, indent=4)

def save_weight_maps(weight_maps_per_bbox, json_info):
    path = json_info['path']
    experiment_name = json_info['experiment_name']
    save_path = os.path.join(os.path.dirname(path), f"{experiment_name}_weight_maps.npz")

    np.savez_compressed(save_path, **{f"bbox_{i}": weight_maps for i, weight_maps in zip(range(len(weight_maps_per_bbox)), weight_maps_per_bbox)})
    json_info['weight_maps_path'] = save_path
    save_json(json_info)

def save_result(dicts, length_middle_lines, json_info):

    path = json_info['path']
    experiment_name = json_info['experiment_name']
    path = os.path.join(os.path.dirname(path), f"{experiment_name}_results_bbox_")

    i = 0
    dfs = []
    for length_middle_line, dict_position in zip(length_middle_lines, dicts):

        lengths = np.linspace(0, length_middle_line, len(dict_position[0]))

        df = pd.DataFrame(dict_position)
        df['length'] = lengths
        df.index.name = 'line_num'

        path_loc = path + f"{i}.csv"
        df.to_csv(path_loc, index=False)

        i += 1
        dfs.append(df)

    return dfs

def load_weight_maps(weight_maps_path):
    print('loading weight maps')
    data = np.load(weight_maps_path, allow_pickle=True)
    weight_maps = [data[key] for key in data.files]
    return weight_maps
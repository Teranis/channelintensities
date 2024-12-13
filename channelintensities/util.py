import json
import skimage.io, skimage.transform, skimage.util
import numpy as np
import pandas as pd
import os
import pickle
from tqdm import tqdm as tq

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
    if os.path.isfile(path):
        directory = os.path.dirname(path)
    else:
        directory = path
    json_path = os.path.join(directory, f"{experiment_name}.json")
    json_keys = ['experiment_name', 
                 'path', 
                 'angle', 
                 'bboxs', 
                 "frames_to_skip",
                 "tiff_dim",
                 "dim_order",
                 "fl_channel",
                 "path_fl",
                 "path_bf",
                 "rows",
                 "seconds_per_frame",
                 "length_per_pixel",
                 'lines_per_pixel_length',
                 'save_path_coords',
                 'save_path_crops',
                 ]
    data = {key: value for key, value in data.items() if key in json_keys}
    data = {key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in data.items()}
    for json_key in json_keys:
        if json_key not in data:
            data[json_key] = None

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)

def save_res_json(path, experiment_name, bboxi, res_dict):
    if os.path.isfile(path):
        directory = os.path.dirname(path)
    else:
        directory = path

    directory = os.path.join(directory, f"{experiment_name}_results")
    os.makedirs(directory, exist_ok=True)
    json_path = os.path.join(directory, f"{experiment_name}_bbox{bboxi}_res.json")
    with open(json_path, 'w') as f:
        json.dump(res_dict, f, indent=4)

def crop_weight_maps(weight_maps_per_bbox):
    print('Cropping weight maps')
    crop_coords_per_bbox = []
    crop_per_bbox = []

    img_shape = np.array(weight_maps_per_bbox[0][0]).shape
    for weight_maps in tq(weight_maps_per_bbox, desc='Cropping weight maps', total=len(weight_maps_per_bbox)):
        crop_coords = []
        crops = []
        nonzero_coords = np.argwhere(weight_maps != 0)
        layer_indices = nonzero_coords[:, 0]
        nonzero_coords = nonzero_coords[:, 1:]
        for j, weight_map in enumerate(weight_maps):
            nonzero_coords_layer = nonzero_coords[layer_indices == j]
            # if nonzero_coords_layer.size == 0:
            #     raise ValueError("No nonzero values found in weight map")
            min_x, min_y = np.min(nonzero_coords_layer, axis=0)
            max_x, max_y = np.max(nonzero_coords_layer, axis=0)
            
            # Adjusting the indices
            min_x, min_y, max_x, max_y = max(min_x - 1, 0), max(min_y - 1, 0), min(max_x + 2, img_shape[0]), min(max_y + 2, img_shape[1])

            crop_coords.append(((min_x, max_x), (min_y, max_y)))
            crops.append(weight_map[min_x:max_x, min_y:max_y])

            # assert crops[-1].shape == (max_x - min_x, max_y - min_y)

        crop_per_bbox.append(crops)
        crop_coords_per_bbox.append(crop_coords)
    return crop_per_bbox, crop_coords_per_bbox

def save_weight_maps(weight_maps_per_bbox, json_info):
    path = json_info['path']
    experiment_name = json_info['experiment_name']
    if os.path.isfile(path):
        path = os.path.dirname(path)
    save_folder = os.path.join(path, f"{experiment_name}_weight_maps")
    os.makedirs(save_folder, exist_ok=True)
    save_path_crops = os.path.join(save_folder, f"{experiment_name}_weight_maps_crops_bbox_{{index}}.npz")
    save_path_coords = os.path.join(save_folder, f"{experiment_name}_weight_maps_coords.npz")

    crop_per_bbox, crop_coords_per_bbox = crop_weight_maps(weight_maps_per_bbox)

    # Validate before saving
    for crops, coords in zip(crop_per_bbox, crop_coords_per_bbox):
        for crop, coord in zip(crops, coords):
            if crop.shape != (coord[0][1] - coord[0][0], coord[1][1] - coord[1][0]):
                raise ValueError("The crop and the coordinates don't match")

    json_info['save_path_crops'] = save_path_crops
    json_info['save_path_coords'] = save_path_coords

    save_json(json_info)

    number_digits_bbox = len(str(len(crop_per_bbox)))
    number_digits_crop = len(str(len(crop_per_bbox[0])))


    np.savez_compressed(save_path_coords, **{f"bbox_{str(i).zfill(number_digits_bbox)}": crop_coords for i, crop_coords in enumerate(crop_coords_per_bbox)})

    for i, crops in enumerate(crop_per_bbox):
        np.savez_compressed(save_path_crops.format(index=str(i).zfill(number_digits_bbox)), **{f"crop_{str(j).zfill(number_digits_crop)}": crop for j, crop in enumerate(crops)})

    print('Weight maps saved')

    return crop_per_bbox, crop_coords_per_bbox

def load_weight_maps(json_info):
    print('Loading weight maps')
    save_path_crops = json_info['save_path_crops']
    save_path_coords = json_info['save_path_coords']

    coords_per_bbox = np.load(save_path_coords)
    keys = sorted(coords_per_bbox.files)
    coords_per_bbox = [coords_per_bbox[key] for key in keys]

    weight_maps_per_bbox = []
    for i, coords in enumerate(coords_per_bbox):
        data = np.load(save_path_crops.format(index=i))
        keys = sorted(data.files)
        weight_maps = [data[key] for key in keys]
        weight_maps_per_bbox.append(weight_maps)

        # Check data integrity
        if len(coords) != len(weight_maps):
            raise ValueError("The number of weight maps and the number of coordinates don't match")
        for coord, weight_map in zip(coords, weight_maps):
            if weight_map.shape != (coord[0][1] - coord[0][0], coord[1][1] - coord[1][0]):
                print(weight_map.shape, (coord[0][1] - coord[0][0], coord[1][1] - coord[1][0]))
                raise ValueError("The weight map and the coordinates don't match")

    return coords_per_bbox, weight_maps_per_bbox


def prop_up_weight_maps(coords_per_bbox, weight_maps_per_bbox_crop, img_shape):
    print('Propping up weight maps')
    weight_maps_per_bbox = []
    empty_weight_map = np.zeros(img_shape)
    for coords, weight_maps_crop in tq(zip(coords_per_bbox, weight_maps_per_bbox_crop), desc='Propping up weight maps', total=len(weight_maps_per_bbox_crop)):
        weight_maps = [empty_weight_map.copy() for _ in range(len(weight_maps_crop))]
        for j, (coord, weight_map_crop) in enumerate(zip(coords, weight_maps_crop)):
            (min_x, max_x), (min_y, max_y) = coord
            weight_maps[j][min_x:max_x, min_y:max_y] = weight_map_crop
        weight_maps_per_bbox.append(weight_maps)

    weight_maps_per_bbox = [np.array(weight_maps) for weight_maps in weight_maps_per_bbox]
    return weight_maps_per_bbox

def save_result(dicts, length_middle_lines, json_info):

    path = json_info['path']
    experiment_name = json_info['experiment_name']
    if os.path.isfile(path):
        path = os.path.dirname(path)
    path = os.path.join(path, f"{experiment_name}_result")
    os.makedirs(path, exist_ok=True)
    path = os.path.join(path, f"{experiment_name}_results_bbox_")

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

def load_metadata(tiff_file):
    import PIL

    import tifffile
    with tifffile.TiffFile(tiff_file) as tif:
        metadata = tif.pages[0].tags
        x_resolution = metadata.get('XResolution')
        y_resolution = metadata.get('YResolution')

        physical_pixel_size_x_tifffile = 1 / x_resolution.value[0] if x_resolution else None
        physical_pixel_size_y_tifffile = 1 / y_resolution.value[0] if y_resolution else None

        import tifffile

    # Access the first page metadata
    description = tif.pages[0].tags.get('ImageDescription')
    if description:
        metadata_text = description.value
        
        # Example: Look for a frame rate keyword in the description
        if 'FrameRate' in metadata_text:
            # Extract frame rate value (assumes it's labeled 'FrameRate: value')
            frame_rate_tiffile = metadata_text.split('FrameRate: ')[1].split()[0]
        else:
            frame_rate_tiffile = None

    with PIL.Image.open(tiff_file) as img:
        dpi = img.info.get('dpi')
        x_dpi, y_dpi = dpi if dpi else (None, None)

        x_res = img.info.get('x_resolution')
        y_res = img.info.get('y_resolution')

        x_res, y_res = x_res if x_res else None, y_res if y_res else None
        
        # translate dpi to physical size

        physical_pixel_size_x_PIL_1 = 1 / x_res if x_res else None
        physical_pixel_size_y_PIL_1 = 1 / y_res if y_res else None

        # convert to mm
        x_dpi = x_dpi / 2.54
        y_dpi = y_dpi / 2.54

        physical_pixel_size_x_PIL_2 = 1 / x_dpi if x_dpi else None
        physical_pixel_size_y_PIL_2 =1 / y_dpi if y_dpi else None

        # Inspect all available metadata
        metadata = img.info
        # Check for frame rate in a relevant key
        frame_rate_PIL = metadata.get('FrameRate') if metadata.get('FrameRate') else metadata.get('frame_rate')
        frame_rate_PIL = frame_rate_PIL if frame_rate_PIL else None

    dict_metadata_pixel_size = {
        'pysical_pixel_size_tifffile': (physical_pixel_size_x_tifffile, physical_pixel_size_y_tifffile),
        'physical_pixel_size_PIL_1': (physical_pixel_size_x_PIL_1, physical_pixel_size_y_PIL_1),
        'physical_pixel_size_PIL_2': (physical_pixel_size_x_PIL_2, physical_pixel_size_y_PIL_2),
    }

    for token, (x, y) in dict_metadata_pixel_size.items():
        (x, y) = (x*10000, y*10000) if x and y else (None, None)
        dict_metadata_pixel_size[token] = (x, y)


    dict_metadata_fr = {
        'frame_rate_PIL': frame_rate_PIL,
        'frame_rate_tiffile': frame_rate_tiffile
    }

    for token, fr in dict_metadata_fr.items():
        fr = 1/fr if fr else None
        dict_metadata_fr[token] = fr

    return dict_metadata_pixel_size, dict_metadata_fr
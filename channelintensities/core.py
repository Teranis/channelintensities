from .GUI import plot_preview_lines, main_menu, ask_for_folder_file, ask_for_input, ask_for_another_round, ask_skip_frames, find_rotation, find_bboxs, ask_data_structure, show_my_info, two_img_preview
from .analysis import weight_maps_preview, generate_all_weight_maps, apply_weight_maps, calc_middle_lines_length
from .util import save_result, load_data, load_json, load_weight_maps, save_json, save_res_json
from .plotting import plot_master
import pandas as pd
import skimage.transform

def preprep_load_data():
    dim_order, tiff_dim, path = ask_data_structure()
    dim_order_required = ['channels', 'time', 'x', 'y']
    fl_channel = 'normal'
    if tiff_dim == 4:
        path_bf, path_fl = None, None
    else:
        path_bf, path_fl, path = None, None, None

    missing_dim = [dim for dim in dim_order_required if dim not in dim_order]
    if tiff_dim == 4:
        if path is None:
            path = ask_for_folder_file('TIFF file of the experiment', file_types=['*.tif', '*.tiff'],file_types_string='TIFF files',askopenfilename_toggle=True)
        if path is None:
            raise ValueError("No path selected")
        bf, fl = load_data(tiff_dim=tiff_dim, path=path, dim_order=dim_order, fl_channel=fl_channel)

    elif tiff_dim == 3:
        if missing_dim == ['channels']:
            path_bf = ask_for_folder_file('Brightfield TIFF file', file_types=['*.tif', '*.tiff'],file_types_string='TIFF files',askopenfilename_toggle=True)
            path_fl = ask_for_folder_file('Fluorescence TIFF file', file_types=['*.tif', '*.tiff'],file_types_string='TIFF files',askopenfilename_toggle=True)
            if path_bf is None or path_fl is None:
                raise ValueError("No path selected")
            bf, fl = load_data(tiff_dim=False, path_bf=path_bf, path_fl=path_fl, dim_order=dim_order, fl_channel=fl_channel)
            
        if missing_dim == ['time']:
            info_title = "Not so robust"
            info_text = "please put all TIFF files into one folder each\nThe program relies that the time points are in alphabetical order in the folder. So time point 0 has to be the first folder, time point 1 the second, and so on."
            show_my_info(info_title, info_text)
            path = ask_for_folder_file('TIFF file of the experiment', file_types=['*.tif', '*.tiff'],file_types_string='TIFF files',askopenfilename_toggle=True)
            if path is None:
                raise ValueError("No path selected")
            bf, fl = load_data(tiff_dim=False, dim_order=dim_order, fl_channel=fl_channel, path=path)
        else:
            raise ValueError("Invalid tiff dimension")

    elif tiff_dim == 2:
            info_title = "Not so robust"
            info_text = "please put all TIFF files for one channel into one folder each\nThe program relies that the time points are in alphabetical order in the folder. So time point 0 has to be the first folder, time point 1 the second, and so on."
            show_my_info(info_title, info_text)

            path_bf = ask_for_folder_file('Brightfield TIFF file folder')
            path_fl = ask_for_folder_file('Fluorescence TIFF file folder')
            if path_bf is None or path_fl is None:
                raise ValueError("No path selected")
            
            bf, fl = load_data(tiff_dim=False, path_bf=path_bf, path_fl=path_fl, dim_order=dim_order, fl_channel=fl_channel)
    else:
        raise ValueError("Invalid tiff dimension")
    

    if path is None:
        path = ask_for_folder_file('JSON save directory')


    switch_img1_img2, img_bad = two_img_preview(bf, fl)

    if img_bad:
        show_my_info("Bad images", "Please retry and check if you dimensions are correct.\nAlternatively contact the developer\nIt is also recommended to concat all in 4D, with order: [channels, time, x, y]")
        raise ValueError("Bad images")

    if switch_img1_img2:
        bf, fl = fl, bf
        fl_channel = 'switched'
    
    return bf, fl, path, path_bf, path_fl, dim_order, tiff_dim, fl_channel


def run_preprep():
    bf, fl, path, path_bf, path_fl, dim_order, tiff_dim, fl_channel = preprep_load_data()
    input_spec = [
    {
        "name": "Experiment Name",
        "type": str,
        "default": "new_experiment"
    }
    ]

    output = ask_for_input("Choose experiment name", input_spec)
    try:
        experiment_name = output['Experiment Name']
    except TypeError:
        print(output)
        raise ValueError("No experiment name selected")
    except KeyError:
        raise ValueError("No experiment name selected")
    

    last_angle = find_rotation(bf, fl)
    print('Angle:')
    print(last_angle)
    print()

    bf = [skimage.transform.rotate(img, last_angle) for img in bf]
    fl = [skimage.transform.rotate(img, last_angle) for img in fl]

    frames_to_skip = ask_skip_frames(bf, fl)

    bf = [bf[i] for i in range(len(bf)) if i not in frames_to_skip]
    fl = [fl[i] for i in range(len(fl)) if i not in frames_to_skip]
    
    print('Frames to skip:')
    print(frames_to_skip)
    bf = [bf[i] for i in range(len(bf)) if i not in frames_to_skip]
    fl = [fl[i] for i in range(len(fl)) if i not in frames_to_skip]

    bboxs = find_bboxs(bf, fl)

    print('bboxs:')
    bboxs_list = []
    for bbox in bboxs:
        bbox_points = []
        for point in bbox:
            bbox_points.append((point[0], point[1]))

        bboxs_list.append((bbox_points))
        print(bbox_points, sep='\n', end='\n\n')
    
    most_left_points = [min(bbox, key=lambda x: x[0]) for bbox in bboxs_list]
    bboxs_left_to_right = [bbox for _, bbox in sorted(zip(most_left_points, bboxs_list), key=lambda x: x[0][0])]

    json_info = {
        'experiment_name': experiment_name,
        'path': path,
        'angle': last_angle,
        'bboxs': bboxs_left_to_right,
        'frames_to_skip': frames_to_skip,
        'dim_order': dim_order,
        'fl_channel': fl_channel,
        'tiff_dim': tiff_dim,
        'path_fl': path_fl,
        'path_bf': path_bf,
    }

    save_json(json_info)

    json_info['bf'] = bf
    json_info['fl'] = fl

    return json_info

def main_func():
    (preprep_var, 
    box_preview_var, 
    weight_map_gen_var, 
    weight_map_display_var, 
    apply_weight_map_var,
    plot_var) = main_menu()

    if preprep_var == box_preview_var == weight_map_gen_var == weight_map_display_var == apply_weight_map_var == plot_var == False: 
        raise ValueError("No option selected! Please select at least one option!")

    if preprep_var:
        json_info = run_preprep()
    else:
        json_path = ask_for_folder_file('json file of the experiment', file_types=['*.json'], file_types_string='json files',askopenfilename_toggle=True)
        if json_path is None:
            raise ValueError("No json file selected")
        json_info = load_json(json_path)
        bf, fl = load_data(json_info=json_info)
        json_info['bf'] = bf
        json_info['fl'] = fl

    if json_info['bboxs'] == []:
        raise ValueError("No bounding boxes drawn!")

    img = json_info['bf'][0]
    img_shape = img.shape

    input_spec = []
    title = "Choose parameters for further"
    if box_preview_var:
        input_spec += [
        {
            "name": "Number of lines to display (preview)",
            "type": int,
            "default": 5
        }
        ]
        title += " Box Preview"
        if weight_map_gen_var:
            title += " and"
    if weight_map_gen_var:
        input_spec += [
        {
            "name": "Lines per pixel length",
            "type": float,
            "default": 1
        }
        ]
        title += " Weight Map Generation"

    if box_preview_var or weight_map_gen_var:
        output = ask_for_input(title, input_spec)

    if box_preview_var:
        weight_maps_preview(json_info, img_shape, num_lines=output['Number of lines to display (preview)'])

    if weight_map_gen_var:
        weight_maps_per_bbox, length_middle_lines = generate_all_weight_maps(json_info, 
                                                            img_shape, 
                                                            lines_per_pixel_length=output['Lines per pixel length'])
    
        json_info['Lines per pixel length'] = output['Lines per pixel length']
        save_json(json_info)
    elif weight_map_display_var or apply_weight_map_var:
        try:
            weight_maps_per_bbox = load_weight_maps(json_info['weight_maps_path'])
            length_middle_lines = calc_middle_lines_length(json_info['bboxs'])
        except KeyError:
            raise KeyError("No weight maps found! Please run weight map generation for the experiment name before applying them!")

    if weight_map_display_var:
        plot_preview_lines(weight_maps_per_bbox, json_info['bf'])

    if apply_weight_map_var:
        dicts = apply_weight_maps(weight_maps_per_bbox, json_info['fl'])
        dfs = save_result(dicts, length_middle_lines, json_info)

    if plot_var:

        input_spec = [
        {
            "name": "Length per pixel (um)",
            "type": float,
            "default": 1
        },
        {
            "name": "Seconds per frame",
            "type": float,
            "default": 2
        },
        {
            "name": "Number of rows",
            "type": int,
            "default": 6
        },
        ]
        #
        outputs = []
        if not apply_weight_map_var:
            continue_asking = True
            dfs = []
            while continue_asking == True:
                df_path = ask_for_folder_file('csv file of the experiment', file_types=['*.csv'], file_types_string='csv files', askopenfilename_toggle=True)

                if df_path is not None:
                    output = ask_for_input("Choose parameters for plotting", input_spec)
                    outputs.append(output)

                    input_spec[0]['default'] = output['Length per pixel (um)']
                    input_spec[1]['default'] = output['Seconds per frame']
                    input_spec[2]['default'] = output['Number of rows']
                
                dfs.append(pd.read_csv(df_path))

                continue_asking = ask_for_another_round("Continue", "Do you want to add another csv of another position?")

            if dfs == []:
                raise ValueError("No csv files selected!")

        else:
            for i, _ in enumerate(dfs):
                output = ask_for_input(f"Choose parameters for plotting {i}", input_spec)

                input_spec[0]['default'] = output['Length per pixel (um)']
                input_spec[1]['default'] = output['Seconds per frame']
                input_spec[2]['default'] = output['Number of rows']

                outputs.append(output)

        for i, df in enumerate(dfs):
            output = outputs[i]
            res_json = plot_master(df, output['Length per pixel (um)'], output['Seconds per frame'], output['Number of rows'])
            res_json['Lines per pixel length'] = json_info['Lines per pixel length']
            save_res_json(json_info['path'], json_info['experiment_name'], i, res_json)

    print("Done!")

if __name__ == "__main__":
    main_func()
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry import LineString
import itertools
import tqdm
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from .GUI import plot_weight_maps_preview
from .util import save_weight_maps

# @numba.jit(nopython=True, parallel=True)
def find_pixel_weights(img_shape, line_coords, line_index):
    # calculate the intersection length of the line with each pixel
    # and return the weights for each pixel
    rows, cols = img_shape
    (x_line_1, y_line_1), (x_line_2, y_line_2) = line_coords

    x_min = min(x_line_1, x_line_2)
    x_max = max(x_line_1, x_line_2)
    y_min = min(y_line_1, y_line_2)
    y_max = max(y_line_1, y_line_2)

    # Initialize an array to store lengths
    pixel_lengths = np.zeros((rows, cols))

    # Check if the line is within one pixel
    x_line_1_round = round(x_line_1, ndigits=0)
    y_line_1_round = round(y_line_1, ndigits=0)
    bbox_1 = [x_line_1_round-0.5, x_line_1_round+0.5, y_line_1_round-0.5, y_line_1_round+0.5]
    if bbox_1[0] <= x_line_2 <= bbox_1[1] and bbox_1[2] <= y_line_2 <= bbox_1[3]:
        # Line is within one pixel
        i, j = int(x_line_1_round), int(y_line_1_round)
        pixel_lengths[i, j] = np.sqrt((x_line_2 - x_line_1)**2 + (y_line_2 - y_line_1)**2)

    # Iterate over each pixel
    for i in range(int(y_min) - 2, int(y_max) + 3, 1):
        for j in range(int(x_min) - 2, int(x_max) + 3, 1):
            # Pixel boundaries
            binding_x = [j-0.5, j+0.5]
            binding_y = [i-0.5, i+0.5]                  
            
            # Collect intersection points with pixel edges
            intersections = []

            for x_pix in binding_x:
                # from parametric equation of a line x = x1 + t(x2 - x1) and t in [0, 1] (all possible xs)
                # --> t = (x - x1) / (x2 - x1)
                # None if vertical line
                if x_line_2 != x_line_1:    
                    t = (x_pix - x_line_1) / (x_line_2 - x_line_1)
                    if 0 <= t <= 1: # see if the intersection is not outside the line
                        y = y_line_1 + t * (y_line_2 - y_line_1) # get the y coordinate of the possible intersection
                        if binding_y[0] <= y <= binding_y[1]: # check if y is within the pixel
                            intersections.append((x_pix, y)) # add the intersection to the list

            for y_pix in binding_y:
                # from parametric equation of a line y = y1 + t(y2 - y1) and t in [0, 1] (all possible ys)
                # --> t = (y - y1) / (y2 - y1)
                # None if horizontal line
                if y_line_2 != y_line_1: 
                    t = (y_pix - y_line_1) / (y_line_2 - y_line_1)
                    if 0 <= t <= 1: # see if the intersection is not outside the line
                        x = x_line_1 + t * (x_line_2 - x_line_1) # get the x coordinate of the possible intersection
                        if binding_x[0] <= x <= binding_x[1]: # check if x is within the pixel
                            intersections.append((x, y_pix)) # add the intersection to the list

            # Calculate the segment length within the pixel
            if len(intersections) == 2:
                (x1, y1), (x2, y2) = intersections
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                pixel_lengths[i, j] = length

            elif len(intersections) == 1:
                (x1, y1) = intersections[0]

                for endpoints in [(x_line_1, y_line_1), (x_line_2, y_line_2)]:
                    if binding_x[0] <= endpoints[0] <= binding_x[1] and binding_y[0] <= endpoints[1] <= binding_y[1]:
                        length = np.sqrt((endpoints[0] - x1)**2 + (endpoints[1] - y1)**2)
                        pixel_lengths[i, j] = length
            
            elif len(intersections) > 2:
                # print("More than 2 intersections found.")
                # print("Intersections:", intersections)
                doubles = []
                for intersection in intersections:
                    if intersections.count(intersection) > 1:
                        doubles.append(intersection)
                # print("Doubles:", doubles)

                intersections = list(set(intersections))

                if len(intersections) == 2:
                    (x1, y1), (x2, y2) = intersections
                    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    pixel_lengths[i, j] = length
                
                else:
                    raise ValueError("More than 2 unique intersections found.")
                
    return pixel_lengths, line_index

def sort_points_and_get_edge_lines(bbox):
    sorted_points = sorted(bbox, key=lambda x: x[1])

    bottom_points = sorted_points[0:2]
    top_points = sorted_points[2:4]

    sorted_top_points = sorted(top_points, key=lambda x: x[0])
    sorted_bottom_points = sorted(bottom_points, key=lambda x: x[0])

    top_left = sorted_top_points[0]
    top_right = sorted_top_points[1]
    buttom_left = sorted_bottom_points[0]
    buttom_right = sorted_bottom_points[1]
    
    edge_line_1 = (buttom_left, top_left)
    edge_line_2 = (buttom_right, top_right)

    middle_point_top = ((top_left[0] + top_right[0]) / 2, (top_left[1] + top_right[1]) / 2)
    middle_point_bottom = ((buttom_left[0] + buttom_right[0]) / 2, (buttom_left[1] + buttom_right[1]) / 2)
    middle_line = (middle_point_top, middle_point_bottom)
    length_middle_line = np.linalg.norm(np.array(middle_line[1]) - np.array(middle_line[0]))

    return middle_line, length_middle_line, edge_line_1, edge_line_2

def generate_lines(bbox, normal_lines_num=None, lines_per_pixel_length=None, return_edge_lines=False):
    # usual value lines_per_pixel_length = 3
    if normal_lines_num is None and lines_per_pixel_length is None:
        raise ValueError("Either normal_lines_num or lines_per_pixel_length must be specified.")
    if normal_lines_num is not None and lines_per_pixel_length is not None:
        raise ValueError("Only one of normal_lines_num or lines_per_pixel_length can be specified.")

    # Ensure all points are unique
    if len(set(bbox)) != 4:
        raise ValueError("Bounding box points must be unique.")
    
    if not Polygon(bbox).is_valid:
        raise ValueError("Bounding box points must form a valid polygon.")
    
    # sort points so edge_line_1 and edge_line_2 both go from buttom to top

    _, length_middle_line, edge_line_1, edge_line_2 = sort_points_and_get_edge_lines(bbox)

    if normal_lines_num is None:
        normal_lines_num = int(length_middle_line * lines_per_pixel_length)


    # xs_side_1 = np.linspace(buttom_left[0], top_left[0], num=normal_lines_num)
    # ys_side_1 = np.linspace(buttom_left[1], top_left[1], num=normal_lines_num)

    # xs_side_2 = np.linspace(buttom_right[0], top_right[0], num=normal_lines_num)
    # ys_side_2 = np.linspace(buttom_right[1], top_right[1], num=normal_lines_num)

    xs_side_1 = np.linspace(edge_line_1[0][0], edge_line_1[1][0], num=normal_lines_num)
    ys_side_1 = np.linspace(edge_line_1[0][1], edge_line_1[1][1], num=normal_lines_num)

    xs_side_2 = np.linspace(edge_line_2[0][0], edge_line_2[1][0], num=normal_lines_num)
    ys_side_2 = np.linspace(edge_line_2[0][1], edge_line_2[1][1], num=normal_lines_num)

    lines = []
    for i in range(normal_lines_num):
        lines.append(((xs_side_1[i], ys_side_1[i]), (xs_side_2[i], ys_side_2[i])))

    # check if any lines overlap with each other or the edge lines
    iterations = itertools.combinations(lines, 2)
    for combo in iterations:
        line_1 = LineString(combo[0])
        line_2 = LineString(combo[1])
        if line_1.intersects(line_2):
            raise ValueError("Lines must not intersect.")
        
    if return_edge_lines:
        return lines, (edge_line_1, edge_line_2)
    
    return lines, length_middle_line

def generate_weights_for_lines(lines, img_shape):
    weight_maps = [np.zeros(img_shape) for _ in range(len(lines))]

    def pipeline(line_index):
        return find_pixel_weights(img_shape, lines[line_index], line_index)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(pipeline, line_index) for line_index in range(len(lines))]
        for future in concurrent.futures.as_completed(futures):
            pixel_weights, line_index = future.result()
            weight_maps[line_index] = pixel_weights

    return weight_maps

def generate_weight_maps(bboxs, img_shape, lines_per_pixel_length=None, return_lines=False, num_lines=None):
    weight_maps_per_bbox = []
    if not return_lines:
        length_middle_lines = []

    for bbox in tqdm.tqdm(bboxs, desc="Generating Weight Maps Per Bounding Box", total=len(bboxs)):
        if return_lines:
            lines, edge_lines = generate_lines(bbox, lines_per_pixel_length=lines_per_pixel_length, normal_lines_num=num_lines, return_edge_lines=return_lines)
        else:
            lines, length_middle_line = generate_lines(bbox, lines_per_pixel_length=lines_per_pixel_length, normal_lines_num=num_lines, return_edge_lines=return_lines)

        # start_time = time.time()
        weight_maps = generate_weights_for_lines(lines, img_shape)
        # end_time = time.time()
        # print("Time to generate weight maps:", end_time - start_time)

        if return_lines:
            weight_maps_per_bbox.append((weight_maps, lines, edge_lines))
        else:
            weight_maps_per_bbox.append(weight_maps)
            length_middle_lines.append(length_middle_line)

    if not return_lines:
        return weight_maps_per_bbox, length_middle_lines
    else:
        return weight_maps_per_bbox

def weight_maps_preview(json_info, img_shape, lines_per_pixel_length=None, num_lines=None):
    bboxs = json_info['bboxs']
    bf = json_info['bf']
    fl = json_info['fl']
    weight_maps_and_lines = generate_weight_maps(bboxs, img_shape, lines_per_pixel_length=lines_per_pixel_length, return_lines=True, num_lines=num_lines)
    plot_weight_maps_preview(weight_maps_and_lines, bf, fl, pixel_size=json_info['length_per_pixel'])

def get_most_left_point(bbox):
    return min(bbox, key=lambda x: x[0])

def generate_all_weight_maps(json_info, img_shape, lines_per_pixel_length=None, num_lines=None):
    print('Generating all weight maps...')

    bboxs = json_info['bboxs']
    weight_maps_per_bbox, length_middle_lines = generate_weight_maps(bboxs, img_shape, lines_per_pixel_length=lines_per_pixel_length, num_lines=num_lines)

    # oops the image is kind of displayed upside down soo....
    for weight_maps in weight_maps_per_bbox:
        weight_maps.reverse()        

    weight_maps_per_bbox = [np.array(weight_maps) for weight_maps in weight_maps_per_bbox]
    crop_per_bbox, crop_coords_per_bbox = save_weight_maps(weight_maps_per_bbox, json_info)

    return crop_per_bbox, crop_coords_per_bbox, length_middle_lines, weight_maps_per_bbox

# def prepare_weight_maps_per_bbox(weight_maps, bbox_index):
#     weight_maps_sums = []
#     cutout_for_weight_maps = []
#     for weight_map in weight_maps:
#         non_zero_indices = np.nonzero(weight_map)

#         min_y, max_y = np.min(non_zero_indices[0]), np.max(non_zero_indices[0])
#         min_x, max_x = np.min(non_zero_indices[1]), np.max(non_zero_indices[1])
#         cutout = (min_y-1, max_y+2, min_x-1, max_x+2)

#         weight_maps_sums.append(np.sum(weight_map[cutout[0]:cutout[1], cutout[2]:cutout[3]]))

#         cutout_for_weight_maps.append(cutout)

#     return weight_maps_sums, cutout_for_weight_maps, bbox_index

def prepare_weight_maps(crop_per_bbox):

    weight_maps_sums_per_bbox = np.sum(crop_per_bbox, axis=(1, 2))

    # with ThreadPoolExecutor() as executor:
    #     futures = [executor.submit(prepare_weight_maps_per_bbox, weight_maps, bbox_index) for bbox_index, weight_maps in enumerate(weight_maps_per_bbox)]
    #     for future in concurrent.futures.as_completed(futures):
    #         weight_maps_sums, cutout_for_weight_maps, bbox_index = future.result()
    #         weight_maps_sums_per_bbox.append(weight_maps_sums)
    #         cutout_for_weight_maps_per_bbox.append(cutout_for_weight_maps)
    #         bbox_indexes.append(bbox_index)

    # sorted_output = sorted(zip(weight_maps_sums_per_bbox, cutout_for_weight_maps_per_bbox, bbox_indexes), key=lambda x: x[2])
    # weight_maps_sums_per_bbox, cutout_for_weight_maps_per_bbox, bbox_indexes = zip(*sorted_output)
    return weight_maps_sums_per_bbox#, crop_per_bbox

def apply_weight_maps(crop_per_bbox, crop_coords_per_bbox, fl):
    dicts = []
    # weight_maps_sums_per_bbox, cutout_for_weight_maps_per_bbox = prepare_weight_maps(crop_per_bbox)

    i = 0
    for bbox_crops_weight_map, bbox_coords_cutout in tqdm.tqdm(zip(crop_per_bbox, crop_coords_per_bbox), desc="Applying Weight Maps Per Bounding Box", total=len(crop_per_bbox)):
        dict_loc = {}
        cutouts_for_weight_maps = [i]
        weight_maps_totals = [np.sum(weight_map) for weight_map in bbox_crops_weight_map]
            
        frame_index = 0
        for frame in tqdm.tqdm(fl, desc="Applying Weight Maps Per Frame", total=len(fl)):
            output = []
            for crop_weight_map, weight_map_total, coords in zip(bbox_crops_weight_map, weight_maps_totals, bbox_coords_cutout):
                if weight_map_total == 0:
                    output.append(0)
                else:
                    (min_y, max_y), (min_x, max_x)  = coords
                    frame_cutout = frame[min_y:max_y, min_x:max_x]
                    output.append(np.sum(frame_cutout*crop_weight_map)/weight_map_total)
            dict_loc[frame_index] = output
            frame_index += 1
        dicts.append(dict_loc)
        i += 1

    return dicts

def calc_middle_lines_length(bboxs):

    middle_lines_lengths = []
    for bbox in bboxs:
        _, length_middle_line, _, _ = sort_points_and_get_edge_lines(bbox)
        middle_lines_lengths.append(length_middle_line)
    
    return middle_lines_lengths

import skimage
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from matplotlib.transforms import IdentityTransform
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import Polygon
import tkinter as tk
from tkinter import filedialog, messagebox, StringVar
from tkinter import ttk

import os
from itertools import permutations


def create_window_with_buttons(title, content_frame_func):
    """
    Create a Tkinter window with common functionality (title, Submit/Cancel buttons).
    
    Args:
        title (str): Title of the window.
        content_frame_func (function): A function that adds custom widgets to the window.

    Returns:
        The value returned by the content_frame_func after interaction.
    """
    # Create the main window
    root = tk.Tk()
    root.title(title)
    
    # Create a frame for the main content
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    title_label = ttk.Label(frame, text=title)
    title_label.pack(pady=10)
    
    # Variable to track if the dialog was canceled
    canceled = True
    
    # Add content using the provided function
    result = None
    def content_frame_callback():
        nonlocal result
        result = content_frame_func(frame)

    content_frame_callback()
    
    # Function to close the dialog with a canceled flag
    def cancel():
        root.quit()
        root.destroy()
        nonlocal canceled
        canceled = True

    # Function to close the dialog with a submitted flag
    def submit():
        root.quit()
        root.destroy()
        nonlocal canceled
        canceled = False
    
    # Buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=10)

    # Buttons inside the frame
    submit_button = ttk.Button(button_frame, text="Done", command=submit)
    submit_button.pack(side=tk.LEFT, padx=5)

    cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel)
    cancel_button.pack(side=tk.LEFT, padx=5)

    # Run the Tkinter event loop
    root.protocol("WM_DELETE_WINDOW", cancel)
    root.mainloop()
    
    return None if canceled else result

def find_rotation(bf, fl):

    last_angle = 0
    last_index = 0

    # Create the main window
    root = tk.Tk()
    root.title("Right click to get straight line, make sure the orientation of the diffusion/flow is from button to top, close window to use selected angle")

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)

    fig.suptitle('Make sure the orientation of the diffusion/flow is from button to top\nclose window to use selected angle')

    # Plot the data
    image1 = ax1.imshow(bf[0], cmap='gray')
    ax1.set_title('Bright field')

    image2 = ax2.imshow(fl[0], cmap='gray')
    ax2.set_title('Fluroscence')
    # Create a canvas to display the plot

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # Initialize a variable to store the line object
    vertical_line_1 = None
    vertical_line_2 = None

    def on_done():
        root.quit()  
        root.destroy()
        
    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    def onclick(event):
        nonlocal vertical_line_1, vertical_line_2

        if toolbar.mode != '':
            return
        
        if event.inaxes == ax1 or ax2:
            # Remove the previous line if it exists
            if vertical_line_1 is not None:
                vertical_line_1.remove()
                vertical_line_2.remove()
            # Draw a new vertical line
            x_coord_line = event.xdata
            vertical_line_1 = ax1.axvline(x=x_coord_line, color='r', linestyle='--')
            vertical_line_2 = ax2.axvline(x=x_coord_line, color='r', linestyle='--')
            fig.canvas.draw_idle()

    # Connect the click event
    fig.canvas.mpl_connect('button_press_event', onclick)

    def update_plot(val):
        nonlocal last_angle, last_index
        idx = int(scrollbar.get())
        angle = float(val)
        rotated_image1 = skimage.transform.rotate(bf[idx], angle)
        rotated_image2 = skimage.transform.rotate(fl[idx], angle)
        image1.set_data(rotated_image1)
        image2.set_data(rotated_image2)
        fig.canvas.draw_idle()
        last_angle = angle
        last_index = idx

    # Add a scrollbar for time points
    scrollbar = tk.Scale(root, from_=0, to=len(bf)-1, orient=tk.HORIZONTAL, command=lambda val: update_plot(angle_scale.get()))
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Add a scale for rotation angle
    angle_scale = tk.Scale(root, from_=-180, to=180, orient=tk.HORIZONTAL, label="Rotation Angle", command=update_plot, resolution=90)
    angle_scale.pack(side=tk.BOTTOM, fill=tk.X)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()

    plt.close(fig)

    return last_angle

def ask_skip_frames(bf, fl):
    print('Note: only chose frames in the beginning or at the end')
    del_frames = []

    # Create the main window
    root = tk.Tk()
    root.title("Check if frames should be skipped\nNote: only chose frames in the beginning or at the end")

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)
    fig.suptitle('Check if frames should be skipped\nNote: only chose frames in the beginning or at the end')

    # Plot the data
    image1 = ax1.imshow(bf[0], cmap='gray')
    ax1.set_title('Bright field')

    image2 = ax2.imshow(fl[0], cmap='gray')
    ax2.set_title('Fluroscence')

    bf_disp, fl_disp = bf.copy(), fl.copy()

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    def on_done():
        root.quit()
        root.destroy()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    def update_plot(val):

        idx = int(val)
        image1.set_data(bf_disp[idx])
        image2.set_data(fl_disp[idx])
        fig.canvas.draw_idle()

    # Add a scrollbar for time points
    scrollbar = tk.Scale(root, from_=0, to=len(bf_disp)-1, orient=tk.HORIZONTAL, command=update_plot)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Entry widget to input frame indices to delete
    def on_entry_change():
        nonlocal del_frames, bf, fl, bf_disp, fl_disp
        frame_indexes = entry.get().split(',')
        del_frames = [int(idx.strip()) for idx in frame_indexes]
        print(f"Frames to skip: {del_frames}")

        new_max = len(bf) - len(del_frames) - 1
        scrollbar.config(to=new_max)
        if scrollbar.get() > new_max:
            scrollbar.set(new_max)

        bf_disp = [bf[i] for i in range(len(bf)) if i not in del_frames]
        fl_disp = [fl[i] for i in range(len(fl)) if i not in del_frames]

        update_plot(scrollbar.get())

    entry = tk.Entry(root)
    entry.pack(side=tk.BOTTOM, pady=10)
    entry.bind('<Return>', lambda e: on_entry_change())

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()

    plt.close(fig)

    return del_frames

def find_bboxs(bf, fl):
    # Create the main window
    root = tk.Tk()
    root.title("Right click to add corner of bbox, left click to delete, close window to use selected bboxs")

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)

    fig.suptitle('Right click to add corner of bbox\nleft click to delete\nclose window to use selected bboxs')

    # Plot the data
    image1 = ax1.imshow(bf[0], cmap='gray')
    ax1.set_title('Bright field')

    image2 = ax2.imshow(fl[0], cmap='gray')
    ax2.set_title('Fluorescence')

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    
    def on_done():
        root.quit()
        root.destroy()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    # Initialize variables for onclick
    points_coords = []
    drawn_points = []
    drawn_bboxs = []

    def onclick(event):
        nonlocal points_coords, drawn_points, drawn_bboxs
        if event.inaxes != ax1 and event.inaxes != ax2:
            return
        
        if toolbar.mode != '':
            return

        if event.button == 1:
            points_coords.append((event.xdata, event.ydata))
            point1 = ax1.plot(event.xdata, event.ydata, 'ro')[0]
            point2 = ax2.plot(event.xdata, event.ydata, 'ro')[0]
            drawn_points.append((point1, point2))

            if len(points_coords) % 4 == 0:
                bbox = points_coords[-4:]
                rect1 = Polygon(bbox, closed=True, linewidth=1, edgecolor='r', facecolor='none')
                ax1.add_patch(rect1)
                rect2 = Polygon(bbox, closed=True, linewidth=1, edgecolor='r', facecolor='none')
                ax2.add_patch(rect2)
                drawn_bboxs.append((rect1, rect2))

        elif event.button == 3:
            if len(points_coords) == 0:
                return

            if len(points_coords) % 4 == 0 and len(drawn_bboxs) > 0:
                [bbox.remove() for bbox in drawn_bboxs[-1]]
                drawn_bboxs = drawn_bboxs[:-1]

            [point.remove() for point in drawn_points[-1]]
            drawn_points = drawn_points[:-1]
            points_coords = points_coords[:-1]

        fig.canvas.draw_idle()

    # Connect the click event
    fig.canvas.mpl_connect('button_press_event', onclick)

    def update_plot(val):
        idx = int(val)
        image1.set_data(bf[idx])
        image2.set_data(fl[idx])
        fig.canvas.draw_idle()

    # Add a scrollbar for time points
    scrollbar = tk.Scale(root, from_=0, to=len(bf)-1, orient=tk.HORIZONTAL, command=update_plot)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()

    plt.close(fig)
    bboxs = [bbox_pair[0].get_xy()[:4] for bbox_pair in drawn_bboxs]

    return bboxs

###########

def plot_weight_maps_preview(weight_maps_per_bbox, bf, fl, pixel_size):
    root = tk.Tk()
    root.title("Binding box Preview")

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)

    fig.suptitle("Binding box Preview", position=(0.5, 0.88))

    # Plot the data
    image1 = ax1.imshow(bf[0], cmap='gray')
    ax1.set_title('Bright field')

    image2 = ax2.imshow(fl[0], cmap='gray')
    ax2.set_title('Fluorescence')

    scale_bar_length = 100  # 10 micrometers

    # Calculate scale bar length in pixels
    scale_bar_length_pixels = scale_bar_length / pixel_size

    scalebar1 = AnchoredSizeBar(
        ax1.transData,                  # Use data coordinates
        scale_bar_length_pixels,       # Length of scale bar in pixels
        f'{scale_bar_length} µm',      # Scale bar label
        'upper right',                 # Location of the scale bar
        pad=0.5,
        color='white',
        frameon=False,
        size_vertical=2                # Thickness of the scale bar
        )

    scalebar2 = AnchoredSizeBar(
        ax2.transData,                  # Use data coordinates
        scale_bar_length_pixels,       # Length of scale bar in pixels
        f'{scale_bar_length} µm',      # Scale bar label
        'upper right',                 # Location of the scale bar
        pad=0.5,
        color='white',
        frameon=False,
        size_vertical=2                # Thickness of the scale bar
        )

    ax1.add_artist(scalebar1)
    ax2.add_artist(scalebar2)

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    def on_done():
        root.quit()
        root.destroy()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)
    
    ax1.grid(True)
    ax2.grid(True)
    for weight_maps, lines, edge_lines in weight_maps_per_bbox:
        for weight_map in weight_maps:
            weight_map = np.where(weight_map == 0, np.nan, weight_map)
            ax1.imshow(weight_map, cmap='viridis', alpha=0.5)
            ax2.imshow(weight_map, cmap='viridis', alpha=0.5)
            for line in lines:
                ax1.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='red')
                ax2.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='red')
            for line in edge_lines:
                ax1.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='blue')
                ax2.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='blue')

    def update_plot(val):
        idx = int(val)
        image1.set_data(bf[idx])
        image2.set_data(fl[idx])
        fig.canvas.draw_idle()

    # Add a scrollbar for time points
    scrollbar = tk.Scale(root, from_=0, to=len(bf)-1, orient=tk.HORIZONTAL, command=update_plot)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()

    plt.close(fig)

def plot_preview_lines(weight_maps_per_box, crops_per_bbox, crop_coords_per_bbox, bf):
    # weight_maps_per_box = [np.where(bboxs == 0, np.nan, bboxs) for bboxs in weight_maps_per_bbox]

    root = tk.Tk()
    root.title('Preview Weight Maps')

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2)

    fig.suptitle('Preview Weight Maps')

    # Plot the data
    image1 = ax1.imshow(bf[0], cmap='gray')
    ax1.set_title('Bright field')

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    def on_done():
        root.quit()
        root.destroy()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)
    
    ax1.grid(True)
    ax2.grid(True)

    weight_map = weight_maps_per_box[0][0]

    coords = crop_coords_per_bbox[0][0]
    x_min, x_max = coords[1]
    y_min, y_max = coords[0]
    crop = weight_map[y_min:y_max, x_min:x_max]

    wp1 = ax1.imshow(weight_map, cmap='viridis', alpha=0.5)
    wp2 = ax2.imshow(crop, cmap='viridis', alpha=0.5)

    def update_plot(val):
        nonlocal wp2

        idx = int(scrollbar.get())
        idx_wp = int(val)

        new_max = len(weight_maps_per_box[idx])-1
        wp_scale.config(to=new_max)  

        if idx_wp > new_max:
            wp_scale.set(new_max)
            idx_wp = new_max

        # image1.set_data(bf[idx])
        # image2.set_data(fl[idx])
        weight_map = weight_maps_per_box[idx][idx_wp]
        crop_per_bbox = crops_per_bbox[idx][idx_wp]

        wp1.set_data(weight_map)
        wp2.remove()
        wp2 = ax2.imshow(crop_per_bbox, cmap='viridis', alpha=0.5)

        fig.canvas.draw_idle()

    # Add a scrollbar for selecting bbox
    scrollbar = tk.Scale(root, from_=0, to=len(weight_maps_per_box)-1, orient=tk.HORIZONTAL, label='bbox', command=lambda val: update_plot(wp_scale.get()))
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Add a scale for selecting specific line
    wp_scale = tk.Scale(root, from_=0, to=len(weight_maps_per_box[0])-1, orient=tk.HORIZONTAL, label="displayed weight map", command=update_plot, resolution=1)
    wp_scale.pack(side=tk.BOTTOM, fill=tk.X)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()
    plt.close(fig)

def main_menu():
    """
    Creates and displays the main menu GUI for selecting various options.
    The main menu includes check buttons for the following options:
    - Preprep
    - Bbox preview
    - Generate weight maps
    - Weight maps preview
    - Apply weight maps
    - Plot Data
    The selected options are displayed in a label and updated dynamically as the user interacts with the check buttons.
    Returns:
        tuple: A tuple containing the state (0 or 1) of each check button in the following order:
            (preprep_var, box_preview_var, weight_map_gen_var, weight_map_preview_var, apply_waight_map_var, plotting_var)
    """
    def show_selected():

        selected_options = []
        if preprep_var.get():
            selected_options.append("Preprep")
        if box_preview_var.get():
            selected_options.append("Bbox preview")
        if weight_map_gen_var.get():
            selected_options.append("Generate weight maps")
        if weight_map_preview_var.get():
            selected_options.append("Weight maps preview")
        if apply_waight_map_var.get():
            selected_options.append("Apply weight maps")
        if plotting_var.get():
            selected_options.append('Plot Data')
        
        selected_text = "\n".join(selected_options) if selected_options else "None"
        result_label.config(text=f"Selected:\n{selected_text}")
    # Create the main application window
    root = tk.Tk()
    root.title("Main Menu")
    def on_done():
        root.quit()
        root.destroy()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    # Create variables to track the state of check buttons
    preprep_var = tk.IntVar()
    box_preview_var = tk.IntVar()
    weight_map_gen_var = tk.IntVar()
    weight_map_preview_var = tk.IntVar()
    apply_waight_map_var = tk.IntVar()
    plotting_var = tk.IntVar()

    # Create check buttons with text
    preprep = tk.Checkbutton(root, text="Preprep", variable=preprep_var, command=show_selected)
    preprep.pack(anchor="w", padx=20, pady=5)

    box_preview = tk.Checkbutton(root, text="Bbox preview", variable=box_preview_var, command=show_selected)
    box_preview.pack(anchor="w", padx=20, pady=5)

    weight_map_gen = tk.Checkbutton(root, text="Generate weight maps", variable=weight_map_gen_var, command=show_selected)
    weight_map_gen.pack(anchor="w", padx=20, pady=5)

    weight_map_preview = tk.Checkbutton(root, text="Weight maps preview", variable=weight_map_preview_var, command=show_selected)
    weight_map_preview.pack(anchor="w", padx=20, pady=5)

    apply_waight_map = tk.Checkbutton(root, text="Apply weight maps", variable=apply_waight_map_var, command=show_selected)
    apply_waight_map.pack(anchor="w", padx=20, pady=5)

    apply_waight_map = tk.Checkbutton(root, text="Plot Data", variable=plotting_var, command=show_selected)
    apply_waight_map.pack(anchor="w", padx=20, pady=5)

    # Label to display selected options
    result_label = tk.Label(root, text="Selected: None")
    result_label.pack(pady=20)
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()

    return preprep_var.get(), box_preview_var.get(), weight_map_gen_var.get(), weight_map_preview_var.get(), apply_waight_map_var.get(), plotting_var.get()

def ask_for_folder_file(title, initialdir=None, askopenfilename_toggle=False, file_types=None, file_types_string=None):   
    """
    Opens a dialog to ask the user to select a folder or file.
    Parameters:
    title (str): The title of the dialog window.
    initialdir (str, optional): The initial directory that the dialog will open in. Defaults to None.
    askopenfilename_toggle (bool, optional): If True, the dialog will ask for a file instead of a directory. Defaults to False.
    file_types (list, optional): A list of file types/extensions to filter by when asking for a file. Defaults to None.
    file_types_string (str, optional): A description of the file types. Defaults to None.
    Returns:
    str: The absolute path of the selected folder or file, or None if the user cancels the dialog.
    """
    output_path = None
    canceled = False

    if askopenfilename_toggle and file_types is not None:
        file_types_ending = [file_type.replace("*", "") for file_type in file_types]
        file_types=[(f"{file_types_string}", ' '.join(file_types)), ("All Files", "*.*")]

    else:
        file_types_ending = None

    def select_folder():
        nonlocal output_path, askopenfilename_toggle,title, initialdir,file_types
        if askopenfilename_toggle:
            output_path = filedialog.askopenfilename(title=title, 
                                                     initialdir=initialdir, 
                                                     filetypes=file_types)
        else:
            output_path = filedialog.askdirectory(title=title, initialdir=initialdir)
        
        if output_path:
            if askopenfilename_toggle and file_types:
                file_ending = os.path.splitext(output_path)[1]
                if file_ending not in file_types_ending:
                    messagebox.showwarning("Invalid file type", f"Invalid file type! Please select a file with the following extensions: {file_types_ending}")
                    return None
            output_path = os.path.abspath(output_path)
            root.quit() 
            root.destroy()
            return output_path
        else:  # If the user cancels or closes the dialog
            messagebox.showwarning("No Selection", "No directory was selected!")
        return None

    def cancel():
        nonlocal canceled
        canceled = True
        root.quit()
        root.destroy()
        return None

    # Create the main application window
    root = tk.Tk()
    root.title(title)

    # Create a button to open the folder selection dialog
    if askopenfilename_toggle:
        select_button = ttk.Button(root, text=f'Select a file for {title}', command=select_folder)
    else:
        select_button = ttk.Button(root, text=f'Select a folder for {title}', command=select_folder)
    select_button.pack(pady=20)

    cancel_button = ttk.Button(root, text="Cancel", command=cancel)
    cancel_button.pack(pady=20)

    # Start the main loop
    root.protocol("WM_DELETE_WINDOW", cancel)
    root.mainloop()

    if output_path is not None:
        output_path = os.path.abspath(output_path)
    
    if canceled:
        return None
    
    return output_path

def ask_for_input(title, input_specs):
    """
    Creates a form with dynamic inputs and returns user input or None if canceled.

    Args:
        title (str): The title of the window.
        input_specs (list): A list of dictionaries specifying input fields.
            Each dict should have "name", "type", and "default".

    Returns:
        dict: A dictionary of user inputs or None if the dialog was canceled.
    """
    def input_form(frame):
        """
        Populate the frame with labels and entry widgets based on input_specs.
        """
        user_inputs = {}
        entries = []

        def get_result():
            """
            Collect and validate inputs from the form.
            """
            for spec, entry in zip(input_specs, entries):
                input_name = spec["name"]
                input_type = spec["type"]
                raw_value = entry.get()

                if raw_value == "":  # Handle blank inputs with a warning
                    messagebox.showwarning("Invalid input", f"Input for {input_name} is blank!")
                    return None
                else:
                    try:
                        user_inputs[input_name] = input_type(raw_value)
                    except ValueError:
                        messagebox.showwarning("Invalid input", f"Invalid input for {input_name}! Please enter a valid {input_type.__name__}.")
                        return None
            return user_inputs

        # Create labels and entry widgets dynamically
        for spec in input_specs:
            input_name = spec["name"]
            default_value = spec["default"]

            label = ttk.Label(frame, text=f"{input_name} (default: {default_value})")
            label.pack(pady=5)

            entry = ttk.Entry(frame)
            entry.insert(0, str(default_value))
            entry.pack(pady=5)

            entries.append(entry)

        return get_result

    # Use the generic create_window_with_buttons to handle the common logic
    def wrapper(frame):
        get_result = input_form(frame)
        return get_result()

    # Collect the results
    result = create_window_with_buttons(title, wrapper)
    return result

def ask_for_another_round(question_title, question_text):
    """
    Display a message box with a yes/no question and return the user's response.
    Parameters:
    question_title (str): The title of the message box.
    question_text (str): The text of the question to be displayed in the message box.
    Returns:
    bool: True if the user clicks 'Yes', False if the user clicks 'No'.
    """
    response = None
    def ask_yes_no():
        nonlocal question_title, question_text, response
        response = messagebox.askyesno(question_title, question_text)
        root.quit()
        root.destroy()

    # Create the main window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Call the function to show the message box
    ask_yes_no()
    return response

def show_my_info(info_title, info_text):
    """
    Displays an informational message box with the given title and text.
    Args:
        info_title (str): The title of the information message box.
        info_text (str): The text content of the information message box.
    Returns:
        None
    """
    def show_info():
        nonlocal info_title, info_text
        messagebox.showinfo(info_title, info_text)

    # Create the main window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Call the function to show the info window
    show_info()

def drop_down_menu(title, options):
    """
    Create a dropdown menu window and return the selected option.

    Args:
        title (str): Title of the window.
        options (list): Options for the dropdown menu.

    Returns:
        str: The selected option, or None if canceled.
    """
    options = ['Select option'] + options
    def dropdown_content(frame):
        # Create the dropdown menu and its supporting widgets
        
        selected_value = StringVar()
        selected_value.set(options[0])  # Default selection
        
        dropdown = ttk.OptionMenu(frame, selected_value, *options)
        dropdown.pack(pady=20)
        
        return selected_value  # Pass selected_value back for retrieval
    
    # Use the generic window creator function
    result = create_window_with_buttons(title, dropdown_content)
    return None if result is None else result.get()


def show_example_tiff(img):
    shape = img.shape
    root = tk.Tk()
    root.title('Example data structure')

    # Create a figure and axis
    fig, ax1 = plt.subplots()

    fig.suptitle('Example data structure')

    # Plot the data
    image1 = ax1.imshow(img[0, 0], cmap='gray')

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)
    
    ax1.grid(True)

    def update_plot(val):
        nonlocal img
        idx0 = int(scrollbar_dim0.get())
        idx1 = int(val)

        img_disp = img[idx0, idx1]
        image1 = ax1.imshow(img_disp, cmap='gray')
        fig.canvas.draw_idle()
    
    scrollbar_dim0 = tk.Scale(root, from_=0, to=shape[0]-1, orient=tk.HORIZONTAL, label='fluorecence', command=lambda val: update_plot(scrollbar_dim1.get()))
    scrollbar_dim1 = tk.Scale(root, from_=0, to=shape[1]-1, orient=tk.HORIZONTAL, label="time", command=update_plot, resolution=1)

    scrollbar_dim1.pack(side=tk.BOTTOM, fill=tk.X)
    scrollbar_dim0.pack(side=tk.BOTTOM, fill=tk.X)

    happy = False
    def on_done():
        nonlocal happy
        happy = True
        root.quit()
        root.destroy()
        return happy

    def on_sad():
        root.quit()
        root.destroy()

    happyButton = ttk.Button(root, text="Done", command=on_done)
    happyButton.pack(side=tk.BOTTOM, padx=20, pady=10)

    sadButton = ttk.Button(root, text="Not Done", command=on_sad)
    sadButton.pack(side=tk.BOTTOM, padx=20, pady=10)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_sad)
    root.mainloop()
    plt.close(fig)
    return happy

def provide_struc_options(ndimg=None):
    possible_dimensions = [2, 3, 4]
    if ndimg:
        possible_dimensions = [ndimg]

    dimensions = ("(x,y)", "time", "channels")
    if 4 in possible_dimensions:
        dim_single_tiff = list(permutations(dimensions))
        options_4D = [f'4D TIFFs: {', '.join(perm)}' for perm in dim_single_tiff]
    else:
        options_4D = []

    if 3 in possible_dimensions:
        dim_multiple_tiff = list(permutations(dimensions, 2))
        options_3D = [f'3D TIFFs: {', '.join(perm)}' for perm in dim_multiple_tiff]
        options_3D_not_supported = ['3D TIFFs: time, channels', '3D TIFFs: channels, time']
        options_3D = [opt for opt in options_3D if opt not in options_3D_not_supported]
    else:
        options_3D = []
    
    if 2 in possible_dimensions:
        options_2D = ['2D TIFFs: (x,y)']
    else:
        options_2D = []

    return options_4D + options_3D + options_2D

def restruc_output(selection):
    if selection.startswith('3D TIFFs: '):
        selection = selection.replace('3D TIFFs: ', '')
        selection = selection.replace('(x,y)', 'x, y')
        output = selection.split(', ')#
        dimension_input=3

    elif selection.startswith('4D TIFFs: '):
        selection = selection.replace('4D TIFFs: ', '')
        selection = selection.replace('(x,y)', 'x, y')
        output = selection.split(', ')#
        dimension_input=4

    elif selection == '2D TIFFs: (x,y)': 
        output = ['x', 'y']
        dimension_input=2
    
    else:
        raise ValueError(f"Invalid selection: {selection}")

    return output, dimension_input


def ask_data_structure(img_original=None, selct_opt_example=True, final_lockin=False, path=None):
    if img_original is not None:
        ndimg = img_original.ndim
    else:
        ndimg = None

    title = "What structure does your data have?"
    view_example_option = ["View example data structure"]

    if selct_opt_example:
        selection = drop_down_menu(title, view_example_option + provide_struc_options(ndimg=ndimg))
    else:
        selection = drop_down_menu(title, provide_struc_options(ndimg=ndimg))

    if final_lockin:
        output, dimension_input = restruc_output(selection)
        return output, dimension_input, path

    if selection is None:
        return None, None, None

    if selection == view_example_option[0]:
        path = ask_for_folder_file('Example TIFF file', askopenfilename_toggle=True, file_types=['*.tif', '*.tiff'], file_types_string='TIFF files')
        img = skimage.io.imread(path)
        img_original = img.copy()
        img_dim = img_original.ndim
        shape = img_original.shape
        response = ask_for_another_round('Do you want to see an example?', f'Image dimension: {img_dim}, shape: {shape}\nDo you want to see an example?\n!The windows will maybe open behind other windows!')
        if response:
            if img_dim == 2:
                img = img[np.newaxis, np.newaxis, :, :]
            if img_dim == 3:
                img = img[np.newaxis, :, :, :]
            happy = show_example_tiff(img)
            if happy:
                output, dimension_input = restruc_output(selection)
                return output, dimension_input, path
            else:
                return ask_data_structure(img_original=img_original, selct_opt_example=False, path=path)

        else:
            return ask_data_structure(img_original=img_original, selct_opt_example=False, final_lockin=True, path=path)
    elif not selct_opt_example:
        response = ask_for_another_round('Do you want to see an(other) example?', f'Do you want to see an example?\n!The windows will maybe open behind other windows!')
        if response:
            output, dimension_input = restruc_output(selection)

            desired_dim_order = ['channels', 'time', 'x', 'y']
            missing_dims = [dim for dim in desired_dim_order if dim not in output]
            img = img_original.copy()
            if ndimg == 2:
                img = img[np.newaxis, np.newaxis, :, :]
            if ndimg == 3:
                if missing_dims == ['channels']:
                    img = img_original[np.newaxis, :, :, :]
                    output = ['channels'] + output
                else:
                    img = img[:, np.newaxis, :, :]
                    # enter time at second position
                    output = [output[0]] + ['time'] + output[1:]

            img = np.moveaxis(img, [output.index(dim) for dim in desired_dim_order if dim in output], list(range(len(output))))
            happy = show_example_tiff(img)
            if happy:
                return output, dimension_input, path
            else:
                return ask_data_structure(img_original=img_original, selct_opt_example=False, path=path)

        else:
            return ask_data_structure(img_original=img_original, selct_opt_example=False, final_lockin=True, path=path)

    else:
        output, dimension_input= restruc_output(selection)
        return output, dimension_input, path

def two_img_preview(img1, img2):
    # Create the main window
    switch_img1_img2 = False
    img_bad = False

    root = tk.Tk()
    root.title("Data preview")

    # Create a figure and axis
    fig, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)
    fig.suptitle('Data preview')

    # Plot the data
    image1 = ax1.imshow(img1[0], cmap='gray')
    ax1.set_title('Bright field')

    image2 = ax2.imshow(img2[0], cmap='gray')
    ax2.set_title('Fluroscence')

    # Create a canvas to display the plot
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    def on_done():
        root.quit()
        root.destroy()

    def on_bad():
        nonlocal img_bad
        img_bad = True
        on_done()

    def on_switch():
        nonlocal switch_img1_img2, img1, img2, ax1, ax2, image1, image2
        switch_img1_img2 = True
        img1, img2 = img2, img1

        idx = int(scrollbar.get())
        image1 = ax1.imshow(img1[idx], cmap='gray')
        image2 = ax2.imshow(img2[idx], cmap='gray')
        fig.canvas.draw_idle()

    done_button = ttk.Button(root, text="Done", command=on_done)
    done_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    bad_button = ttk.Button(root, text="Doesn't look good", command=on_bad)
    bad_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    switch_img1_img2_button = ttk.Button(root, text="Switch Images", command=on_switch)
    switch_img1_img2_button.pack(side=tk.BOTTOM, padx=20, pady=10)

    def update_plot(val):
        idx = int(val)
        image1.set_data(img1[idx])
        image2.set_data(img2[idx])
        fig.canvas.draw_idle()

    # Add a scrollbar for time points
    scrollbar = tk.Scale(root, from_=0, to=len(img1)-1, orient=tk.HORIZONTAL, command=update_plot)
    scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Start the Tkinter main loop
    root.protocol("WM_DELETE_WINDOW", on_done)
    root.mainloop()
    plt.close(fig)
    return switch_img1_img2, img_bad

def ask_for_metadata_and_exp_name(dict_len, dict_rate):
    title = 'Please select the correct metadata for pixel size\nand an experiment name'

    input_spec = [
    {
        "name": "Experiment Name",
        "type": str,
        "default": "new_experiment"
    }
    ]
    values = list(dict_len.values())
    value_act = (2, 2)
    for value in values:
        if not value == (None, None):
            value_act = value
            break

    input_spec +=  [
        {"name": "Pixel length [um]", "type": float, "default": value_act[0]},
    ]

    values = list(dict_rate.values())
    value_act = 60
    for value in values:
        if not value == None:
            value_act = value
            break

    input_spec += [
        {"name": "Time interval [s]", "type": float, "default": value_act}
    ]

    result = ask_for_input(title, input_spec)
    if result is None:
        return None, None, None

    pixel_size = result["Pixel length [um]"]
    time_interval = result["Time interval [s]"]
    experiment_name = result["Experiment Name"]

    return experiment_name, pixel_size, time_interval
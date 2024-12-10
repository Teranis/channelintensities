from .analysis import generate_lines, find_pixel_weights
import numpy as np


def demo_generate_lines(bbox=[(1, 1), (5, 4), (10, 0), (0,0)], normal_lines_num=4):
    lines, edge_lines = generate_lines(bbox, normal_lines_num=normal_lines_num, return_edge_lines=True)

    # Print the result
    print("Lines:")
    for line in lines:
        print(line)
        print(np.linalg.norm(np.array(line[1]) - np.array(line[0])))

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    for line in lines:
        ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='red')
    for point in bbox:
        ax.plot(point[0], point[1], 'bo')
    for line in edge_lines:
        ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='blue')
    
    plt.show()

def demo_find_pixel_weights(grid_size=(10,10), line_params=((9, 1), (1, 1))):
    pixel_lengths = find_pixel_weights(grid_size, line_params)

    # Print the result
    np.set_printoptions(precision=2, suppress=True)
    print("Pixel Lengths:")
    print(pixel_lengths)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.imshow(pixel_lengths, cmap='viridis', origin='lower')
    ax.plot([line_params[0][0], line_params[1][0]], [line_params[0][1], line_params[1][1]], color='red')
    plt.show()
#
#using numpy create randomg bounding box of different sizes

def general_demo():
    iterations = 10
    for i in range(iterations):
        bbox = []
        for i in range(4):
            bbox.append((np.random.randint(0, 100), np.random.randint(0, 100)))
        normal_lines_num = np.random.randint(2, 5)
        try:
            lines, edge_lines = generate_lines(bbox=bbox, normal_lines_num=normal_lines_num, return_edge_lines=True)
        except ValueError as e:
            print(e)
            continue

        img_shape = (100, 100)

        pixel_weights_master = np.zeros(img_shape)
        for line in lines:
            pixel_weights = find_pixel_weights(img_shape, line)
            pixel_weights_master += pixel_weights

        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()

        ax.imshow(pixel_weights_master, cmap='viridis', origin='lower')
        ax.grid(True)
        for point in bbox:
            ax.plot(point[0], point[1], 'bo')
        for line in edge_lines:
            ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='blue')
        for line in lines:
            ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]], color='red')

        plt.show()
# Cell Size Regulation Dynamics Toolkit

This repository contains tools for analyzing cell size regulation dynamics by annotating single cells across generations. The workflow emphasizes a GUI-based approach for defining regions, saving plots, and managing analysis results.

## Features

1. **Channel Alignment and Preprocessing**  
   - Rotate the image so the main channel is at the bottom.
   - Cut unwanted frames to focus on the relevant data.

2. **GUI-Based Region Definition**  
   - Use an interactive GUI to define bounding boxes (bbox) for each channel.

3. **Weight Map Calculation**  
   - Generate equidistant lines throughout the bbox. 
   - Each pixel is assigned a value based on the length of its line of traversal within the bbox.  
   *(See illustration below)*

4. **Data Storage**  
   - Results are saved in a structured table for further analysis.

5. **Visualization and Analysis**  
   - Predefined plots for visualizing results.
   - Out-of-the-box fitting for diffusion coefficient (D).

## Installation Guide

# Setting Up Your Environment

To ensure a clean and isolated development environment, it's recommended to use a Python virtual environment (venv). Follow the instructions below to install Python, create a virtual environment, and set up the toolkit.

---

### 1. **Installing Python**
   
#### **For Windows**
1. Download the latest Python installer from the [official Python website](https://www.python.org/).
2. Run the installer and make sure to check the option **"Add Python to PATH"** during the installation process.
3. Verify the installation by running the following command in the Command Prompt:
   ```bash
   python --version
   ```
   
#### **For macOS**
1. Install Python using **Homebrew** (recommended). First, install Homebrew if you haven't already:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python:
   ```bash
   brew install python
   ```
3. Verify the installation:
   ```bash
   python3 --version
   ```

#### **For Linux**
1. Use your package manager to install Python (if not already installed). For example:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```
2. Verify the installation:
   ```bash
   python3 --version
   ```

---

### 2. **Creating a Virtual Environment**

1. Open a terminal (Command Prompt, PowerShell, or your OS-specific terminal).
2. Navigate to your project folder:
   ```bash
   cd /path/to/your/project
   ```
3. Create a virtual environment:
   ```bash
   python -m venv <your_venv_name>
   ```
   This will create a folder named `your_venv_name` in your project directory containing the isolated environment.

   Replace <your_venv_name> with the deisred name, for example:

   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - **Windows**:
     ```bash
     <your_venv_name>\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source <your_venv_name>/bin/activate
     ```

5. Verify that the virtual environment is active:
   - Your terminal prompt should now show `(venv)` at the beginning.
   - Check the Python version in the environment:
     ```bash
     python --version
     ```

---

### 3. **Installing the Toolkit**

With the virtual environment active, install the `cell-size-dynamics` toolkit from PyPI:

```bash
pip install cell-size-dynamics
```

---

### 4. **Installing Additional Dependencies**

If you encounter missing dependencies or want to install optional packages for development, use the `requirements.txt` file if provided:

```bash
pip install -r requirements.txt
```

---

### 5. **Deactivating the Virtual Environment**

When you're done, deactivate the virtual environment to return to your system Python:

```bash
deactivate
```

---

By following these steps, you ensure that your project dependencies are managed cleanly and do not interfere with other Python projects on your system. 

## Workflow Instructions
### 0. Select steps from the main menu
- steps can be skipped, and every step which produces output is saved, so feel free to try out different things

### 0. Load Data
- Loading data from TIFF files. 4D, 2x3D (one for each channel), 1x3D (all in one folder with one for each time point), 2x2D (two folders with all imgs for one channel in one folder) is supported

### 2. Align the Main Channel
- Rotate the image so that the primary channel is at the bottom using the GUI elements provided.

### 3. Trim Frames
- Use the GUI to select and remove unwanted frames from the dataset.

### 4. Define Bounding Boxes
- Open the GUI to manually define bounding boxes (bbox) for each channel. This step allows for precise region targeting.

### 5. Generate Weight Maps
- The toolkit automatically generates equidistant lines within each defined bbox.  
- **How It Works**: 
  - Each line is spaced equidistantly within the bbox.  
  - The value assigned to each pixel corresponds to the traversal length of its associated line.

### 6. Save Results
- Results are saved in a tabular format for further analysis and reproducibility.

### 7. Visualization and Analysis
- Visualize results using predefined plot templates.
- Fit diffusion coefficients (D) directly using the integrated fitting tools.

## Tips for Saving Plots

When saving plots, always use the **matplotlib GUI** elements for consistent file management and output quality.

## Contribution

Feel free to contribute to this project by submitting pull requests or reporting issues. For questions, contact the repository maintainer.

---

Happy analyzing! 🎉

# 🦠 CellSePi – Cell Segmentation Pipeline 🦠

[![PyPI version](https://img.shields.io/pypi/v/cellsepi.svg)](https://pypi.org/project/cellsepi/)
[![License](https://img.shields.io/pypi/l/cellsepi.svg)](LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/cellsepi.svg)](https://pypi.org/project/cellsepi/)
[![Last Commit](https://img.shields.io/github/last-commit/PraiseTheDarkFlo/cellsepi.svg)](https://github.com/PraiseTheDarkFlo/cellsepi)
![GitHub Repo stars](https://img.shields.io/github/stars/PraiseTheDarkFlo/cellsepi)
![GitHub forks](https://img.shields.io/github/forks/PraiseTheDarkFlo/cellsepi)
![GitHub issues](https://img.shields.io/github/issues/PraiseTheDarkFlo/cellsepi)

> **Segmentation of microscopy images and data analysis pipeline with a graphical user interface, powered by Cellpose.**

## 🌟 Highlights

- **User-Friendly Interface:** Intuitive GUI for seamless image segmentation.
- **Advanced Segmentation:** Leverages Cellpose models for accurate cellular segmentation.
- **Correction Tools:** Easily refine and correct segmentation results with an integrated drawing tool.
- **Fluorescence Readout:** Automatically extract fluorescence data.
- **Correction Tools:** Easily refine and correct segmentation results.
- **Fluorescence Readout:** Automatically extract fluorescence data.
- **Custom Model Training:** Train and fine-tune models with your own data.
- **Batch Processing:** Process multiple images simultaneously.
- **Multi-Format Support:** Compatible with `.lif` and `.tif`/`.tiff` image formats.
- **Configurable Profiles:** Save and manage processing parameters effortlessly.
- **Adjustable Image Settings:** Manually or automatically fine-tune contrast and brightness.

## ℹ️ Overview

This project was developed in the context of a Bachelor project commissioned by the [Self-Organizing Systems Lab](https://www.bcs.tu-darmstadt.de/welcome/index.en.jsp) of the Technical University Darmstadt and supervised by [Eric Kubaczka](https://github.com/ERIK-KE). CellSePi is a powerful segmentation pipeline designed for microscopy images, featuring an interactive GUI to streamline your workflow. By utilizing the advanced Cellpose segmentation engine, CellSePi empowers researchers to efficiently process and analyze cellular images.

## 🚀 Usage

**1. Start the Application**  
Run the following command to launch the GUI:

```bash
python -m cellsepi
```

**Interface Overview**  
Main Window Start Screen
![Main Window Start Screen](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/images/main_window_start_screen.png?raw=true)

Main Window with Images
![Main Window with Images](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/images/main_window_with_images.png?raw=true)



**Options**  
- The dark/light theme adapts to your system settings. The changed theme is only active for the current session. 
- Mask and outline colors can be customized and are saved between sessions.
- Mask opacity can be changed for the current session.

> **Note:** Changes to the **Mask Opacity** will only appear in the drawing window after reloading the currently opened image by pressing on the **Drawing Tools** button.

![Options](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/options.gif?raw=true)

**Profiles**  
Save and manage the following parameters:

- **Bright-Field Channel:**  
  The channel on which segmentation is performed and whose masks are currently displayed.

- **Channel Prefix:**  
  The prefix in the image name that separates the series name and the channel. For example, if the channel prefix is set to `c`, the images `series100c1` and `series100c2` are recognized as part of series100 with channels 1 and 2.

- **Mask Suffix:**  
  Specifies the suffix that is used to identify and create the masks of the corresponding images. For instance, `series100c1_seg` is recognized as the mask for the image `series100c1`.

- **Diameter:**  
  Represents the average cell diameter used by the segmentation model.

> **Note:** Changes to the **Mask Suffix** or **Channel Prefix** will only take effect when new files are loaded.


![Profiles](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/profiles.gif?raw=true)

**Segmentation**  
To start segmentation process select both:
- a `.lif` or `.tif`/`.tiff` file 
- a compatible model

You will be alerted if you selected an incompatible model, when trying to start the segmentation. 

During segmentation, you can:
- **Pause:** Temporarily halt the process and resume later.
- **Cancel:** Abort the process, reverting to the previous masks or removing them if none existed before.
> **Note:** Large images can take longer to pause or to cancel, because the segmentation of the current image needs to be finished.

![Segmentation](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/segmentation.gif?raw=true)


**Readout**  
Generates an `.xlsx` file containing the extracted fluorescence values. Click the "Open fluorescence file" button to launch your system’s default spreadsheet application with the generated file (e.g. ONLYOFFICE as seen below).

![Readout](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/readout.gif?raw=true)

**Drawing Tools**  
Correct segmentation errors manually or draw masks to train new models.  
- **Cell ID Shifting:** Automatically adjusts cell IDs to maintain a consecutive numbering when a cell is deleted.
- **Drawing:** Draw own cells. Finishes the outline and fills the cell with color automatically 
- **Deletion:** Delete an unwanted cell
- **Undo/Redo changes:** If the deletion or drawing is not to your liking, you are able to reverse the made changes 

All changes in the Drawing Tools window are synchronized in real time with the main window.

![Drawing Tools](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/drawing_tools.gif?raw=true)


**Brightness and Contrast**  
Enhance the visibility of your image by using the brightness and contrast sliders. The "Auto brightness and contrast" button automatically adjusts and normalizes the image.  

![Brightness Contrast](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/brightness_contrast.gif?raw=true)

**Average Diameter**  
The average diameter of all cells over all images is displayed and updated with every change in the masks. The cell diameter is approximated by assuming circular cells and calculating the diameter from the area.  

![Average Diameter](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/images/average_diameter.png?raw=true)

**Training**  
Train your own models using the **Cellpose** framework. Two training modes are available:
1. **New Model Training:** Train a model from scratch using standard Cellpose models (`nuclei`, `cyto`, `cyto2` or `cyto3`).
2. **Model Fine-Tuning:** Retrain an existing model with your own images and masks for improved performance.

![Training](https://github.com/PraiseTheDarkFlo/CellSePi/blob/main/docs/gifs/training.gif?raw=true)

## ⬇️ Installation

To install CellSePi, simply run:

```bash
pip install cellsepi
```

This command automatically installs all required dependencies as specified in the package configuration.

**Required Packages (with versions):**

- **Python 3.8+**
- `numpy==1.26.4`
- `numba==0.61.0`
- `pillow`
- `pandas`
- `openpyxl`
- `cellpose==3.1.1.1`
- `flet==0.25.2`
- `flet-desktop==0.25.2`
- `flet-runtime==0.24.1`
- `matplotlib`
- `pytest`
- `pyqt5`
- `flet_contrib`
- `flet_core==0.24.1`
- `bioio==1.2.0`
- `bioio-lif`

## 📚 Citations

Our segmentation and models are powered by [CellPose](https://github.com/MouseLand/cellpose).

- **Stringer, C., Wang, T., Michaelos, M., & Pachitariu, M. (2021). Cellpose:**  
  a generalist algorithm for cellular segmentation. *Nature Methods, 18*(1), 100-106.
- **Pachitariu, M. & Stringer, C. (2022). Cellpose 2.0:**  
  how to train your own model. *Nature Methods, 1-8.*
- **Stringer, C. & Pachitariu, M. (2025). Cellpose3:**  
  one-click image restoration for improved segmentation. *Nature Methods.*
- **Eva Maxfield Brown, Dan Toloudis, Jamie Sherman, Madison Swain-Bowden, Talley Lambert, Sean Meharry, Brian Whitney, AICSImageIO Contributors (2023). BioIO:**  
  Image Reading, Metadata Conversion, and Image Writing for Microscopy Images in Pure Python [Computer software]. [GitHub](https://github.com/bioio-devs/bioio)
- **dilli_hangrae(2024):**
  Scanline Filling Algorithm. [Website](https://medium.com/@dillihangrae/scanline-filling-algorithm-852ad47fb0dd)

## ✍️ Authors

Developed by:  
- **Jenna Ahlvers** – [GitHub](https://github.com/Jnnnaa)  
- **Santosh Chhetri Thapa** – [GitHub](https://github.com/SantoshCT111)  
- **Nike Dratt** – [GitHub](https://github.com/SirHenry10)  
- **Pascal Heß** – [GitHub](https://github.com/Pasykaru)  
- **Florian Hock** – [GitHub](https://github.com/PraiseTheDarkFlo)

## 📝 License

This project is licensed under the **Apache License 2.0** – see the [LICENSE](LICENSE) file for details.

## 📖 How to cite 
If you use our repository in you own work, please cite us as follows: 
```bash
Jenna Ahlvers,Santosh Chhetri Thapa, Nike Dratt, Pascal Heß, Florian Hock(2025). CellSePi: Cell Segmentation Pipeline[computer software]. GitHub. https://github.com/PraiseTheDarkFlo/CellSePi
```
or as bibtext: 
```bash
@misc{cellsepi,
  author    = {Ahlvers, Jenna and Chhetri Thapa, Santosh and Dratt, Nike and Heß, Pascal and Hock, Florian},   
  title     = {CellSePi: Cell Segmentation Pipeline},  
  year      = {2025},  
  publisher = {GitHub},  
  url       = {https://github.com/PraiseTheDarkFlo/CellSePi}  
}
```

## 💭 Feedback & Contributions

Report bugs or suggest features via [GitHub Issues](https://github.com/PraiseTheDarkFlo/CellSePi/issues).

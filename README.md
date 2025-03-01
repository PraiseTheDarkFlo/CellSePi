# 🦠 **CellSePi** – Cell Segmentation Pipeline 🦠

> **Microscope segmentation and data analysis pipeline with a graphical interface, based on Cellpose**  

## 🌟 **Highlights**  
✅ **Easy-to-use** segmentation with a graphical interface  
✅ **Segmentation** based on Cellpose models  
✅ **Segmentation correction** tools   
✅ **Readout Flureszens** possible  
✅ **Custom model training** and fine-tuning options   
✅ **Batch processing** for multiple images  
✅ **Lif and Tif** image support   
✅ **Profiles** for different Lif's and Tif's  
✅ **Contrast and Brightness** adjustments possible

## ℹ️ **Overview**  
CellSePi is a segmentation pipeline designed for **microscopy images**, featuring an interactive GUI for easier workflow integration. It utilizes **Cellpose** as the core segmentation engine, allowing researchers to efficiently process and analyze cellular images.  

## 📚 **Citation**  
Our segmentation and models are powered by [CellPose](https://github.com/MouseLand/cellpose) and includes additional tools for correction and analysis.  

- **Stringer, C., Wang, T., Michaelos, M., & Pachitariu, M. (2021). Cellpose:**  
a generalist algorithm for cellular segmentation. Nature methods, 18(1), 100-106.
- **Pachitariu, M. & Stringer, C. (2022). Cellpose 2.0**:  
how to train your own model. Nature methods, 1-8.
- **Stringer, C. & Pachitariu, M. (2025). Cellpose3:**  
one-click image restoration for improved segmentation. Nature Methods.  
 

## ✍️ **Authors**  
Developed by:
- **Jenna Ahlvers**, [GitHub](https://github.com/Jnnnaa)    
            
- **Santosh Chhetri Thapa**, [GitHub](https://github.com/SantoshCT111)    
            
- **Nike Dratt**, [GitHub](https://github.com/SirHenry10)    
            
- **Pascal Heß**, [GitHub](https://github.com/Pasykaru)    
            
- **Florian Hock**, [GitHub](https://github.com/PraiseTheDarkFlo)  

## 📝 License  
This project is licensed under the **Apache License 2.0** – see the [LICENSE](LICENSE) file for details.  

## 🚀 **Usage**  

**1. Start the application**  
Run the following command to start the GUI:  
```bash
python -m cellsepi
```
**Interface overview** (without image left side and with images right side)
<p float="left">
  <img src="docs/images/main_window_start_screen.png" width="400" />
  <img src="docs/images/main_window_with_images.png" width="400" />
</p>


**Options**  
- Dark/Light Theme is based on your system and if you change it in options its only for this season.
- Mask and Outline Color are saved in the config file so they are permanent.  

![Options](docs/gifs/options.gif)

**Profiles**  
Our profiles store various parameters **bright-field channel**, **channel prefix**, **mask suffix**, and **diameter**. 

![Profiles](docs/gifs/profiles.gif)  

**Segmentation**   
To start the segmentation you need to select:
- lif or tif files
- a model  

If the snackbar says ```You have selected an incompatible file for the segmentation model.``` than you selected model is not compatible with the Cellpose segmentation prozess.

While segmentation there are two option:
- **pause**: this pauses the segmentation process (this can take some time if the images are large) and with **resume** button you can continue the segmentation.
- **cancel**: this cancels the segmentation process and sets the mask to the old mask before the segmentation started or deletes them if there was no mask.

![Segmentation](docs/gifs/segmentation.gif)

**Readout**  
Generates an ```.xlsx``` file containing the extracted fluorescence values.

To open the generated Excel file with your system’s default spreadsheet program, simply click the "Open Excel" button in the GUI. This will automatically launch the application associated with ```.xlsx``` files on your operating system (e.g., ONLYOFFICE in the example below).  

![Readout](docs/gifs/readout.gif)

**Drawing Tools**  
To correct wrong segmentation by the model there is the possibility to fix them by hand or if you want you can also draw just the mask without the model to create them to train a new model.
- **Cell ID shifting**: Shifts the mask when a mask got deleted to restore an order without gaps.

All changes are synchronised between the **Drawing Tools** window and the **main** window. So if you delete or draw something in the **Drawing Tools** window you can instantly see it in the **main** window. Furthermore, when you have the **Drawing Tools** window open while segmentation it also updates the drawing window live.

![Drawing Tools](docs/gifs/drawing_tools.gif)

**Training**  
#TODO: write training part and screenrecord
![Segmentation](docs/gifs/drawing_tools.gif)
## ⬇️ **Installation**  
```bash
pip install cellsepi
```
Requirements are listed in `requirements.txt`. Make sure you have:  
- **Python 3.8+**  
- `numpy==1.26.4`  
- `numba==0.61.0`
- `pillow`  
- `pandas`  
- `openpyxl`  
- `cellpose==3.1.1.1`  
- `flet==0.25.2`  
- `flet-desktop == 0.25.2` 
- `flet-runtime == 0.24.1`  
- `matplotlib`  
- `pytest`  
- `pyqt5`  
- `flet_contrib`  
- `flet_core == 0.24.1`
- `bioio==1.2.0`
- `bioio-lif`

To install all dependencies:  
```bash
pip install -r requirements.txt
```

## 💭 **Feedback & Contributions**  
- Report bugs or suggest features via [GitHub Issues](https://github.com/PraiseTheDarkFlo/CellSePi/issues)


from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def get_data_files():
    data_files = []

    if os.path.isfile('config.json'):
        data_files.append(('share/cellsepi', ['config.json']))

    models_dir = 'models'
    for root, _, files in os.walk(models_dir):
        install_dir = os.path.join('share/cellsepi', root)

        filtered_files = [
            os.path.join(root, f)
            for f in files
            if f.endswith('.gitkeep') or (f != '.gitkeep' and files)
        ]

        if filtered_files:
            data_files.append((install_dir, filtered_files))

    return data_files


setup(
    name="cellsepi",
    version="0.4",
    license="Apache License 2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy==1.26.4", "pillow", "pandas", "openpyxl", "cellpose==3.1.1.1",
        "flet==0.25.2", "flet-desktop==0.25.2", "flet-runtime==0.24.1", "bioio==1.2.0",
        "numba==0.61.0", "matplotlib", "pytest", "pyqt5", "flet_contrib", "flet_core==0.24.1",
        "bioio-lif"
    ],
    python_requires=">=3.8",
    author="Jenna Ahlvers, Santosh Chhetri Thapa, Nike Dratt, Pascal Heß, Florian Hock",
    url="https://github.com/PraiseTheDarkFlo/CellSePi",
    description="Segmentation of microscopy images and data analysis pipeline with a graphical user interface, powered by Cellpose.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "cellsepi = cellsepi.main:main",
        ],
    },
    data_files=get_data_files(),
    include_package_data=True
)

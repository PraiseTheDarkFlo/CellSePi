from setuptools import setup, find_packages

setup(
    name="cellsepi",
    version="0.1",
    license="Apache License 2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy==1.26.4", "pillow", "pandas", "openpyxl", "cellpose==3.1.1.1",
        "flet==0.25.2", "flet-desktop==0.25.2", "flet-runtime==0.24.1","bioio==1.2.0", "numba==0.61.0",
        "matplotlib", "pytest", "pyqt5", "flet_contrib", "flet_core==0.24.1", "bioio-lif"
    ],
    entry_points={
        "console_scripts": [
            "cellsepi = cellsepi.main:main",
        ],
    },
)



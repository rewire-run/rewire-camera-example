import os
from glob import glob

from setuptools import setup

package_name = "camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools"],
    data_files=[
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    entry_points={
        "console_scripts": [
            "image_publisher = camera.image_publisher:main",
            "depth_publisher = camera.depth_publisher:main",
        ],
    },
)

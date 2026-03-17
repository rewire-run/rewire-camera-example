import os
from glob import glob

from setuptools import setup

package_name = "rewire_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools"],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        (os.path.join("share", package_name), ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    entry_points={
        "console_scripts": [
            "image_publisher = rewire_camera.image_publisher:main",
            "depth_publisher = rewire_camera.depth_publisher:main",
        ],
    },
)

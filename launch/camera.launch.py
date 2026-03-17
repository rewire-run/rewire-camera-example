from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

width = LaunchConfiguration("width")
height = LaunchConfiguration("height")
frequency_hz = LaunchConfiguration("frequency_hz")

width_arg = DeclareLaunchArgument("width", default_value="320")
height_arg = DeclareLaunchArgument("height", default_value="240")
frequency_hz_arg = DeclareLaunchArgument("frequency_hz", default_value="30")

image_publisher = Node(
    package="rewire_camera",
    executable="image_publisher",
    parameters=[{"width": width, "height": height, "frequency_hz": frequency_hz}],
)

depth_publisher = Node(
    package="rewire_camera",
    executable="depth_publisher",
    parameters=[{"width": width, "height": height, "frequency_hz": frequency_hz}],
)

republish_rgb = Node(
    package="image_transport",
    executable="republish",
    name="republish_rgb",
    arguments=["raw", "compressed"],
    remappings=[
        ("in", "/camera/image_raw"),
        ("out/compressed", "/camera/image_raw/compressed"),
    ],
)


def generate_launch_description():
    return LaunchDescription(
        [
            width_arg,
            height_arg,
            frequency_hz_arg,
            image_publisher,
            depth_publisher,
            republish_rgb,
        ]
    )

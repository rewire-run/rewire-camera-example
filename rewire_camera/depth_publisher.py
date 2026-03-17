import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import Header

TOPIC = "/camera/depth"
WIDTH = 320
HEIGHT = 240
FREQUENCY_HZ = 30
MIN_DEPTH = 0.3
MAX_DEPTH = 10.0

class DepthPublisher(Node):
    def __init__(self):
        super().__init__("camera_depth_publisher")

        self.declare_parameter("width", WIDTH)
        self.declare_parameter("height", HEIGHT)
        self.declare_parameter("frequency_hz", FREQUENCY_HZ)

        self.width = self.get_parameter("width").value
        self.height = self.get_parameter("height").value
        self.frequency_hz = self.get_parameter("frequency_hz").value
        self.frame_count = 0

        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1)
        self.raw_pub = self.create_publisher(Image, TOPIC, qos)
        self.compressed_pub = self.create_publisher(CompressedImage, f"{TOPIC}/compressed", qos)

        y = np.linspace(0, 1, self.height, dtype=np.float32)
        x = np.linspace(0, 1, self.width, dtype=np.float32)
        self._xgrid, self._ygrid = np.meshgrid(x, y)

        self.get_logger().info(
            f"Publishing {self.width}x{self.height} depth (raw + compressed) at {self.frequency_hz} Hz"
        )

        self.create_timer(1.0 / self.frequency_hz, self._on_publish)

    def _on_publish(self):
        now = self.get_clock().now().to_msg()
        header = Header(stamp=now, frame_id="camera")
        depth = self._generate_depth(self.frame_count)

        raw = Image()
        raw.header = header
        raw.height = self.height
        raw.width = self.width
        raw.encoding = "32FC1"
        raw.is_bigendian = 0
        raw.step = self.width * 4
        raw.data = depth.tobytes()
        self.raw_pub.publish(raw)

        depth_16u = (depth * 1000.0).astype(np.uint16)
        _, png = cv2.imencode(".png", depth_16u)
        compressed = CompressedImage()
        compressed.header = header
        compressed.format = "png"
        compressed.data = png.tobytes()
        self.compressed_pub.publish(compressed)

        self.frame_count += 1

    def _generate_depth(self, frame: int):
        phase = frame * 0.05
        return (
            MIN_DEPTH
            + (MAX_DEPTH - MIN_DEPTH)
            * (
                0.5
                + 0.3 * np.sin(2.0 * np.pi * self._xgrid + phase)
                + 0.2 * np.cos(2.0 * np.pi * self._ygrid + phase * 0.7)
            )
        ).astype(np.float32)


def main(args=None):
    rclpy.init(args=args)
    node = DepthPublisher()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

import numpy as np
import rclpy
from builtin_interfaces.msg import Time as TimeMsg
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from tf2_ros import StaticTransformBroadcaster

IMAGE_TOPIC = "/camera/image_raw"
WIDTH = 320
HEIGHT = 240
FREQUENCY_HZ = 30


class ImagePublisher(Node):
    def __init__(self):
        super().__init__("camera_image_publisher")

        self.declare_parameter("width", WIDTH)
        self.declare_parameter("height", HEIGHT)
        self.declare_parameter("frequency_hz", FREQUENCY_HZ)

        self.width = self.get_parameter("width").value
        self.height = self.get_parameter("height").value
        self.frequency_hz = self.get_parameter("frequency_hz").value
        self.frame_count = 0

        self.get_logger().info(
            f"Publishing {self.width}x{self.height} rgb8 images at {self.frequency_hz} Hz "
            f"({self.width * self.height * 3 / 1_000_000:.1f} MB/frame)"
        )

        image_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.publisher = self.create_publisher(Image, IMAGE_TOPIC, image_qos)

        self.tf_broadcaster = StaticTransformBroadcaster(self)
        self._publish_static_tf()

        self.pixels = np.empty((self.height, self.width, 3), dtype=np.uint8)
        self.pixels[:, :, 2] = 128

        r_base = np.linspace(0, 255, self.width, dtype=np.uint8)
        g_base = np.linspace(0, 255, self.height, dtype=np.uint8)
        self._r_base = r_base
        self._g_col = g_base[:, np.newaxis]

        period = 1.0 / self.frequency_hz
        self.timer = self.create_timer(period, self._on_timer)

    def _publish_static_tf(self):
        t = TransformStamped()
        t.header.stamp = TimeMsg(sec=0, nanosec=0)
        t.header.frame_id = "map"
        t.child_frame_id = "camera"
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 1.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t)
        self.get_logger().info("Published static TF: map -> camera")

    def _on_timer(self):
        now = self.get_clock().now().to_msg()

        self._fill_gradient(self.frame_count)

        msg = Image()
        msg.header = Header(stamp=now, frame_id="camera")
        msg.height = self.height
        msg.width = self.width
        msg.encoding = "rgb8"
        msg.is_bigendian = 0
        msg.step = self.width * 3
        msg.data = self.pixels.tobytes()

        self.publisher.publish(msg)
        self.frame_count += 1

    def _fill_gradient(self, frame: int):
        offset = np.uint8((frame * 7) & 0xFF)
        self.pixels[:, :, 0] = self._r_base + offset
        self.pixels[:, :, 1] = self._g_col


def main(args=None):
    rclpy.init(args=args)
    node = ImagePublisher()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

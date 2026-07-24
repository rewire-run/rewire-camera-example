from fractions import Fraction

import av
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Header

VIDEO_TOPIC = "/camera/video"
WIDTH = 320
HEIGHT = 240
FREQUENCY_HZ = 30
KEYFRAME_INTERVAL = 30

CODECS = {
    "h264": {
        "candidates": ("libx264", "libopenh264", "h264"),
        "options": {
            "libx264": {"preset": "ultrafast", "tune": "zerolatency"},
            "libopenh264": {"allow_skip_frames": "false"},
        },
    },
    "h265": {
        "candidates": ("libx265", "hevc"),
        "options": {
            "libx265": {
                "preset": "ultrafast",
                "tune": "zerolatency",
                "x265-params": "repeat-headers=1:frame-threads=1:log-level=error",
            },
        },
    },
}


class VideoEncoder:
    def __init__(self, codec: str, width: int, height: int, fps: int, gop: int):
        if codec not in CODECS:
            raise ValueError(f"unsupported codec {codec!r}, expected one of {sorted(CODECS)}")
        self.codec = codec
        self.time_base = Fraction(1, fps)
        spec = CODECS[codec]
        last_error = None
        for name in spec["candidates"]:
            try:
                ctx = av.CodecContext.create(name, "w")
            except av.FFmpegError as e:
                last_error = e
                continue
            ctx.width = width
            ctx.height = height
            ctx.pix_fmt = "yuv420p"
            ctx.time_base = self.time_base
            ctx.framerate = Fraction(fps, 1)
            ctx.gop_size = gop
            ctx.max_b_frames = 0
            ctx.options = spec["options"].get(name, {})
            self.ctx = ctx
            self.codec_name = name
            return
        raise RuntimeError(f"no {codec} encoder available: {last_error}")

    def encode(self, rgb: np.ndarray, pts: int) -> bytes:
        frame = av.VideoFrame.from_ndarray(rgb, format="rgb24").reformat(
            format="yuv420p"
        )
        frame.pts = pts
        frame.time_base = self.time_base
        return b"".join(bytes(packet) for packet in self.ctx.encode(frame))


class VideoPublisher(Node):
    def __init__(self):
        super().__init__("camera_video_publisher")

        self.declare_parameter("width", WIDTH)
        self.declare_parameter("height", HEIGHT)
        self.declare_parameter("frequency_hz", FREQUENCY_HZ)
        self.declare_parameter("codec", "h264")

        self.width = self.get_parameter("width").value
        self.height = self.get_parameter("height").value
        self.frequency_hz = self.get_parameter("frequency_hz").value
        self.codec = self.get_parameter("codec").value
        self.frame_count = 0

        self.encoder = VideoEncoder(
            self.codec, self.width, self.height, self.frequency_hz, KEYFRAME_INTERVAL
        )
        self.get_logger().info(
            f"Publishing {self.width}x{self.height} {self.codec} ({self.encoder.codec_name}) "
            f"at {self.frequency_hz} Hz on {VIDEO_TOPIC}"
        )

        qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10)
        self.publisher = self.create_publisher(CompressedImage, VIDEO_TOPIC, qos)

        self.pixels = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._r_base = np.linspace(0, 255, self.width, dtype=np.uint8)
        self._g_col = np.linspace(0, 255, self.height, dtype=np.uint8)[:, np.newaxis]

        period = 1.0 / self.frequency_hz
        self.timer = self.create_timer(period, self._on_timer)

    def _on_timer(self):
        now = self.get_clock().now().to_msg()

        self._fill_frame(self.frame_count)
        payload = self.encoder.encode(self.pixels, self.frame_count)
        self.frame_count += 1
        if not payload:
            return

        msg = CompressedImage()
        msg.header = Header(stamp=now, frame_id="camera_optical")
        msg.format = self.codec
        msg.data = payload
        self.publisher.publish(msg)

    def _fill_frame(self, frame: int):
        offset = np.uint8((frame * 7) & 0xFF)
        self.pixels[:, :, 0] = self._r_base + offset
        self.pixels[:, :, 1] = self._g_col
        self.pixels[:, :, 2] = 128

        size = min(self.width, self.height) // 5
        x = (frame * 4) % (self.width - size)
        y = (self.height - size) // 2
        self.pixels[y : y + size, x : x + size] = (255, 255, 255)


def main(args=None):
    rclpy.init(args=args)
    node = VideoPublisher()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

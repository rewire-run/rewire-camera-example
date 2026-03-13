# rewire-camera-example

Synthetic camera publishers for testing [rewire](https://github.com/rewire-run/rewire) image converters.

## Topics

| Topic | Type | Description |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | RGB8 scrolling gradient |
| `/camera/image_raw/compressed` | `sensor_msgs/CompressedImage` | JPEG via `image_transport` |
| `/camera/depth` | `sensor_msgs/Image` | 32FC1 animated sine wave (0.3–10m) |
| `/camera/depth/compressed` | `sensor_msgs/CompressedImage` | PNG-encoded 16UC1 depth |
| `/tf_static` | `tf2_msgs/TFMessage` | Static transform: `map` → `camera` |

## Setup

Requires [pixi](https://pixi.sh).

```bash
pixi install
```

## Usage

```bash
pixi run launch
```

With custom resolution and frame rate:

```bash
pixi run launch width:=1280 height:=720 frequency_hz:=10
```

## How it works

The launch file starts three nodes:

- **image_publisher** — publishes synthetic RGB images and a static TF (`map` → `camera`)
- **depth_publisher** — publishes raw 32FC1 depth and a PNG-compressed variant
- **republish** — `image_transport` republish node that produces JPEG from the raw RGB topic

In a separate terminal, run rewire to visualize all topics in Rerun:

```bash
pixi run rewire record --all
```

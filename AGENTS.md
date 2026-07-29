# AGENTS.md

## Project

Synthetic camera / depth / video publishers used to exercise
[rewire](https://github.com/rewire-run/rewire) image and VideoStream converters.
ROS 2 package name: `rewire_camera`. Build type: `ament_python`. Managed with
[pixi](https://pixi.sh).

## Layout

```text
rewire_camera/       # Python package
  image_publisher.py # RGB + camera_info + static TF
  depth_publisher.py # raw + compressed depth
  video_publisher.py # H.264/H.265 CompressedImage stream
launch/
  camera.launch.py   # image + depth + video nodes
config/
  rewire.json5       # rewire record config (used by `pixi run viz`)
  camera-example.rbl # Rerun blueprint
resource/            # ament package marker
package.xml          # ROS package manifest
setup.py / setup.cfg # ament_python install
pixi.toml            # env, deps, tasks (app / viz)
```

## Runtime

- Default ROS distro: **humble** (`pixi` default environment)
- Other envs: `jazzy`, `kilted`, `lyrical` via `pixi run -e <env> ...`
- Platforms: `osx-arm64`, `linux-64`
- Channels: conda-forge, robostack-*, prefix.dev/rewire;
  lyrical uses `https://prefix.dev/robostack-lyrical`
- Package build backend: `pixi-build-ros`
- Extra workspace deps: `numpy`, `opencv`, `av` (PyAV for video encode)

### Tasks

| Task | Command |
|------|---------|
| `pixi run app` | `ros2 launch rewire_camera camera.launch.py` |
| `pixi run viz` | `rewire record --config $PIXI_PROJECT_ROOT/config/rewire.json5` |

Setup: `pixi install`. Run app and viz in separate terminals.

Launch args (pass after `--`): `width`, `height`, `frequency_hz`, `video_codec`
(`h264` default, or `h265`):

```bash
pixi run app -- width:=1280 height:=720 frequency_hz:=10
pixi run app -- video_codec:=h265
```

### Rewire config (`config/rewire.json5`)

- `app_id`: `camera-example`
- `diagnostics`: enabled
- Topics: include `/**`, exclude `/rosout` and `/parameter_events`
- Prefer editing this file over hardcoding CLI flags on the `viz` task

## Published topics

| Topic | Type | Source |
|-------|------|--------|
| `/camera/image_raw` | `sensor_msgs/Image` | `image_publisher` |
| `/camera/image_raw/compressed` | `sensor_msgs/CompressedImage` | `image_transport` |
| `/camera/video` | `sensor_msgs/CompressedImage` | `video_publisher` (`format: h264`/`h265`) |
| `/camera/depth` | `sensor_msgs/Image` | `depth_publisher` |
| `/camera/depth/compressed` | `sensor_msgs/CompressedImage` | `depth_publisher` |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | `image_publisher` |
| `/tf_static` | `tf2_msgs/TFMessage` | `image_publisher` (`map` → `camera_optical`) |

## Nodes

- **image_publisher** — RGB8 scrolling gradient, camera info, static TF
- **depth_publisher** — 32FC1 depth + PNG-compressed 16UC1 depth
- **video_publisher** — H.264/H.265 via PyAV (`format: "h264"` / `"h265"`) for
  Rerun `VideoStream` (rewire ≥ 0.7.0)

Console entry points in `setup.py`: `image_publisher`, `depth_publisher`,
`video_publisher`.

## Dependencies (runtime)

`rclpy`, `sensor_msgs`, `geometry_msgs`, `std_msgs`, `tf2_ros` / `tf2_ros_py`,
`image_transport`, `image_transport_plugins`. Workspace: `rewire`, `zenohd`,
colcon, ros2cli stack per distro feature in `pixi.toml`.

## Conventions for agents

- Prefer small, focused changes; match existing style (minimal comments unless
  requested)
- Keep entry points and install paths in sync across `setup.py`, `package.xml`,
  and `pixi.toml` path package names (`ros-<distro>-rewire-camera`)
- When changing published topics/frames, update README topic table and this file
- Do not commit `.pixi/`, `__pycache__/`, `*.egg-info/`, or `files.txt`
- Do not commit `CLAUDE.md` or `.claude/` (if present)
- Git commits: conventional commits (`feat:`, `fix:`, `docs:`, …)
- Markdown lines ≤ 120 characters

## Out of scope

Synthetic publishers only — not real camera drivers or full perception stacks.
Viewer FFmpeg low-latency setup lives in the README under Testing VideoStream.

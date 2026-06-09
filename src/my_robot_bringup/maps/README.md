Place saved map files in this directory.

Expected Nav2 map input:

- map.yaml
- map.pgm or map.png referenced by map.yaml

Run navigation with a custom map:

ros2 launch my_robot_bringup all.launch.py map:=/absolute/path/to/map.yaml

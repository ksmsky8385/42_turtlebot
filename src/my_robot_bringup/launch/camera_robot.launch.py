import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    tb3_launch_dir = os.path.join(get_package_share_directory('turtlebot3_bringup'), 'launch')

    turtlebot3_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([tb3_launch_dir, '/robot.launch.py'])
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy',
        output='screen',
        parameters=[{
            'require_enable_button': False,
            'axis_linear.x': 1,
            'axis_angular.yaw': 0,
            'scale_linear.x': 0.20,
            'scale_angular.yaw': 2.0,
        }]
    )

    return LaunchDescription([
        turtlebot3_bringup,
        joy_node,
        teleop_node,
    ])

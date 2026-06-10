import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    slam_dir = get_package_share_directory('slam_toolbox')
    package_dir = get_package_share_directory('my_robot_bringup')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock'),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(package_dir, 'config', 'slam_toolbox.yaml'),
            description='Full path to SLAM Toolbox parameters'),
        Node(
            package='my_robot_bringup',
            executable='scan_normalizer',
            name='scan_normalizer',
            output='screen',
            parameters=[{
                'input_topic': '/scan',
                'output_topic': '/scan_fixed',
                'fixed_count': 0,
            }],
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(slam_dir, 'launch', 'online_async_launch.py')
            ),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'slam_params_file': LaunchConfiguration('slam_params_file'),
            }.items(),
        ),
    ])

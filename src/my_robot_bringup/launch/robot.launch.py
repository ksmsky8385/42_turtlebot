import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_camera = LaunchConfiguration('use_camera')
    use_joy = LaunchConfiguration('use_joy')
    use_ld08 = LaunchConfiguration('use_ld08')
    use_twist_mux = LaunchConfiguration('use_twist_mux')

    # 1. 터틀봇3 Bringup 기본 모터 구동 런치
    tb3_launch_dir = os.path.join(get_package_share_directory('turtlebot3_bringup'), 'launch')
    turtlebot3_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([tb3_launch_dir, '/robot.launch.py'])
    )

    bringup_launch_dir = os.path.join(get_package_share_directory('my_robot_bringup'), 'launch')
    joy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([bringup_launch_dir, '/joy.launch.py']),
        condition=IfCondition(use_joy),
    )
    twist_mux_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([bringup_launch_dir, '/twist_mux.launch.py']),
        condition=IfCondition(use_twist_mux),
    )

    # 2. 라이다 노드 강제 포함 (분리되어 있을 경우를 대비)
    # LDS-02 기본 드라이버 기준 (본인 라이다 패키지명에 맞춰 변경 가능)
    # ld_lidar_node = Node(
    #     package='ld08_driver',  # 또는 hls_lfcd_lds_driver
    #     executable='ld08_driver',
    #     name='ld08_driver',
    #     output='screen',
    #     condition=IfCondition(use_ld08),
    #     parameters=[{
    #         'port_name': '/dev/ttyUSB0', # 라이다가 꽂힌 포트 고정
    #         'frame_id': 'base_scan'
    #     }]
    # )

    camera_node = Node(
        package='my_robot_bringup',
        executable='camera_pub',
        name='camera_image_publisher',
        output='screen',
        condition=IfCondition(use_camera),
        parameters=[{
            'publish_rate': 10.0,
            'topic_name': 'image_raw',
            'image_size': [320, 240],
            'camera_index': 0,
            'frame_id': 'camera_link',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_camera',
            default_value='true',
            description='Start camera image publisher'),
        DeclareLaunchArgument(
            'use_joy',
            default_value='true',
            description='Start joy_node and teleop_twist_joy'),
        DeclareLaunchArgument(
            'use_ld08',
            default_value='false',
            description='Start standalone LD08 lidar driver. Keep false when turtlebot3_bringup already starts the lidar.'),
        DeclareLaunchArgument(
            'use_twist_mux',
            default_value='true',
            description='Start twist_mux for /cmd_vel arbitration'),
        turtlebot3_bringup,
        # ld_lidar_node, # 라이다 노드 추가
        camera_node,
        joy_launch,
        twist_mux_launch,
        ])

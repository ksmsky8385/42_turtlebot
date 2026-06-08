import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 터틀봇3 Bringup 기본 모터 구동 런처
    tb3_launch_dir = os.path.join(get_package_share_directory('turtlebot3_bringup'), 'launch')
    turtlebot3_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([tb3_launch_dir, '/robot.launch.py'])
    )

    # 2. 라이다 노드 강제 포함 (분리되어 있을 경우를 대비)
    # LDS-02 기본 드라이버 기준 (본인 라이다 패키지명에 맞춰 변경 가능)
    ld_lidar_node = Node(
        package='ld08_driver',  # 또는 hls_lfcd_lds_driver
        executable='ld08_driver',
        name='ld08_driver',
        output='screen',
        parameters=[{
            'port_name': '/dev/ttyUSB0', # 라이다가 꽂힌 포트 고정
            'frame_id': 'base_scan'
        }]
    )

    return LaunchDescription([
        turtlebot3_bringup,
        ld_lidar_node, # 라이다 노드 추가
        ])

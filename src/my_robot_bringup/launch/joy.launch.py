from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_node',
        output='screen',
        remappings=[
            ('/cmd_vel', '/cmd_vel_joy'),
        ],
        parameters=[{
            'require_enable_button': False,
            'axis_linear': {
                'x': 1,
            },
            'axis_angular': {
                'yaw': 0,
            },
            'scale_linear': {
                'x': 0.20,
            },
            'scale_angular': {
                'yaw': 2.0,
            },
        }]
    )

    joy_nav_controller = Node(
        package='my_robot_bringup',
        executable='joy_nav_controller',
        name='joy_nav_controller',
        output='screen',
        parameters=[{
            'toggle_button': 9,
            'fall_center_deadband': 0.12,
            'fall_angular_gain': 0.8,
            'fall_max_angular_speed': 0.45,
            'fall_target_timeout': 0.6,
        }],
    )

    return LaunchDescription([
        joy_node,
        teleop_node,
        joy_nav_controller,
    ])

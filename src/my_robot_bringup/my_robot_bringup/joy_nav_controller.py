import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, Float32MultiArray


class JoyNavController(Node):
    def __init__(self):
        super().__init__('joy_nav_controller')

        self.declare_parameter('toggle_button', 9)
        self.declare_parameter('fall_center_deadband', 0.12)
        self.declare_parameter('fall_angular_gain', 0.8)
        self.declare_parameter('fall_max_angular_speed', 0.45)
        self.declare_parameter('fall_target_timeout', 0.6)
        self._toggle_btn = int(self.get_parameter('toggle_button').value)
        self._fall_center_deadband = float(
            self.get_parameter('fall_center_deadband').value)
        self._fall_angular_gain = float(
            self.get_parameter('fall_angular_gain').value)
        self._fall_max_angular_speed = float(
            self.get_parameter('fall_max_angular_speed').value)
        self._fall_target_timeout = float(
            self.get_parameter('fall_target_timeout').value)

        # True = nav 잠금(중지), False = nav 허용(주행)
        self._nav_locked = False
        self._lock_reason = None
        self._prev_btn = 0
        self._warned_button_range = False
        self._fall_tracking = False
        self._fall_suppressed = False
        self._fall_error_x = 0.0
        self._last_fall_target_time = None

        self._lock_pub = self.create_publisher(Bool, '/manual_override_lock', 1)
        self._fall_cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel_fall_follow',
            10,
        )
        self.create_subscription(Joy, '/joy', self._joy_callback, 10)
        self.create_subscription(
            Float32MultiArray,
            '/fall_target',
            self._fall_target_callback,
            10,
        )
        self.create_timer(0.1, self._fall_control_timer)

        self.get_logger().info(
            f'JoyNavController ready - button {self._toggle_btn} toggles nav'
        )

    def _joy_callback(self, msg: Joy):
        if self._toggle_btn >= len(msg.buttons):
            if not self._warned_button_range:
                self.get_logger().warn(
                    f'Joy message has {len(msg.buttons)} buttons, '
                    f'but toggle_button is {self._toggle_btn}'
                )
                self._warned_button_range = True
            return

        self._warned_button_range = False
        cur_btn = msg.buttons[self._toggle_btn]
        if cur_btn == 1 and self._prev_btn == 0:  # 상승 에지만 감지
            self._toggle_nav_lock()

        self._prev_btn = cur_btn

    def _toggle_nav_lock(self):
        was_fall_tracking = self._fall_tracking

        self._nav_locked = not self._nav_locked
        self._lock_pub.publish(Bool(data=self._nav_locked))

        if not self._nav_locked:
            self._stop_fall_rotation()
            self._lock_reason = None
            if was_fall_tracking:
                self._fall_suppressed = True
                self.get_logger().info(
                    'Fall target ignored until it leaves the camera view'
                )
        else:
            self._lock_reason = 'manual'
            self._fall_suppressed = False

        state = 'STOPPED' if self._nav_locked else 'RUNNING'
        self.get_logger().info(f'Nav autonomy {state}')

    def _fall_target_callback(self, msg: Float32MultiArray):
        if not msg.data:
            return

        self._last_fall_target_time = self.get_clock().now()
        if self._fall_suppressed:
            return

        if self._nav_locked and self._lock_reason != 'fall':
            return

        self._fall_error_x = max(-1.0, min(1.0, float(msg.data[0])))

        if not self._nav_locked:
            self._nav_locked = True
            self._lock_reason = 'fall'
            self._lock_pub.publish(Bool(data=True))
            self.get_logger().warn(
                'Fall target detected - nav stopped, centering camera angle'
            )

        self._fall_tracking = True

    def _fall_control_timer(self):
        if self._last_fall_target_time is None:
            return

        now = self.get_clock().now()
        age = (now - self._last_fall_target_time).nanoseconds / 1e9

        if age > self._fall_target_timeout:
            if self._fall_tracking:
                self._stop_fall_rotation()
            self._fall_suppressed = False
            return

        if not self._fall_tracking:
            return

        cmd = Twist()
        if abs(self._fall_error_x) > self._fall_center_deadband:
            angular = -self._fall_angular_gain * self._fall_error_x
            cmd.angular.z = max(
                -self._fall_max_angular_speed,
                min(self._fall_max_angular_speed, angular),
            )
        self._fall_cmd_pub.publish(cmd)

    def _stop_fall_rotation(self):
        self._fall_tracking = False
        self._fall_error_x = 0.0
        self._fall_cmd_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = JoyNavController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

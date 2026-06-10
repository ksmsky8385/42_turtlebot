import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool


class JoyNavController(Node):
    def __init__(self):
        super().__init__('joy_nav_controller')

        self.declare_parameter('toggle_button', 9)
        self._toggle_btn = int(self.get_parameter('toggle_button').value)

        # True = nav 잠금(중지), False = nav 허용(주행)
        self._nav_locked = False
        self._prev_btn = 0
        self._warned_button_range = False

        self._lock_pub = self.create_publisher(Bool, '/manual_override_lock', 1)
        self.create_subscription(Joy, '/joy', self._joy_callback, 10)

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
            self._nav_locked = not self._nav_locked
            self._lock_pub.publish(Bool(data=self._nav_locked))
            state = 'STOPPED' if self._nav_locked else 'RUNNING'
            self.get_logger().info(f'Nav autonomy {state}')

        self._prev_btn = cur_btn


def main(args=None):
    rclpy.init(args=args)
    node = JoyNavController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

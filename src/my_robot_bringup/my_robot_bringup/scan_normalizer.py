import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanNormalizer(Node):
    def __init__(self):
        super().__init__('scan_normalizer')

        self.declare_parameter('input_topic', '/scan')
        self.declare_parameter('output_topic', '/scan_fixed')
        self.declare_parameter('fixed_count', 0)

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self._fixed_count = int(self.get_parameter('fixed_count').value)

        self._angle_min = None
        self._angle_max = None
        self._angle_increment = None

        self._pub = self.create_publisher(LaserScan, output_topic, 10)
        self.create_subscription(LaserScan, input_topic, self._scan_callback, 10)

        self.get_logger().info(
            f'Normalizing {input_topic} into fixed-size {output_topic}'
        )

    def _initialize_grid(self, msg):
        if self._fixed_count <= 0:
            self._fixed_count = len(msg.ranges)

        self._angle_min = msg.angle_min
        self._angle_max = msg.angle_max
        if self._fixed_count > 1:
            self._angle_increment = (
                self._angle_max - self._angle_min
            ) / float(self._fixed_count - 1)
        else:
            self._angle_increment = msg.angle_increment

        self.get_logger().info(
            'Fixed scan grid: '
            f'count={self._fixed_count}, '
            f'angle_min={self._angle_min:.3f}, '
            f'angle_max={self._angle_max:.3f}, '
            f'angle_increment={self._angle_increment:.6f}'
        )

    def _scan_callback(self, msg):
        if not msg.ranges:
            return

        if self._angle_min is None:
            self._initialize_grid(msg)

        fixed_ranges = [math.inf] * self._fixed_count
        fixed_intensities = [0.0] * self._fixed_count

        for i, scan_range in enumerate(msg.ranges):
            angle = msg.angle_min + (i * msg.angle_increment)
            index = round((angle - self._angle_min) / self._angle_increment)

            if index < 0 or index >= self._fixed_count:
                continue

            if not math.isfinite(scan_range):
                continue

            if scan_range < msg.range_min or scan_range > msg.range_max:
                continue

            if scan_range < fixed_ranges[index]:
                fixed_ranges[index] = scan_range
                if i < len(msg.intensities):
                    fixed_intensities[index] = msg.intensities[i]

        fixed_msg = LaserScan()
        fixed_msg.header = msg.header
        fixed_msg.angle_min = self._angle_min
        fixed_msg.angle_max = self._angle_max
        fixed_msg.angle_increment = self._angle_increment
        fixed_msg.time_increment = msg.time_increment
        fixed_msg.scan_time = msg.scan_time
        fixed_msg.range_min = msg.range_min
        fixed_msg.range_max = msg.range_max
        fixed_msg.ranges = fixed_ranges
        fixed_msg.intensities = fixed_intensities

        self._pub.publish(fixed_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ScanNormalizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

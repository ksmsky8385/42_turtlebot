import cv2
import rclpy
from cv_bridge import CvBridge
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImagePublisher(Node):
    def __init__(self):
        super().__init__('image_publisher')
        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('topic_name', 'image_raw')
        self.declare_parameter('image_size', [320, 240])
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('frame_id', 'camera_link')

        self.rate = self.get_parameter('publish_rate').value
        self.topic = self.get_parameter('topic_name').value
        self.size = self.get_parameter('image_size').value
        self.camera_index = self.get_parameter('camera_index').value
        self.frame_id = self.get_parameter('frame_id').value

        self.add_on_set_parameters_callback(self.parameter_callback)

        self.publisher_ = self.create_publisher(Image, self.topic, 10)
        self.timer = self.create_timer(1.0 / self.rate, self.timer_callback)
        self.cap = cv2.VideoCapture(self.camera_index)
        self.bridge = CvBridge()

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'publish_rate':
                self.rate = param.value
                self.timer.cancel()
                self.timer = self.create_timer(1.0 / self.rate, self.timer_callback)
                self.get_logger().info(f'publish_rate={self.rate}Hz')
            elif param.name == 'image_size':
                self.size = param.value
                self.get_logger().info(f'image_size={self.size}')
            elif param.name == 'frame_id':
                self.frame_id = param.value
                self.get_logger().info(f'frame_id={self.frame_id}')
        return SetParametersResult(successful=True)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        resized = cv2.resize(frame, tuple(self.size))
        img_msg = self.bridge.cv2_to_imgmsg(resized, encoding='bgr8')
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = self.frame_id
        self.publisher_.publish(img_msg)

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ImagePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

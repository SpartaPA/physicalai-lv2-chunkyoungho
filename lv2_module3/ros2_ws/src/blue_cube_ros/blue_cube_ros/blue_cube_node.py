"""튜터 예제 blue_cube_reference.detect_blue()를 그대로 호출하는 최소 ROS 2 래퍼.

  Raw Image 구독 -> detect_blue(frame) -> Mask(mono8)·Overlay(bgr8)·검출(Detection2DArray) 발행
검출 알고리즘(HSV inRange -> open·close -> findContours -> MIN_AREA 필터)은 blue_cube_reference.py에만 있고,
이 파일은 ROS 메시지 변환과 발행만 한다.

설정값: blue_cube_reference.py의 모듈 상수 LOWER_BLUE·UPPER_BLUE·MIN_AREA를 노드 시작 시 ROS 파라미터 값으로 덮어쓴다.
detect_blue()는 호출할 때마다 모듈 상수를 읽으므로 덮어쓴 값이 그대로 적용된다.
파라미터는 시작 시 한 번만 읽는다 -> 값을 바꾸면 노드를 재시작한다.
"""
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray

from blue_cube_ros import blue_cube_reference as ref


class BlueCubeNode(Node):
    def __init__(self):
        super().__init__('blue_cube_detector')
        # 기본값 = blue_cube_reference.py의 상수 값
        image_topic = self.declare_parameter('image_topic', '/camera/camera/color/image_raw').value
        lower = self.declare_parameter('lower_hsv', ref.LOWER_BLUE.tolist()).value
        upper = self.declare_parameter('upper_hsv', ref.UPPER_BLUE.tolist()).value
        min_area = self.declare_parameter('min_area', float(ref.MIN_AREA)).value

        ref.LOWER_BLUE = np.array(lower, dtype=np.uint8)
        ref.UPPER_BLUE = np.array(upper, dtype=np.uint8)
        ref.MIN_AREA = float(min_area)

        self.bridge = CvBridge()
        self.frame_count = 0
        self.mask_pub = self.create_publisher(Image, '~/mask', 10)
        self.overlay_pub = self.create_publisher(Image, '~/overlay', 10)
        self.det_pub = self.create_publisher(Detection2DArray, '~/detections', 10)
        # 카메라·bag 재생 Image는 보통 best-effort라 sensor QoS로 구독한다
        self.create_subscription(Image, image_topic, self.on_image, qos_profile_sensor_data)
        # 실제 적용값 기록 (보고서의 '적용 확인' 근거)
        self.get_logger().info(
            f'applied: image_topic={image_topic} LOWER_BLUE={ref.LOWER_BLUE.tolist()} '
            f'UPPER_BLUE={ref.UPPER_BLUE.tolist()} MIN_AREA={ref.MIN_AREA}')

    def on_image(self, msg):
        # detect_blue()는 BGR 배열을 가정한다. rgb8 입력(RealSense ROS·bag)도 bgr8로 변환해 넘긴다
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        result, mask, boxes = ref.detect_blue(frame)

        # 출력 header = 입력 header: 같은 stamp로 Raw·Mask·검출을 같은 프레임으로 묶는다
        mask_msg = self.bridge.cv2_to_imgmsg(mask, encoding='mono8')
        mask_msg.header = msg.header
        self.mask_pub.publish(mask_msg)
        overlay_msg = self.bridge.cv2_to_imgmsg(result, encoding='bgr8')
        overlay_msg.header = msg.header
        self.overlay_pub.publish(overlay_msg)

        det = Detection2DArray()
        det.header = msg.header
        for i, (x, y, w, h) in enumerate(boxes):   # boundingRect: 왼쪽 위 (x, y), 폭 w, 높이 h [px]
            d = Detection2D()
            d.header = msg.header
            d.id = str(i)
            d.bbox.center.position.x = x + (w - 1) / 2.0   # 박스 중심 [px], 원본 해상도 기준
            d.bbox.center.position.y = y + (h - 1) / 2.0
            d.bbox.size_x = float(w)
            d.bbox.size_y = float(h)
            det.detections.append(d)
        self.det_pub.publish(det)                  # 미검출이면 detections: [] 를 그대로 발행

        self.frame_count += 1
        if self.frame_count % 30 == 1:
            self.get_logger().info(
                f'frame={self.frame_count} stamp={msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d} '
                f'{msg.width}x{msg.height} {msg.encoding} boxes={boxes}')


def main(args=None):
    rclpy.init(args=args)
    node = BlueCubeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

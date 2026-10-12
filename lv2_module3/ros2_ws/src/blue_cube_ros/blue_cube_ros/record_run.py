"""실험 A·B 비교용 기록: blue_cube_detector가 발행한 토픽을 구독해 stamp별로 저장한다 (검출 노드와 별도 실행).

bag 재생은 프레임이 계속 바뀌므로, 출력 header.stamp(= 입력 Raw stamp)를 기준으로 A·B를 맞춘다.

  ros2 run blue_cube_ros record_run --out results/exp1/A --prefix exp1_A --snap 1791784737.984 [--duration 15]

저장 (<out>/):
  <prefix>_detections.csv   stamp, 박스 수, 박스 목록(cx;cy;w;h), Mask 픽셀 수 — 토픽에서 받은 값 그대로
  <prefix>_summary.json     노드에 실제 적용된 파라미터, 받은 프레임 수, 박스 수 분포, Mask 픽셀 수 통계
  <prefix>_detections_sample.yaml  검출 메시지 1개 원문 (필드 확인용)
  <prefix>_{raw,mask,overlay}_<stamp>.png   --snap으로 지정한 stamp의 세 토픽 이미지
"""
import argparse
import collections
import csv
import json
import os
import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rcl_interfaces.srv import GetParameters
from rclpy.parameter import parameter_value_to_python
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rosidl_runtime_py import message_to_yaml
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray

NODE = '/blue_cube_detector'
PARAMS = ['image_topic', 'lower_hsv', 'upper_hsv', 'min_area']


def stamp_key(header):
    """header.stamp -> 'sec.msec' 문자열 (파일 이름·CSV 공통 키)."""
    return f'{header.stamp.sec}.{header.stamp.nanosec // 1_000_000:03d}'


def get_params(node, timeout=3.0):
    """검출 노드에 실제 적용된 파라미터를 서비스로 읽는다 (파일 값이 아니라 실행 중인 값)."""
    cli = node.create_client(GetParameters, f'{NODE}/get_parameters')
    if not cli.wait_for_service(timeout_sec=timeout):
        return None
    fut = cli.call_async(GetParameters.Request(names=PARAMS))
    rclpy.spin_until_future_complete(node, fut, timeout_sec=timeout)
    if not fut.done() or fut.result() is None:
        return None
    return {n: (list(v) if isinstance(v, (list, tuple, np.ndarray)) else v)
            for n, v in zip(PARAMS, (parameter_value_to_python(p) for p in fut.result().values))}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--out', required=True, help='저장 폴더 (예: results/exp1/A)')
    p.add_argument('--prefix', required=True, help='파일 이름 앞부분 (예: exp1_A)')
    p.add_argument('--duration', type=float, default=15.0, help='[s] 기록 시간. bag 한 바퀴(약 11.6 s)보다 길게')
    p.add_argument('--snap', nargs='*', default=[], help='Raw·Mask·Overlay를 저장할 stamp (sec.msec)')
    p.add_argument('--raw-topic', default='/camera/camera/color/image_raw')
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    out = lambda name: os.path.join(a.out, f'{a.prefix}_{name}')  # noqa: E731

    rclpy.init()
    node = rclpy.create_node('record_run')
    br = CvBridge()
    det, mask_px, sample, saved = {}, {}, [], set()
    snaps = set(a.snap)

    def save(kind, msg, encoding):
        key = stamp_key(msg.header)
        if key in snaps and (kind, key) not in saved:
            cv2.imwrite(out(f'{kind}_{key}.png'), br.imgmsg_to_cv2(msg, encoding))
            saved.add((kind, key))
        return key

    def on_mask(msg):
        key = save('mask', msg, 'mono8')
        mask_px[key] = int(np.count_nonzero(br.imgmsg_to_cv2(msg, 'mono8')))

    def on_det(msg):
        key = stamp_key(msg.header)
        det[key] = [(d.bbox.center.position.x, d.bbox.center.position.y, d.bbox.size_x, d.bbox.size_y)
                    for d in msg.detections]
        if not sample:
            sample.append(message_to_yaml(msg))

    reliable = QoSProfile(depth=100, reliability=ReliabilityPolicy.RELIABLE)
    node.create_subscription(Image, a.raw_topic, lambda m: save('raw', m, 'bgr8'), qos_profile_sensor_data)
    node.create_subscription(Image, f'{NODE}/mask', on_mask, qos_profile_sensor_data)
    node.create_subscription(Image, f'{NODE}/overlay', lambda m: save('overlay', m, 'bgr8'), qos_profile_sensor_data)
    node.create_subscription(Detection2DArray, f'{NODE}/detections', on_det, reliable)

    params = get_params(node)
    end = time.monotonic() + a.duration
    while rclpy.ok() and time.monotonic() < end:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()

    keys = sorted(det, key=float)
    with open(out('detections.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['stamp', 'n_boxes', 'boxes_cx;cy;w;h', 'mask_px'])
        for k in keys:
            w.writerow([k, len(det[k]), ' '.join(f'{cx:.1f};{cy:.1f};{bw:.0f};{bh:.0f}' for cx, cy, bw, bh in det[k]),
                        mask_px.get(k, '')])
    if sample:
        with open(out('detections_sample.yaml'), 'w', encoding='utf-8') as f:
            f.write(sample[0])
    px = np.array([v for k, v in mask_px.items() if k in det] or [0])
    summary = {
        'applied_params': params,
        'frames': len(keys),
        'boxes_per_frame_hist': dict(sorted(collections.Counter(len(det[k]) for k in keys).items())),
        'mask_px': {'min': int(px.min()), 'median': float(np.median(px)), 'max': int(px.max())},
        'snapshots': sorted(f'{kind}_{k}' for kind, k in saved),
        'snap_missing': sorted(set(a.snap) - {k for _, k in saved}),
    }
    with open(out('summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()

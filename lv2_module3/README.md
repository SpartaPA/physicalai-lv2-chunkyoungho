# 모듈 3 과제 — 설정값에 따른 Mask와 검출 결과 변화

- 작성자: 천경호
- 보고서: [report.md](report.md)
- 결과: [results/](results/)
- 코드: 수업 코드를 이용했습니다.

## 1. 입력

입력은 두 가지이며 용도가 다릅니다.

| 입력 | 내용 | 용도 |
|---|---|---|
| **분석용** rosbag | D435로 직접 녹화한 bag을 `ros2 bag play --loop`로 재생 ([results/input/](results/input/)) | **설정값 변경에 따른 Mask·검출 변화 검증과 분석(보고서)**. 같은 bag이면 A·B에 프레임(stamp)별로 같은 입력이 들어감 |
| **실시간** Camera | `realsense2_camera`로 D435 영상을 실시간 발행 | 같은 노드·설정이 실제 카메라 토픽에서도 동작함을 확인. 분석 수치에는 쓰지 않음 |

## 2. 처리 흐름과 토픽

```
[분석용] ros2 bag play    → /camera/camera/color/image_raw  (sensor_msgs/Image, rgb8 640x480, 30 Hz)
[실시간] /camera/camera   → /camera/camera/color/image_raw  (sensor_msgs/Image, rgb8 640x480, 30 Hz)
  └─ blue_cube_detector
       ├─ cv_bridge: rgb8 → bgr8
       └─ detect_blue(frame)
            HSV 변환 → inRange(LOWER_BLUE, UPPER_BLUE) → open·close(5x5)
            → findContours → contourArea >= MIN_AREA → boundingRect
       ├─ /blue_cube_detector/mask        sensor_msgs/Image mono8 (open·close 후 마스크, 255 = 범위 안)
       ├─ /blue_cube_detector/overlay     sensor_msgs/Image bgr8  (초록 박스 + 'BLUE')
       └─ /blue_cube_detector/detections  vision_msgs/Detection2DArray
```

- 세 출력의 `header`는 입력 Raw Image의 `header`를 그대로 씁니다. 같은 `stamp`로 같은 프레임인지 확인할 수 있습니다.
- bag 재생은 녹화된 메시지를 그대로 다시 발행하므로 `header.stamp`도 촬영 시각 그대로입니다. 그래서 A·B 결과를 같은 stamp끼리 비교합니다.
- `detections[i].bbox`: `center.position.x/y` = 박스 중심 [px], `size_x/size_y` = 폭·높이 [px], 원본 해상도 기준입니다. `results`(클래스·점수)는 비워 둡니다. `detect_blue()`가 박스만 반환하기 때문입니다.
- 미검출이면 `detections: []`를 매 프레임 발행합니다.

## 3. 실행 환경

| 항목 | 값 |
|---|---|
| OS | Ubuntu 24.04.5 LTS (PC) |
| ROS 2 | Lyrical, RMW `rmw_fastrtps_cpp`(기본값) |
| Python | 3.12.3 |
| OpenCV | 4.6.0 (Ubuntu `python3-opencv`) |
| NumPy | 1.26.4 |
| 의존 패키지 | `cv_bridge`, `vision_msgs`, `rqt_image_view`, `ros2bag`(mcap) |
| Camera 드라이버 | `ros-lyrical-realsense2-camera` 4.57.7, `ros-lyrical-librealsense2` 2.57.7 |
| Camera | Intel RealSense D435, 펌웨어 5.15.1.55, USB 3.2 연결 |

## 4. 설정값

설정값은 ROS 2 파라미터입니다. 노드는 시작할 때 이 값으로 `detect_blue()`가 쓰는 상수를 덮어쓰고, `detect_blue()`는 호출될 때마다 이 상수를 읽습니다. 파라미터는 시작 시 한 번만 읽으므로 값을 바꾸면 노드를 재시작합니다.

| 파라미터 | 덮어쓰는 상수 | 기본값(= 원본 상수) | 쓰이는 곳 |
|---|---|---|---|
| `lower_hsv` | `LOWER_BLUE` | `[95, 80, 50]` | `cv2.inRange` 하한 (Mask 생성) |
| `upper_hsv` | `UPPER_BLUE` | `[130, 255, 255]` | `cv2.inRange` 상한 (Mask 생성) |
| `min_area` | `MIN_AREA` | `500.0` [px²] | `cv2.contourArea(c) >= MIN_AREA` (검출 후보 필터) |
| `bag_play.uri` | — | — | 분석용 입력으로 재생할 bag |
| `bag_play.loop`, `bag_play.start_offset` | — | `true`, `0.0` [s] | 반복 재생, 앞부분 건너뛰기 |

- 실험마다 설정 파일(`results/expN/{A,B}/params.yaml`)을 두고, 같은 bag으로 검출 설정 **값 하나만** 바꿉니다.
- 노드 시작 로그의 `applied: ... LOWER_BLUE=[...] UPPER_BLUE=[...] MIN_AREA=...` 줄로 실제 적용값을 확인하고 저장합니다.

## 5. 결과 파일 위치

| 경로 | 내용 |
|---|---|
| `results/input/` | 분석용 bag의 `ros2 bag info` 출력과 장면 설명 |
| `results/topics/` | `ros2 topic list -t`, `ros2 topic info --verbose`, `ros2 interface show` 출력 |
| `results/exp1/{A,B}/` | 실험 1(Mask 생성) A·B: `params.yaml`, stamp별 검출·Mask 픽셀 수(CSV), 적용 파라미터·요약(JSON), 지정 stamp의 Raw·Mask·Overlay |
| `results/exp2/{A,B}/` | 실험 2(검출 후보 필터) A·B: 위와 같은 구성 |
| `results/no_target/` | 목표 없음 입력: Mask 캡처, `detections: []` 수신 로그 |

파일 이름에는 실험 번호·A/B·토픽·stamp를 넣습니다. 예: `exp1_B_mask_1791784737.984.png`

## 6. 확인 시험 (2026-10-12)

처음에는 합성 영상(회색 배경 + 파란 사각형 100×80 1개, 20×20 1개, rgb8 10 Hz)으로 노드 동작을 확인했습니다.

- `/blue_cube_detector/mask` 10.0 Hz 수신, encoding `mono8`. `overlay`는 `bgr8`
- `min_area: 500`: 박스 `(100,100,100,80)` 1개만 검출. 20×20(면적 361)은 제외
- `min_area: 300`: 20×20도 검출되어 2개. 파라미터가 적용된 것을 확인
- 파란색이 없는 입력: `detections: []`

실시간 Camera 입력도 확인했습니다.

- 실시간: `/camera/camera/color/image_raw`(rgb8) → Mask 약 30 Hz 수신

# 모듈 3 과제 — 설정값에 따른 Mask와 검출 결과 변화

- 작성자: 천경호
- 보고서: [report.md](report.md)
- 결과: [results/](results/)
- 코드: 수업 코드를 이용했습니다 (출처는 1절).

## 1. 코드 출처

| 구분 | 파일 (`ros2_ws/src/blue_cube_ros/` 기준) | 출처 |
|---|---|---|
| 검출 알고리즘 | [`blue_cube_ros/blue_cube_reference.py`](ros2_ws/src/blue_cube_ros/blue_cube_ros/blue_cube_reference.py) | **수업 코드**(19강 HSV·Contour 예제 `detect_blue()`)를 수정 없이 복사 |
| ROS 2 노드 | [`blue_cube_ros/blue_cube_node.py`](ros2_ws/src/blue_cube_ros/blue_cube_ros/blue_cube_node.py) | 직접 작성. Raw Image를 구독해 `detect_blue()`를 그대로 호출하고, Mask·Overlay·검출 결과를 토픽으로 발행만 함 |
| 기록 도구 | [`blue_cube_ros/record_run.py`](ros2_ws/src/blue_cube_ros/blue_cube_ros/record_run.py) | 직접 작성. 검출 노드의 출력 토픽을 구독해 stamp별로 저장 (6절) |
| 실행·설정 | [`launch/blue_cube.launch.py`](ros2_ws/src/blue_cube_ros/launch/blue_cube.launch.py), [`config/blue_cube.yaml`](ros2_ws/src/blue_cube_ros/config/blue_cube.yaml), [`config/fastdds_shm.xml`](ros2_ws/src/blue_cube_ros/config/fastdds_shm.xml) | 직접 작성 |

수업 코드는 OpenCV 창(`imshow`)으로만 결과를 보여 주고 ROS 토픽을 발행하지 않습니다. 과제는 Mask·검출 결과를 토픽으로 받아야 하므로, **알고리즘은 그대로 두고 발행만 하는 노드**로 감쌌습니다.

## 2. 입력

입력은 두 가지이며 용도가 다릅니다.

| 입력 | 내용 | 용도 |
|---|---|---|
| **분석용** rosbag | D435로 직접 녹화한 bag을 `ros2 bag play --loop`로 재생 ([results/input/](results/input/), 녹화 명령은 6-0) | **설정값 변경에 따른 Mask·검출 변화 검증과 분석(보고서)**. 같은 bag이면 A·B에 프레임(stamp)별로 같은 입력이 들어감 |
| **실시간** Camera | `realsense2_camera`로 D435 영상을 실시간 발행 | 같은 노드·설정이 실제 카메라 토픽에서도 동작함을 확인. 분석 수치에는 쓰지 않음 |

## 3. 처리 흐름과 토픽

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

- 세 출력의 `header`는 입력 Raw Image의 `header`를 그대로 씁니다. 같은 `stamp`로 같은 프레임인지 확인
- bag 재생은 녹화된 메시지를 그대로 다시 발행하므로 `header.stamp`도 촬영 시각 그대로입니다. 그래서 A·B 결과를 같은 stamp끼리 비교
- `detections[i].bbox`: `center.position.x/y` = 박스 중심 [px], `size_x/size_y` = 폭·높이 [px], 원본 해상도 기준
- `detections[i].results`(클래스 = 물체 종류, 점수 = 신뢰도)는 비워 둡니다. `detect_blue()`는 HSV 범위와 면적 조건을 통과한 chunk의 박스만 돌려 - 물체 종류를 판단하거나 신뢰도를 계산하지 않기 때문.
- 미검출이면 `detections: []`를 매 프레임 발행

**검출 결과에 `vision_msgs/msg/Detection2DArray`를 쓴 이유**

- **표준 형식:** `vision_msgs`는 물체 검출기의 출력을 주고받기 위한 ROS 커뮤니티 공통 메시지 패키지입니다(Apache 2.0, 이 환경에 4.2.0 설치). 별도의 메시지 패키지를 직접 만들 필요가 없슴.
- **한 프레임 = 한 메시지:** 한 프레임의 박스 여러 개를 `detections[]` 배열 하나에 담음. `header`로 입력 Raw Image와 같은 프레임임을 표시할 수 있어, A·B 결과를 stamp끼리 맞춰 비교하기 좋음
- **미검출 표현:** 박스가 없으면 빈 배열(`detections: []`)로 나타내어 "검출 없음"과 "메시지가 안 옴"을 구분할 수 있음
- **필드 의미가 정해져 있음:** 박스 중심·크기(`bbox`)의 이름과 단위가 메시지 정의에 정해져 있어 `ros2 topic echo`·`ros2 interface show`로 바로 읽을 수 있음.


## 4. 실행 환경

| 항목 | 값 |
|---|---|
| OS | Ubuntu 24.04.5 LTS (PC) |
| ROS 2 | Lyrical |
| Python | 3.12.3 |
| OpenCV | 4.6.0 (Ubuntu `python3-opencv`) |
| NumPy | 1.26.4 |
| 의존 패키지 | `cv_bridge`, `vision_msgs`, `rqt_image_view`, `ros2bag`(mcap) |
| Camera 드라이버 | `ros-lyrical-realsense2-camera` 4.57.7, `ros-lyrical-librealsense2` 2.57.7 |
| Camera | Intel RealSense D435, 펌웨어 5.15.1.55, USB 3.2 연결 |

## 5. 설정값

설정값은 ROS 2 파라미터입니다. 노드는 시작할 때 이 값으로 `detect_blue()`가 쓰는 상수를 덮어쓰고, `detect_blue()`는 호출될 때마다 이 상수를 읽습니다. 파라미터는 시작 시 한 번만 읽으므로 값을 바꾸면 노드를 재시작합니다.

| 파라미터 | 상수 | 기본값 | 쓰이는 곳 |
|---|---|---|---|
| `lower_hsv` | `LOWER_BLUE` | `[95, 80, 50]` | `cv2.inRange` 하한 (Mask 생성) |
| `upper_hsv` | `UPPER_BLUE` | `[130, 255, 255]` | `cv2.inRange` 상한 (Mask 생성) |
| `min_area` | `MIN_AREA` | `500.0` [px²] | `cv2.contourArea(c) >= MIN_AREA` (검출 후보 필터) |
| `bag_play.uri` | — | `~/lv2_module3_bags/scene_target` | 분석용 입력으로 재생할 bag (상대 경로는 yaml 폴더 기준) |
| `bag_play.loop`, `bag_play.start_offset` | — | `true`, `0.0` [s] | 반복 재생, 앞부분 건너뛰기 |

- 실험마다 설정 파일(`results/expN/{A,B}/params.yaml`)을 두고, 같은 bag으로 검출 설정 서로 **값 하나만** 바꿉
- 노드 시작 로그의 `applied: ... LOWER_BLUE=[...] UPPER_BLUE=[...] MIN_AREA=...` 줄과 `record_run`의 `applied_params`로 실제 적용값을 확인합니다.

## 6. 실행 방법

아래에서 **`<clone 경로>`**는 이 저장소를 `git clone`으로 받은 폴더입니다(예: `~/git`). 실험 명령(6-1 ~ 6-4)은 모두 **`<clone 경로>/physicalai-lv2-chunkyoungho/lv2_module3/` 폴더**에서 실행합니다.

### 6-0. 공통 준비

**저장소 받기와 빌드** (한 번)

```bash
cd <clone 경로>
git clone https://github.com/SpartaPA/physicalai-lv2-chunkyoungho.git
cd physicalai-lv2-chunkyoungho/lv2_module3/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install
```

**모든 터미널에서 먼저 실행**

```bash
source /opt/ros/lyrical/setup.bash
source <clone 경로>/physicalai-lv2-chunkyoungho/lv2_module3/ros2_ws/install/setup.bash
# FastDDS(이 PC의 기본 RMW) 설정 파일 지정: 같은 PC 안 노드끼리 주고받는 공유 메모리를 16 MB로 키운다.
# 기본 공유 메모리(약 0.5 MB)보다 큰 640x480 이미지(약 0.9 MB)는 UDP 조각으로 나뉘어 전송되고,
# 카메라 영상처럼 best-effort로 받으면 조각 하나만 빠져도 프레임 전체가 버려져 영상이 거의 들어오지 않는다.
export FASTDDS_DEFAULT_PROFILES_FILE=$(ros2 pkg prefix blue_cube_ros)/share/blue_cube_ros/config/fastdds_shm.xml
```

> `FASTDDS_DEFAULT_PROFILES_FILE`을 쓰는 이유: 640×480 이미지(약 0.9 MB)가 FastDDS 기본 공유 메모리 세그먼트(약 0.5 MB)보다 큽니다. 그러면 이미지가 UDP 조각으로 나뉘어 전송되고, best-effort 구독에서 대부분 유실됩니다. 설정이 없을 때는 10 Hz로 발행해도 15초 동안 1프레임만 받았습니다. 발행·구독하는 **모든 터미널**에서 같은 값을 설정합니다.

이 세 줄을 `~/.bashrc` 맨 끝에 넣어 두면 새 터미널마다 자동으로 적용됩니다. 빌드한 뒤 이미 열려 있던 터미널은 닫고 새로 엽니다. 예전 환경이 남아 있으면 `PackageNotFoundError: No package metadata was found for blue-cube-ros` 같은 오류가 날 수 있습니다.

**실험 폴더로 이동**

```bash
cd <clone 경로>/physicalai-lv2-chunkyoungho/lv2_module3
```

**입력 bag 준비 (실제로 사용한 녹화 명령)**

bag 원본(각 약 300 MiB)은 저장소에 없습니다. 실험 설정 파일은 `~/lv2_module3_bags/scene_target`, `~/lv2_module3_bags/scene_no_target`을 가리킵니다. 실험에 쓴 bag은 아래 명령으로 녹화했습니다. 결과는 [results/input/](results/input/)에 있습니다.

```bash
# 터미널 1: 카메라 — 컬러만 640x480 30 Hz, 프레임마다 밝기가 바뀌지 않게 자동 노출을 끔
ros2 launch realsense2_camera rs_launch.py enable_depth:=false rgb_camera.color_profile:=640,480,30 rgb_camera.enable_auto_exposure:=false

# 터미널 2: 원통을 든 장면 약 12초 녹화 (ros2 bag record에는 시간 제한 옵션이 없어 timeout으로 SIGINT를 보내 정상 종료)
timeout -s INT 12 ros2 bag record --topics /camera/camera/color/image_raw /camera/camera/color/camera_info -o ~/lv2_module3_bags/scene_target

# 원통만 치우고 같은 자리에서 다시 녹화
timeout -s INT 12 ros2 bag record --topics /camera/camera/color/image_raw /camera/camera/color/camera_info -o ~/lv2_module3_bags/scene_no_target

# 확인: Raw 프레임 수 ≈ 길이(초) × 30
ros2 bag info ~/lv2_module3_bags/scene_target
```

- 압축 토픽(`.../compressed`)은 손실 압축이라 받지 않고, 원본 `image_raw`만 녹화. 저장 형식은 기본값 mcap.
- 녹화하는 터미널에도 위의 환경 설정(특히 `FASTDDS_DEFAULT_PROFILES_FILE`)이 필요. 없으면 이미지가 유실된 채로 녹화됨.

다른 위치의 bag을 쓰려면 설정 파일의 `bag_play.uri`를 고치거나, launch에 `bag:=<bag 폴더>`를 붙입니다(명령줄 값이 우선함).

**기록 도구 `record_run`** 

`record_run`은 검출 노드가 떠 있는 동안 함께 실행해 결과를 파일로 남김. 검출 처리에는 관여하지 않고 구독만 동작.

```bash
ros2 run blue_cube_ros record_run --out <저장 폴더> --prefix <파일 앞부분> [--snap <stamp> ...] [--duration 15]
```

| 옵션 | 의미 |
|---|---|
| `--out`, `--prefix` | 저장 폴더와 파일 이름 앞부분 (필수). 같은 값으로 다시 실행하면 덮어씀 |
| `--duration` | 기록 시간 [s], 기본 15. bag 한 바퀴(약 11.6 s)보다 길게 |
| `--snap` | Raw·Mask·Overlay 이미지를 저장할 stamp (`초.밀리초`, 밀리초 셋째 자리까지 버림). CSV의 `stamp` 열 값을 그대로 쓰면 정확함 |
| `--raw-topic` | Raw 토픽 이름, 기본 `/camera/camera/color/image_raw` |

| 저장 파일 | 내용 |
|---|---|
| `<prefix>_detections.csv` | 프레임(stamp)별 박스 수, 박스 `cx;cy;w;h`, Mask 흰 픽셀 수 |
| `<prefix>_summary.json` | 실행 중인 노드에서 읽은 실제 적용 파라미터, 받은 프레임 수, 박스 수 분포, Mask 픽셀 수 통계, 못 찾은 snap stamp |
| `<prefix>_detections_sample.yaml` | 검출 메시지 원문 1개 |
| `<prefix>_{raw,mask,overlay}_<stamp>.png` | `--snap` stamp의 토픽 이미지 |
| `<prefix>_frame_<stamp>.png` | 위 세 장을 한 장으로 합친 이미지 (토픽 이름·stamp·박스 수·Mask 픽셀 수 표시) |

검출 노드가 먼저 떠 있어야 합니다. 실행이 끝나면 요약 JSON의 `frames`가 bag 프레임 수(scene_target 349)와 같은지 확인합니다.

### 6-1. 실험 1 — Mask 생성 (V 하한 50 → 95)

설정: [results/exp1/A/params.yaml](results/exp1/A/params.yaml)(V 하한 50, 원본), [results/exp1/B/params.yaml](results/exp1/B/params.yaml)(V 하한 95). 다른 값은 동일.

```bash
# A — 터미널 1
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag params_file:=results/exp1/A/params.yaml
# A — 터미널 2 (노드가 뜨고 2~3초 뒤)
ros2 run blue_cube_ros record_run --out results/exp1/A --prefix exp1_A --snap 1791784737.984 --duration 15

# B — 터미널 1의 launch를 Ctrl+C로 끄고 다시 실행
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag params_file:=results/exp1/B/params.yaml
ros2 run blue_cube_ros record_run --out results/exp1/B --prefix exp1_B --snap 1791784737.984 --duration 15
```

### 6-2. 실험 2 — 검출 후보 필터 (min_area 500 → 100)

설정: [results/exp2/A/params.yaml](results/exp2/A/params.yaml)(min_area 500, 원본), [results/exp2/B/params.yaml](results/exp2/B/params.yaml)(min_area 100). HSV는 A·B 모두 `[95,80,80]~[130,255,255]`입니다.

```bash
# A
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag params_file:=results/exp2/A/params.yaml
ros2 run blue_cube_ros record_run --out results/exp2/A --prefix exp2_A --snap 1791784737.984 --duration 15

# B (launch를 끄고 다시 실행)
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag params_file:=results/exp2/B/params.yaml
ros2 run blue_cube_ros record_run --out results/exp2/B --prefix exp2_B --snap 1791784737.984 --duration 15
```

### 6-3. 목표 없음 확인 — 최종 선택 설정

설정: [results/no_target/params.yaml](results/no_target/params.yaml)(V 하한 95, min_area 500, `scene_no_target`, `start_offset 0.1`). 이 bag의 첫 프레임은 이전 장면이라 0.1초를 건너뛰기.

```bash
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag params_file:=results/no_target/params.yaml
ros2 run blue_cube_ros record_run --out results/no_target --prefix no_target --snap 1791784779.749 --duration 15
```

### 6-4. 토픽 정보

검출 노드를 실행한 상태에서 다른 터미널에서 실행합니다. `--no-daemon`은 이전 실행의 토픽 정보가 섞이지 않게 새로 조회하는 옵션.

```bash
ros2 launch blue_cube_ros blue_cube.launch.py source:=bag
ros2 topic list -t --no-daemon
ros2 topic info /blue_cube_detector/mask --verbose --no-daemon     # Raw·Overlay·detections도 같은 방식
ros2 topic hz /blue_cube_detector/mask --window 60
ros2 interface show vision_msgs/msg/Detection2DArray
```

### 6-5. 참고 — 실시간 Camera와 영상 확인

```bash
ros2 launch blue_cube_ros blue_cube.launch.py source:=camera      # realsense2_camera를 함께 띄움
ros2 run rqt_image_view rqt_image_view /blue_cube_detector/mask     # Raw·Overlay도 토픽 이름만 바꿔 확인
```

## 7. 결과 파일 위치

| 경로 | 내용 |
|---|---|
| `results/input/` | 분석용 bag의 `ros2 bag info` 출력, 장면 설명, 대표 프레임 stamp와 결과표 |
| `results/topics/` | `ros2 topic list -t`, `ros2 topic info --verbose`, `ros2 topic hz`, `ros2 interface show` 출력과 요약표 |
| `results/exp1/{A,B}/` | 실험 1(Mask 생성) A·B: `params.yaml`과 `record_run` 결과(CSV·JSON·YAML·대표 프레임 PNG) |
| `results/exp2/{A,B}/` | 실험 2(검출 후보 필터) A·B: 위와 같은 구성 |
| `results/no_target/` | 목표 없음 확인: `params.yaml`과 `record_run` 결과 (모든 프레임 `detections: []`) |

파일 이름에는 실험 번호·A/B·토픽·stamp를 넣음. 예: `exp1_B_mask_1791784737.984.png`

## 8. 확인 시험

처음에는 합성 영상(회색 배경 + 파란 사각형 100×80 1개, 20×20 1개, rgb8 10 Hz)으로 노드 동작을 확인했습니다.

- `/blue_cube_detector/mask` 10.0 Hz 수신, encoding `mono8`. `overlay`는 `bgr8`
- `min_area: 500`: 박스 `(100,100,100,80)` 1개만 검출. 20×20(면적 361)은 제외
- `min_area: 300`: 20×20도 검출되어 2개. 파라미터가 적용된 것을 확인
- 파란색이 없는 입력: `detections: []`

실시간 Camera 입력도 확인

- 실시간: `/camera/camera/color/image_raw`(rgb8) → Mask 약 30 Hz 수신
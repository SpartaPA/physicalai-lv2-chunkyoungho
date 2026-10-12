# 토픽 정보

`ros2 launch blue_cube_ros blue_cube.launch.py source:=bag`(scene_target bag, 기본 설정)으로 실행한 상태에서 저장했습니다. 목록·info는 이전 실행의 정보가 섞이지 않도록 `--no-daemon`으로 새로 조회했습니다. info는 구독자(`record_run`)가 붙어 있는 상태에서 받았습니다.

| 자료 | 토픽 | 메시지 타입 | 발행 노드 | 구독 노드 | 수신 주기 | 파일 |
|---|---|---|---|---|---|---|
| Raw Image | `/camera/camera/color/image_raw` | `sensor_msgs/msg/Image` (rgb8 640×480) | `rosbag2_player` | `blue_cube_detector`, `record_run` | 29.98 Hz | [info_raw.txt](info_raw.txt) |
| Mask | `/blue_cube_detector/mask` | `sensor_msgs/msg/Image` (mono8) | `blue_cube_detector` | `record_run` | 29.97 Hz | [info_mask.txt](info_mask.txt) |
| 검출 Overlay | `/blue_cube_detector/overlay` | `sensor_msgs/msg/Image` (bgr8) | `blue_cube_detector` | `record_run` | 29.98 Hz | [info_overlay.txt](info_overlay.txt) |
| 검출 결과 | `/blue_cube_detector/detections` | `vision_msgs/msg/Detection2DArray` | `blue_cube_detector` | `record_run` | 29.98 Hz | [info_detections.txt](info_detections.txt) |

- 전체 토픽 목록: [topic_list.txt](topic_list.txt)
- 수신 주기: [topic_hz.txt](topic_hz.txt) (`ros2 topic hz`, 60개 메시지 창)
- 메시지 정의: [interface_Detection2DArray.txt](interface_Detection2DArray.txt), [interface_Image.txt](interface_Image.txt)
- QoS: bag 재생 발행자는 RELIABLE, 검출 노드의 Raw 구독은 BEST_EFFORT(센서 QoS)로 서로 호환됩니다. 검출 노드의 출력 세 토픽은 RELIABLE로 발행합니다.

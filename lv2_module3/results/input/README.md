# 분석용 입력 bag

bag 원본(각 약 300 MiB)은 용량 때문에 저장소에 넣지 않고, `ros2 bag info` 출력만 둡니다.

| bag | 정보 | 장면 |
|---|---|---|
| `scene_target` | [scene_target_info.txt](scene_target_info.txt) | 파란 원통을 손에 든 장면. 뒤에 남색 스웨터 |
| `scene_no_target` | [scene_no_target_info.txt](scene_no_target_info.txt) | 같은 자리, 원통 없음. 첫 프레임은 이전 장면이라 `start_offset 0.1`로 제외 |

- 녹화: D435 컬러 640×480 30 Hz(자동 노출 끔), `/camera/camera/color/image_raw`·`/camera/camera/color/camera_info`, mcap. 사용한 명령은 [lv2_module3/README.md](../../README.md) 1절
- 두 bag 모두 약 30.1 Hz로 녹화되어 프레임 누락이 없습니다.

## 대표 프레임

실험 1·2의 A·B 모두 같은 stamp **`1791784737.984`**(`scene_target`의 중간 프레임)를 대표 프레임으로 씁니다. 각 설정에서 토픽으로 받은 Raw | Mask | Overlay를 한 장으로 합쳐 저장했습니다.

| 실험 | 이미지 | 박스 수 | 박스 (cx, cy, w, h) [px] | Mask 픽셀 수 |
|---|---|---|---|---|
| 1-A (V 하한 50) | [exp1_A_frame_1791784737.984.png](../exp1/A/exp1_A_frame_1791784737.984.png) | 2 | (482.0, 168.0, 293, 221), (631.5, 103.5, 16, 64) | 21,034 |
| 1-B (V 하한 95) | [exp1_B_frame_1791784737.984.png](../exp1/B/exp1_B_frame_1791784737.984.png) | 1 | (431.5, 121.5, 48, 88) | 2,937 |
| 2-A (min_area 500) | [exp2_A_frame_1791784737.984.png](../exp2/A/exp2_A_frame_1791784737.984.png) | 1 | (418.5, 121.5, 86, 88) | 3,821 |
| 2-B (min_area 100) | [exp2_B_frame_1791784737.984.png](../exp2/B/exp2_B_frame_1791784737.984.png) | 2 | (418.5, 121.5, 86, 88), (474.5, 70.5, 20, 20) | 3,821 |

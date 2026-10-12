# 분석용 입력 bag

bag 원본(각 약 300 MiB)은 용량 때문에 저장소에 넣지 않고, `ros2 bag info` 출력만 둡니다.

| bag | 정보 | 장면 |
|---|---|---|
| `scene_target` | [scene_target_info.txt](scene_target_info.txt) | 파란 원통을 손에 든 장면. 뒤에 남색 스웨터 |
| `scene_no_target` | [scene_no_target_info.txt](scene_no_target_info.txt) | 같은 자리, 원통 없음. 첫 프레임은 이전 장면이라 `start_offset 0.1`로 제외 |

- 녹화: D435 컬러 640×480 30 Hz(자동 노출 끔), `/camera/camera/color/image_raw`·`/camera/camera/color/camera_info`, mcap. 사용한 명령은 [lv2_module3/README.md](../../README.md) 1절
- 두 bag 모두 약 30.1 Hz로 녹화되어 프레임 누락이 없습니다.

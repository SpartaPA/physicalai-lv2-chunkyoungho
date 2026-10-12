"""blue_cube_detector 실행. 입력을 source로 고른다.

  source:=bag    (기본, 분석용) ros2 bag play로 녹화한 Raw Image를 그대로 재발행 -> /camera/camera/color/image_raw
                 같은 bag을 A·B에 쓰면 프레임(header.stamp)별로 같은 입력이 들어간다.
                 bag 경로·반복·시작 오프셋은 params_file의 bag_play.ros__parameters에서 읽는다.
                 bag:=<bag 폴더> 를 주면 yaml보다 우선한다.
  source:=camera (실시간) realsense2_camera를 함께 띄워 D435 컬러 640x480 30 Hz -> /camera/camera/color/image_raw
  공통: params_file:=<yaml> 로 실험 A·B 설정을 바꿔 넣는다.
  경로 찾는 순서: 절대 경로 -> (yaml 값은 그 yaml 폴더, 명령줄 값은 현재 폴더) 기준
"""
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CAMERA_TOPIC = '/camera/camera/color/image_raw'
SOURCES = ('bag', 'camera')


def resolve_path(path, base_dir, want_dir=False):
    """절대 경로 -> base_dir 기준으로 찾는다. 저장소를 받은 누구나 상대 경로로 쓸 수 있게."""
    path = os.path.expanduser(path)
    candidate = path if os.path.isabs(path) else os.path.join(base_dir, path)
    if os.path.isdir(candidate) if want_dir else os.path.isfile(candidate):
        return os.path.abspath(candidate)
    raise RuntimeError(f'경로 없음: {path} (찾은 위치: {candidate})')


def section(params_file, name):
    """params_file에서 <name>.ros__parameters 를 읽는다 (없으면 빈 dict)."""
    with open(params_file, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get(name, {}).get('ros__parameters', {})


def pick(context, arg, cfg, key, params_file):
    """명령줄 값(현재 폴더 기준)이 있으면 그것을, 없으면 yaml 값(yaml 폴더 기준)을 쓴다."""
    cli = LaunchConfiguration(arg).perform(context)
    if cli:
        return cli, os.getcwd()
    if key in cfg:
        return cfg[key], os.path.dirname(params_file)
    raise RuntimeError(f'{params_file}에 {key} 가 없고 {arg}:= 도 없음')


def launch_setup(context):
    source = LaunchConfiguration('source').perform(context)
    if source not in SOURCES:
        raise RuntimeError(f'source:={source} 는 지원하지 않는다. bag 또는 camera')
    params_file = os.path.abspath(os.path.expanduser(LaunchConfiguration('params_file').perform(context)))
    actions = []
    if source == 'bag':
        play = section(params_file, 'bag_play')
        path, base = pick(context, 'bag', play, 'uri', params_file)
        cmd = ['ros2', 'bag', 'play', resolve_path(path, base, want_dir=True),
               '--topics', CAMERA_TOPIC, '--disable-keyboard-controls', '--progress-bar-update-rate', '0',
               '--start-offset', str(float(play.get('start_offset', 0.0)))]
        if play.get('loop', True):
            cmd.append('--loop')
        actions.append(ExecuteProcess(cmd=cmd, name='bag_play', output='screen'))
    else:
        rs_launch = os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(rs_launch),
            launch_arguments={'enable_depth': 'false', 'rgb_camera.color_profile': '640,480,30'}.items()))
    actions.append(Node(
        package='blue_cube_ros', executable='blue_cube_node', name='blue_cube_detector',
        # 뒤에 오는 dict가 params_file의 image_topic을 덮어쓴다 (두 입력 모두 카메라 토픽)
        parameters=[params_file, {'image_topic': CAMERA_TOPIC}],
        output='screen'))
    return actions


def generate_launch_description():
    default_params = os.path.join(get_package_share_directory('blue_cube_ros'), 'config', 'blue_cube.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('source', default_value='bag',
                              description='bag(녹화 재생, 분석용) | camera(실시간 D435)'),
        DeclareLaunchArgument('params_file', default_value=default_params,
                              description='검출 설정 + bag_play.uri·loop·start_offset'),
        DeclareLaunchArgument('bag', default_value='',
                              description='(선택, bag) yaml의 uri 대신 쓸 bag 폴더, 현재 폴더 기준'),
        OpaqueFunction(function=launch_setup),
    ])

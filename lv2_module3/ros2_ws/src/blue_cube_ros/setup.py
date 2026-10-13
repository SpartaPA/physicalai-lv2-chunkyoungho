from glob import glob

from setuptools import find_packages, setup

package_name = 'blue_cube_ros'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml') + glob('config/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='chunkyoungho',
    maintainer_email='ckhy2k@gmail.com',
    description='ROS 2 wrapper for blue_cube_reference.detect_blue()',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'blue_cube_node = blue_cube_ros.blue_cube_node:main',
            'record_run = blue_cube_ros.record_run:main',
        ],
    },
)

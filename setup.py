#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Carillon',
    version='1.0.0',
    description='Ultra simple keyboard layout controller',
    url='https://github.com/sbreatnach/carillon',
    license='MIT',
    author='Shane Breatnach',
    author_email='shane.breatnach@gmail.com',
    packages=['carillon'],
    keywords='carillon setxkbmap keyboard keyboards layout linux openbox',
    install_requires=[
        'PyYAML>=3.12',
        'pygobject>=3.20'
    ],
    python_requires='~=3.3',
    entry_points={
        'console_scripts': [
            'carillon=carillon:main'
        ]
    }
)

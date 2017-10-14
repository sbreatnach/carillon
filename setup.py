#!/usr/bin/env python

from distutils.core import setup

setup(
    name='SimpleKeys',
    version='0.0.1',
    description='Ultra simple keyboard layout controller',
    url='https://github.com/sbreatnach/simplekeys',
    license='MIT',
    author='Shane Breatnach',
    author_email='shane.breatnach@gmail.com',
    keywords='setxkbmap keyboard keyboards layout linux openbox',
    install_requires=['PyYAML'],
    python_requires='~=3.3',
    entry_points={
        'console_scripts': [
            'simplekeys=simplekeys:main'
        ]
    }
)

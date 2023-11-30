from setuptools import setup

setup(
    name='rgg_save_tool',
    version='0.1',
    py_modules=['rgg_save_tool'],
    install_requires=[
        'chardet',
    ],
    entry_points={
        'console_scripts': [
            'rgg_save_tool=rgg_save_tool:main',
        ],
    },
)

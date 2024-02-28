from setuptools import setup

setup(
    name='chem_tool',
    version='1.0',
    description='GUI For Making Chemistry App Questions',
    author='Tyler Viarengo',
    packages=['chem_tool'],
    entry_points={'console_scripts': [
        'chem_tool_run = chem_tool.gui:main',
    ]},
)
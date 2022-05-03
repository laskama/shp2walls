from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='geo2wall',
    version='0.0.1',
    url='https://github.com/laskama/shp2walls',
    author='Marius Laska',
    author_email='marius.laska@rwth-aachen.de',
    description='This package extract the walls of a building model stored as georeferenced file (e.g. .shp, or .kml)',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)

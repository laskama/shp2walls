from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='geo2wall',
    version='0.0.1',
    url='https://git.rwth-aachen.de/marius.laska/shp2walls.git',
    author='Marius Laska',
    author_email='marius.laska@rwth-aachen.de',
    description='Description of my package',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
)

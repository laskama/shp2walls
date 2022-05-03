# Wall extraction from geo-files such as ESRI shapefile (shp) or Keyhole Markup Language (kml)

### Installation
Installation via virtual environment is recommended
```shell
pip install git+ssh://git@github.com/laskama/shp2walls.git
```

### Usage

```python
from pkg_resources import resource_filename
import geo2wall.extract as g2w
import matplotlib.pyplot as plt

# extract walls
file = resource_filename("geo2wall", "shp/1og.kml")
walls_h, walls_v = g2w.get_walls_from_geometry_file(
    file_path=file,
    kml_folder="Waende",
    rotation_angle=-99)    

# plot extracted walls
g2w.plot_walls((walls_h, walls_v))

plt.show()
```

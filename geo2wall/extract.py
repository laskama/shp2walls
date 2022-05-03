from geopandas import read_file, GeoDataFrame
import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.linestring import LineString
from shapely.geometry.multipolygon import MultiPolygon
import matplotlib.pyplot as plt
import numpy as np
import os
import ezdxf


def get_walls_from_geometry_file(file_path, kml_folder="Waende", rotation_angle=-99, scale=None):
    """
    Reads a file that stores geometries (.kml or .shp) and extracts
    its walls.
    :param file_path: Path to input file
    :param kml_folder: Folder that contains the walls
    :param rotation_angle: Rotation angle
    :return: tuple of (walls_h, walls_v)
    """
    file = read_geometry_file(file_path, kml_folder, scale=scale)
    data, _, _ = rotate_and_translate(file, rotation_angle)
    return transform_to_lines(data)


def read_geometry_file(file_path, kml_folder="Waende", dest_crs="epsg:25832", scale=None):
    """
    Reads geometry files (currently supported: .shp and .kml) into
    geopandas dataframe. Performs projection into destination crs
    (mercator preferred).
    :param file_path: Path to input file
    :param kml_folder: Folder that stores walls of kml file
    (not used when file type is .shp)
    :param dest_crs: Destination coordinate reference system
    :return: geopandas Dataframe
    """
    # read file based on file type
    f_type = os.path.splitext(file_path)[1]
    if f_type == ".shp":
        file = read_file(file_path)
    elif f_type == ".kml":
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        file = read_file(file_path, driver='KML', layer=kml_folder)
    elif f_type == ".dxf":
        file = read_dxf_file(file_path, scale=scale)

    # transform to dest crs
    if not file.crs == dest_crs and f_type != ".dxf":
        file = file.to_crs(dest_crs)
        file = _expand_to_polygons(file)

    return file


def rotate_and_translate(df, angle=-99, rotation_center=None, tranlation=None):
    """
    Rotates geometries of dataframe and translates them such that
    origin is at lower left.
    :param df: Geopandas Dataframe
    :param angle: Rotation angle
    :param rotation_center: Defines the origin for rotation, if None defaults to
    unary_union.centroid
    :return: tuple of
    (Geopandas Geoseries, origin of ration, offset applied during translation)
    """
    if rotation_center is None:
        rotation_center = df.unary_union.centroid
    data = df.rotate(angle, origin=rotation_center)
    if tranlation is None:
        b = data.bounds
        lower_left = b.iloc[:, :2].min(axis=0).to_numpy()
    else:
        lower_left = tranlation
    data = data.translate(xoff=-lower_left[0], yoff=-lower_left[1])

    return data, rotation_center, lower_left


def read_dxf_file(file_name, scale=None):
    doc = ezdxf.readfile(file_name)
    msp = doc.modelspace()

    lines = []

    # entity query for all LINE entities in modelspace
    for e in msp.query('LINE'):
        start, end = e.dxf.start, e.dxf.end
        if scale is not None:
            start *= scale
            end *= scale
        lines.append(LineString((start, end)))

    gdf = gpd.GeoDataFrame(geometry=lines)

    return gdf


def transform_to_lines(data):
    """
    Converts the polygons of the geoseries to walls (no thickness).
    CAREFUL: currently only walls without angle are supported.
    A wall is defined as 4-tuple (x_1, y_1, x_2, y_2) with its two endpoints.
    :param data: Geopandas Geoseries
    :return: tuple of horizontal and vertical walls (walls_h, walls_v)
    """
    walls_h = []
    walls_v = []
    for geo in data:
        if geo.geom_type == "LineString":

            x1, x2 = geo.coords.xy[0][0], geo.coords.xy[0][1]
            y1, y2 = geo.coords.xy[1][0], geo.coords.xy[1][1]

            l = np.array([x1, y1, x2, y2])

            xdiff = np.abs(x1 - x2)
            ydiff = np.abs(y1 - y2)

            if xdiff > ydiff:
                walls_h += [l]
            else:
                walls_v += [l]

        else:
            xdiff = np.abs(geo.bounds[0] - geo.bounds[2])
            ydiff = np.abs(geo.bounds[1] - geo.bounds[3])

            if xdiff > ydiff:
                # horizontal line
                c = (geo.bounds[1] + geo.bounds[3]) / 2.0
                w = np.array([geo.bounds[0], c, geo.bounds[2], c])
                walls_h += [w]
            else:
                # vertical line
                c = (geo.bounds[0] + geo.bounds[2]) / 2.0
                w = np.array([c, geo.bounds[1], c, geo.bounds[3]])
                walls_v += [w]

    return walls_h, walls_v


def plot_walls(walls, ax=None):
    """
    Visualize walls.
    :param walls: tuple of horizontal and vertical walls
    :return:
    """
    if ax is None:
        fig, ax = plt.subplots()
    for w_h in walls[0]:
        ax.plot([w_h[0], w_h[2]], [w_h[1], w_h[3]], color="green")
    for w_h in walls[1]:
        ax.plot([w_h[0], w_h[2]], [w_h[1], w_h[3]], color="green")
    plt.axis('equal')


def _expand_to_polygons(df):
    """
    Code based on: https://gist.github.com/mhweber/cf36bb4e09df9deee5eb54dc6be74d26
    Helping function that converts Multipolygons to list of Polygons
    which is necessary after crs projection.
    :param df: Geopandas dataframe
    :return: Geopandas dataframe with expansion of Multipolygon
    """
    outdf = GeoDataFrame(columns=df.columns)
    for idx, row in df.iterrows():
        if type(row.geometry) == Polygon:
            outdf = outdf.append(row, ignore_index=True)
        if type(row.geometry) == MultiPolygon:
            multdf = GeoDataFrame(columns=df.columns)
            recs = len(row.geometry)
            multdf = multdf.append([row]*recs, ignore_index=True)
            for geom in range(recs):
                multdf.loc[geom, 'geometry'] = row.geometry[geom]
            outdf = outdf.append(multdf, ignore_index=True)
    return outdf


if __name__ == '__main__':
    for idx in range(3):

        walls_h, walls_v = get_walls_from_geometry_file("dxf/e{}.dxf".format(idx), scale=0.001, rotation_angle=0)
        plot_walls((walls_h, walls_v))

    for idx in range(7):
        # read kml files
        walls_h, walls_v = get_walls_from_geometry_file("kml/{}og.kml".format(idx+1))
        plot_walls((walls_h, walls_v))

        # read shp files
        walls_h, walls_v = get_walls_from_geometry_file("shp/{}og.shp".format(idx + 1))
        plot_walls((walls_h, walls_v))

    plt.show()

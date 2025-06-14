import requests
import geopandas as gpd
import numpy as np

from io import BytesIO
from scipy.interpolate import Rbf

from shapely.geometry import Point
from shapely.prepared import prep

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap, PowerNorm
from matplotlib.backends.backend_agg import FigureCanvasAgg

from heatmap.data_provider import StationValue


class HeatmapCreator:

    _GEOJSON_URL = "https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-medium.geojson"
    _GEOJSON_LOCAL = "./data/wojewodztwa-medium.geojson"
    _CRS_LATLON = "EPSG:4326"
    _CRS_PROJECTED = "EPSG:2180"  # Poland CS92
    _COLORMAP = LinearSegmentedColormap.from_list(
    'temp_cmap',
    [('#8e44ad'), ('#3498db'), ('#2ecc71'), ('#f1c40f'), ('#e74c3c')]
    )

    _geometry = None

    def __init__(self):
        self._geometry = self._load_poland_geometry()

    def _load_poland_geometry_from_url(self, url=_GEOJSON_URL):
        response = requests.get(url)
        response.raise_for_status()
        gdf = gpd.read_file(BytesIO(response.content))
        return gdf, gdf.to_crs(self._CRS_PROJECTED).geometry.union_all()

    def _load_poland_geometry_from_file(self, path=_GEOJSON_LOCAL):
        gdf = gpd.read_file(path)
        return gdf, gdf.to_crs(self._CRS_PROJECTED).geometry.union_all()

    def _load_poland_geometry(self):
        try:
            _geometry = self._load_poland_geometry_from_file()
        except:
            _geometry = self._load_poland_geometry_from_url()

        return _geometry

    def generate_heatmap(self, stations: list[StationValue], colormap=_COLORMAP, displaydate=''):

        voivodeships_ll, poland_shape_projected = self._geometry

        prepared_poland = prep(poland_shape_projected.buffer(1000))  # 1km buffer

        # Prepare station data
        lons = np.array([s.lon for s in stations])
        lats = np.array([s.lat for s in stations])
        temps = np.array([s.value for s in stations])
        names = np.array([s.name for s in stations])

        # Convert to projected CRS
        gdf = gpd.GeoDataFrame(
            {'temperature': temps, 'name': names},
            geometry=gpd.points_from_xy(lons, lats),
            crs=self._CRS_LATLON
        ).to_crs(self._CRS_PROJECTED)

        x, y = gdf.geometry.x.values, gdf.geometry.y.values
        t = gdf.temperature.values

        # Create interpolation grid
        bounds = poland_shape_projected.bounds
        x_grid = np.linspace(bounds[0], bounds[2], 500)
        y_grid = np.linspace(bounds[1], bounds[3], 500)
        xx, yy = np.meshgrid(x_grid, y_grid)

        # Interpolate using RBF
        rbf = Rbf(x, y, t, function='linear', smooth=5)
        grid_temp = rbf(xx, yy)

        # Mask areas outside Poland
        points = np.column_stack([xx.ravel(), yy.ravel()])
        mask = np.array([prepared_poland.contains(Point(p)) for p in points]).reshape(xx.shape)
        grid_temp[~mask] = np.nan

        # Reproject grid to geographic coordinates
        grid_points = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(xx.ravel(), yy.ravel()),
            crs=self._CRS_PROJECTED
        ).to_crs(self._CRS_LATLON)

        grid_lon = grid_points.geometry.x.values.reshape(xx.shape)
        grid_lat = grid_points.geometry.y.values.reshape(yy.shape)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 10))

        norm = Normalize(vmin=-5, vmax=30)
        # norm = PowerNorm(gamma=0.7, vmin=-5, vmax=30)
        levels = np.linspace(-5, 30, 200)
        # levels = np.arange(-5, 30.01, 0.2)

        # if colormap is None:
        #     colormap = self._COLORMAP
        colormap = LinearSegmentedColormap.from_list(
        'piecewise_temp',
        [
                (0.0, '#8e44ad'),   # Violet (fixed)
                (0.15, '#3498db'),  # Blue (denser)
                (0.35, '#2ecc71'),  # Green (denser)
                (0.6, '#f1c40f'),   # Yellow (denser)
                (1.0, '#ff0000')    # Red (fixed)
            ]
        )

        # colormap = self.cmap

        # Heatmap
        contour = ax.contourf(
            grid_lon, grid_lat, grid_temp,
            levels=levels,
            cmap=colormap,
            norm=norm,
            extend='both'
        )

        # Station points with names
        for lon, lat, name, temp in zip(lons, lats, names, temps):
            ax.scatter(
                lon, lat,
                c=[temp],
                cmap=colormap,
                norm=norm,
                s=60,
                edgecolor='black',
                linewidth=0.8,
                zorder=10
            )
            ax.text(
                lon + 0.05, lat + 0.03,
                f"{name} ({temp:.1f}°C)",
                fontsize=8,
                ha='left',
                va='bottom',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1)
            )

        # Add administrative boundaries
        voivodeships_ll.boundary.plot(
            ax=ax,
            color='black',
            linewidth=0.6
        )

        # Colorbar
        cbar = fig.colorbar(contour, ax=ax, shrink=0.7)
        cbar.set_label('Temperature (°C)')
        cbar.set_ticks(np.arange(-5, 31, 5))

        # Add padding around plot
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_pad = (xlim[1] - xlim[0]) * 0.02
        y_pad = (ylim[1] - ylim[0]) * 0.02
        ax.set_xlim(xlim[0] - x_pad, xlim[1] + x_pad)
        ax.set_ylim(ylim[0] - y_pad, ylim[1] + y_pad)

        # Final layout
        ax.set_title(displaydate, pad=20, fontsize=14)
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        ax.grid(True, linestyle=':', alpha=0.4)

        return fig


    def generate_image(self, stations, displaydate):
        fig = self.generate_heatmap(stations=stations, displaydate=displaydate)
        try:
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            buf = canvas.buffer_rgba()
            img = np.asarray(buf).reshape((*reversed(canvas.get_width_height()), 4))
            # img = np.array(canvas.renderer.buffer_rgba())
            img = img[:, :, :3]  # Drop alpha channel if present
        finally:
            plt.close(fig)

        return displaydate, img



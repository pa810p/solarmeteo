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
        [
            (0.0, '#8e44ad'),   # Violet (fixed)
            (0.15, '#3498db'),  # Blue (denser)
            (0.35, '#2ecc71'),  # Green (denser)
            (0.6, '#f1c40f'),   # Yellow (denser)
            (1.0, '#ff0000')    # Red (fixed)
        ]
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


    def generate_heatmap(self, stations: list[StationValue], colormap=_COLORMAP, displaydate='', vmin=None, vmax=None,
                         label='Temperature (°C)',
                         scale_min=None, scale_max=None):

        voivodeships_ll, poland_shape_projected = self._geometry

        prepared_poland = prep(poland_shape_projected.buffer(1000))  # 1km buffer

        # Prepare station data
        lons = np.array([s.lon for s in stations])
        lats = np.array([s.lat for s in stations])
        temps = np.array([s.value for s in stations])
        names = np.array([s.name for s in stations])

        if scale_min is not None and scale_max is not None:
            temps_scaled = (temps - scale_min) / (scale_max - scale_min)
        else:
            temps_scaled = temps

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
        # rbf = Rbf(x, y, t, function='linear', smooth=5)
        # grid_temp = rbf(xx, yy)
        rbf = Rbf(x, y, temps_scaled, function='linear', smooth=5)
        grid_temp_scaled = rbf(xx, yy)
        if scale_min is not None and scale_max is not None:
            grid_temp = grid_temp_scaled * (scale_max - scale_min) + scale_min
        else:
            grid_temp = grid_temp_scaled

        # Mask areas outside Poland
        points = np.column_stack([xx.ravel(), yy.ravel()])
        mask = np.array([prepared_poland.contains(Point(p)) for p in points]).reshape(xx.shape)
        grid_temp[~mask] = np.nan
        grid_temp = np.clip(grid_temp, vmin, vmax)

        # Reproject grid to geographic coordinates
        grid_points = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(xx.ravel(), yy.ravel()),
            crs=self._CRS_PROJECTED
        ).to_crs(self._CRS_LATLON)

        grid_lon = grid_points.geometry.x.values.reshape(xx.shape)
        grid_lat = grid_points.geometry.y.values.reshape(yy.shape)

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 10))

        norm = Normalize(vmin=vmin, vmax=vmax)
        levels = np.linspace(vmin, vmax, 200)

        if colormap is None:
            colormap = self._COLORMAP

        # Heatmap
        contour = ax.contourf(
            grid_lon, grid_lat, grid_temp,
            levels=levels,
            cmap=colormap,
            norm=norm,
            extend='neither'
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
                f"{name} ({temp:.1f})",
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
        cbar.set_label(label)
        cbar.set_ticks(np.arange(vmin, vmax + 1, 5))

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
        fig = self.generate(stations=stations, displaydate=displaydate)
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



class TemperatureCreator(HeatmapCreator):

    _COLORMAP = LinearSegmentedColormap.from_list(
        'temp_cmap',
        [
            (0.0, '#8e44ad'),   # Violet (fixed)
            (0.15, '#3498db'),  # Blue (denser)
            (0.35, '#2ecc71'),  # Green (denser)
            (0.6, '#f1c40f'),   # Yellow (denser)
            (1.0, '#ff0000')    # Red (fixed)
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate):
        return self.generate_heatmap(stations=stations, colormap=self._COLORMAP, displaydate=displaydate,
                                     vmin=-5, vmax=30, label="Temperature (°C)")


class PressureCreator(HeatmapCreator):

    _COLORMAP = LinearSegmentedColormap.from_list(
        'temp_cmap',
        [
            (0.0, '#e0f8e0'),  # Very light green
            (0.25, '#a8e6a3'), # Light green
            (0.5, '#5fd68b'),  # Medium green
            (0.75, '#2ecc71'), # Standard green
            (1.0, '#145a32')   # Dark green
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate):
        return self.generate_heatmap(stations=stations, colormap=self._COLORMAP, displaydate=displaydate,
                                     vmin=1000, vmax=1030, label="Pressure (hPa)",
                                     scale_min=960, scale_max=1040)


class HumidityCreator(HeatmapCreator):
    _COLORMAP = LinearSegmentedColormap.from_list(
        'humidity_cmap',
        [
            (0.0, '#e0f7fa'),   # Light cyan
            (0.25, '#81d4fa'),  # Light blue
            (0.5, '#4fc3f7'),   # Medium blue
            (0.75, '#0288d1'),  # Deep blue
            (1.0, '#01579b')    # Dark blue
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate):
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=0, vmax=100,
            label="Humidity (%)",
            scale_min=0, scale_max=100
        )


class WindCreator(HeatmapCreator):
    _COLORMAP = LinearSegmentedColormap.from_list(
        'wind_cmap',
        [
            (0.0, '#e0f2f1'),   # Light teal
            (0.25, '#80cbc4'),  # Teal
            (0.5, '#26a69a'),   # Medium teal
            (0.75, '#00897b'),  # Deep teal
            (1.0, '#004d40')    # Dark teal
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate):
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=0, vmax=15,
            label="Wind (m/s)",
            scale_min=0, scale_max=15
        )


class PrecipitationCreator(HeatmapCreator):
    _COLORMAP = LinearSegmentedColormap.from_list(
        'precipitation_cmap',
        [
            (0.0, '#f7fbff'),   # Very light blue
            (0.25, '#c6dbef'),  # Light blue
            (0.5, '#6baed6'),   # Medium blue
            (0.75, '#2171b5'),  # Deep blue
            (1.0, '#08306b')    # Dark blue
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate):
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=0, vmax=10,
            label="Precipitation (mm)",
            scale_min=0, scale_max=10
        )


import requests
import geopandas as gpd
import numpy as np

from io import BytesIO
from scipy.interpolate import Rbf

from shapely.geometry import Point
from shapely.prepared import prep

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.backends.backend_agg import FigureCanvasAgg

from solarmeteo.heatmap.data_provider import StationValue

from logging import getLogger



logger = getLogger(__name__)


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
                         scale_min=None, scale_max=None,
                         display_labels=None):
        """
        Generates a heatmap frame for the given stations.
        :param display_labels: list of city names for those markers will be rendered
        :param stations: StationValue list containing longitude, latitude, value, and name.
        :param colormap: Matplotlib colormap for the heatmap.
        :param displaydate: Display date for the heatmap title.
        :param vmin: Minimum value for the color scale.
        :param vmax: Maximum value for the color scale.
        :param label: Label for the colorbar.
        :param scale_min: Minimum value for scaling the data.
        :param scale_max: Maximum value for scaling the data.
        :return: generated matplotlib figure.
        """

        if display_labels is None:
            display_labels = []
        voivodeships_ll, poland_shape_projected = self._geometry
        prepared_poland = prep(poland_shape_projected.buffer(1000))  # 1km buffer

        # Prepare station data
        lons = np.array([s.lon for s in stations])
        lats = np.array([s.lat for s in stations])
        temps = np.array([s.value for s in stations])
        names = np.array([s.name for s in stations])
        directions = np.array([getattr(s, 'direction', None) for s in stations])  # Get directions if they exist

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
        # t = gdf.temperature.values

        # Create interpolation grid
        bounds = poland_shape_projected.bounds
        x_grid = np.linspace(bounds[0], bounds[2], 500)
        y_grid = np.linspace(bounds[1], bounds[3], 500)
        xx, yy = np.meshgrid(x_grid, y_grid)

        # scaling because RBF requires normalized values because of problems with large values
        # it uses absolute values for interpolation
        try:
            rbf = Rbf(x, y, temps_scaled, function='linear', smooth=1)
            grid_temp_scaled = rbf(xx, yy)
        except Exception as e:
            logger.error(f"Interpolating heatmap exception {e} on datetime: {displaydate}")
            return None

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
        fig, ax = plt.subplots(figsize=(6, 5))

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

        # Get current limits before adding arrows
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Calculate asymmetric padding
        plot_height = ylim[1] - ylim[0]
        x_pad = (xlim[1] - xlim[0]) * 0.02
        y_pads = {
            'bottom': plot_height * 0.02,
            'top': plot_height * 0.08  # 4x more space at top
        }

        # Set new limits
        ax.set_xlim(xlim[0] - x_pad, xlim[1] + x_pad)
        ax.set_ylim(ylim[0] - y_pads['bottom'], ylim[1] + y_pads['top'])

        # Station points with names
        for lon, lat, name, temp, direction in zip(lons, lats, names, temps, directions):
            if name in display_labels:
                ax.scatter(
                    lon, lat,
                    c=[temp],
                    cmap=colormap,
                    norm=norm,
                    s=60,
                    edgecolor='black',
                    linewidth=0.4,
                    zorder=5
                )

                ax.text(
                    lon + 0.05, lat + 0.03,
                    f"{name} ({temp:.1f})",
                    fontsize=6,
                    ha='left',
                    va='bottom',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1),
                    zorder=2
                )

            if direction is not None:
                    rad = np.radians(direction)
                    # Calculate arrow components (shorter arrow)
                    dx = 0.2 * np.sin(rad)  # 0.1° longitude length
                    dy = 0.2 * np.cos(rad)  # 0.1° latitude length

                    ax.arrow(
                        lon, lat,
                        dx, dy,
                        head_width=0.08,  # Smaller head width
                        head_length=0.1,  # Smaller head length
                        fc='black',
                        ec='black',
                        linewidth=0.3,
                        zorder=6
                    )


        # Add administrative boundaries
        voivodeships_ll.boundary.plot(
            ax=ax,
            color='black',
            linewidth=0.3
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


    def generate_image(self, stations, displaydate, display_labels, **kwargs):
        logger.debug(f"Generate image for: {displaydate}")
        fig = self.generate(stations=stations, displaydate=displaydate, display_labels=display_labels, **kwargs)
        if fig is not None:
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
        else:
            return displaydate, None


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

    def generate(self, stations, displaydate, display_labels, **kwargs):
        # Use provided scale from kwargs, or fall back to the original defaults
        vmin = kwargs.get('vmin', -5)
        vmax = kwargs.get('vmax', 30)
        scale_min = kwargs.get('scale_min')
        scale_max = kwargs.get('scale_max')

        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin,
            vmax=vmax,
            label="Temperature (°C)",
            scale_min=scale_min,
            scale_max=scale_max,
            display_labels=display_labels
        )


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

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 1000)
        vmax = kwargs.get('vmax', 1030)
        scale_min = kwargs.get('scale_min', 960)
        scale_max = kwargs.get('scale_max', 1040)
        return self.generate_heatmap(stations=stations, colormap=self._COLORMAP, displaydate=displaydate,
                                     vmin=vmin, vmax=vmax, label="Pressure (hPa)",
                                     scale_min=scale_min, scale_max=scale_max,
                                     display_labels=display_labels)


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

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 0)
        vmax = kwargs.get('vmax', 100)
        scale_min = kwargs.get('scale_min', 0)
        scale_max = kwargs.get('scale_max', 100)
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin, vmax=vmax,
            label="Humidity (%)",
            scale_min=scale_min, scale_max=scale_max,
            display_labels=display_labels
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

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 0)
        vmax = kwargs.get('vmax', 15)
        scale_min = kwargs.get('scale_min', 0)
        scale_max = kwargs.get('scale_max', 15)
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin, vmax=vmax,
            label="Wind (m/s)",
            scale_min=scale_min, scale_max=scale_max,
            display_labels=display_labels
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

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 0)
        vmax = kwargs.get('vmax', 10)
        scale_min = kwargs.get('scale_min', 0)
        scale_max = kwargs.get('scale_max', 10)
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin, vmax=vmax,
            label="Precipitation (mm)",
            scale_min=scale_min, scale_max=scale_max,
            display_labels=display_labels
        )


class PM10Creator(HeatmapCreator):
    _COLORMAP = LinearSegmentedColormap.from_list(
        'pm10_cmap',
        [
            (0.0,  '#f9f9f9'),  # Very light gray
            (0.25, '#d3d3d3'),  # Light gray
            (0.5,  '#9b9b9b'),  # Medium gray
            (0.75, '#575757'),  # Deep gray
            (1.0,  '#232323')   # Dark gray
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 0)
        vmax = kwargs.get('vmax', 40)
        scale_min = kwargs.get('scale_min', 0)
        scale_max = kwargs.get('scale_max', 50)
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin, vmax=vmax,
            label="PM 10 (ppm)",
            scale_min=scale_min, scale_max=scale_max,
            display_labels=display_labels
        )


class PM25Creator(HeatmapCreator):
    _COLORMAP = LinearSegmentedColormap.from_list(
        'pm25_cmap',
        [
            (0.0,  '#fce4ec'),  # Very light claret
            (0.25, '#f4a6b7'),  # Light claret
            (0.5,  '#c05a6a'),  # Medium claret
            (0.75, '#8b1c3a'),  # Deep claret
            (1.0,  '#4a0d1f')   # Dark claret
        ]
    )

    def __init__(self):
        super().__init__()

    def generate(self, stations, displaydate, display_labels, **kwargs):
        vmin = kwargs.get('vmin', 0)
        vmax = kwargs.get('vmax', 40)
        scale_min = kwargs.get('scale_min', 0)
        scale_max = kwargs.get('scale_max', 50)
        return self.generate_heatmap(
            stations=stations,
            colormap=self._COLORMAP,
            displaydate=displaydate,
            vmin=vmin, vmax=vmax,
            label="PM 2.5 (ppm)",
            scale_min=scale_min, scale_max=scale_max,
            display_labels=display_labels
        )


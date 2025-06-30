from concurrent.futures import ProcessPoolExecutor, as_completed

from solarmeteo.heatmap.data_provider import TemperatureProvider, PressureProvider, PrecipitationProvider, HumidityProvider, \
    WindProvider
from solarmeteo.heatmap.heatmap_creator import TemperatureCreator, PressureCreator, PrecipitationCreator, HumidityCreator, \
    WindCreator

import imageio.v2 as imageio
from datetime import datetime
from logging import getLogger
from PIL import Image

logger = getLogger(__name__)

class CreatorFactory:

    @staticmethod
    def creator(name):
        match name:
            case 'temperature': return TemperatureCreator()
            case 'pressure': return PressureCreator()
            case 'humidity' : return HumidityCreator()
            case 'precipitation': return PrecipitationCreator()
            case 'wind': return WindCreator()
            case _: return None


class ProviderFactory:

    @staticmethod
    def provider(name, meteo_db_url, last):
        match name:
            case 'temperature': return TemperatureProvider(meteo_db_url, last)
            case 'pressure': return PressureProvider(meteo_db_url, last)
            case 'humidity' : return HumidityProvider(meteo_db_url, last)
            case 'precipitation': return PrecipitationProvider(meteo_db_url, last)
            case 'wind': return WindProvider(meteo_db_url, last)
            case _: return None


class HeatMap:
    """
    HeatMap is responsible for generating, saving, and caching heatmap visualizations
    for various meteorological data types (temperature, pressure, precipitation, humidity, wind).
    It supports multiple output formats (PNG, GIF, WebP) and can persist generated frames.

    Attributes:
        heatmaps (list): Supported heatmap types.
        display_labels (list): Labels for display on heatmaps.
        provider_classes (dict): Mapping of heatmap types to their data providers and creators.

    Args:
        meteo_db_url (str): Database URL for meteorological data.
        last (int): Number of recent time points to process.
        file_format (str): Output file format ('png', 'gif', 'webp', 'cache').
        output_file (str): Path to the output file.
        heatmap_type (str): Type of heatmap to generate.
        max_workers (int): Number of parallel workers for processing.
        overwrite (bool): Whether to overwrite existing files.
        usedb (bool): Whether to use the database for persistence.
        persist (bool): Whether to persist generated frames.
    """

    heatmaps = [
        "temperature", "pressure", "precipitation", "humidity", "wind"
    ]

    display_labels = ['Kraków', 'Warszawa', 'Gdańsk', 'Wrocław', 'Szczecin', 'Poznań', 'Suwałki', 'Zakopane', 'Łódź',
                      'Olsztyn', 'Lublin', 'Rzeszów', 'Zielona Góra', 'Białystok']


    def __init__(self, meteo_db_url, last=1, file_format='png', output_file='temperature.png', heatmap_type='temperature', max_workers=16,
                 overwrite=True, usedb=False, persist=False):
        """
        Initialize the HeatMap object with configuration for data source, output, and processing.

        Args:
            meteo_db_url (str): Database URL for meteorological data.
            last (int): Number of recent time points to process.
            file_format (str): Output file format.
            output_file (str): Path to the output file.
            heatmap_type (str): Type of heatmap to generate.
            max_workers (int): Number of parallel workers.
            overwrite (bool): Overwrite existing files.
            usedb (bool): Use database for persistence.
            persist (bool): Persist generated frames.
        """
        self.meteo_db_url = meteo_db_url
        self.last = last
        self.file_format = file_format
        self.output_file = output_file
        self.heatmap_type = heatmap_type
        self.max_workers = max_workers
        self.overwrite = overwrite
        self.usedb = usedb
        self.persist = persist

        self.dataprovider = ProviderFactory.provider(self.heatmap_type, self.meteo_db_url, self.last)
        self.heatmap_creator = CreatorFactory.creator(self.heatmap_type)
        logger.info(f"HeatMap initialized with type: {heatmap_type}, last: {last}, file_format: {file_format}, output_file: {output_file}, max_workers: {max_workers}," \
                + f"overwrite: {overwrite}, usedb: {usedb}, persist: {persist}")


    def _generate_frames_by_datetimes(self, date_times, persist=None ) -> dict:
        """
        Generates heatmap frames for the given list of date_times.

        Args:
            date_times (list): List of date_time objects.
            persist (bool, optional): Whether to persist the frames.

        Returns:
            list: List of generated frames.
        """
        if persist is None:
            persist = self.persist

        logger.debug("Generate frames")
        frames = dict()
        stations = self.dataprovider.provide_stations_by_datetimes(self.heatmap_type, date_times)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.heatmap_creator.generate_image, stations=stations, displaydate=displaydate, display_labels=self.display_labels)
                for idx, (displaydate, stations) in enumerate(stations)
            ]

            for future in as_completed(futures):
                (datetime, frame) = future.result()
                frames [datetime] = frame

        if persist:
            self.dataprovider.store_frames(self.heatmap_type, frames)

        return frames


    def _get_frames_from_persistence(self, datetime):
        """
        Retrieves frames from the persistence layer for the given datetime.

        Args:
            datetime (datetime): Datetime for which to retrieve frames.

        Returns:
            list: List of frames from persistence.
        """
        frames = self.dataprovider.provide_frames_by_type_and_datetimes(self.heatmap_type, datetime)
        return frames


    def _generate_gif(self):
        """
        Generates an animated GIF file from the heatmap frames for the specified type and time range.

        The output file is saved to the path specified by self.output_file.
        """
        last_datetimes =  self.dataprovider.get_last_datetimes(last=self.last)
        frames = self._generate_frames_by_datetimes(last_datetimes)

        # sorted_frames = [image for datetime, image in sorted(frames, key=lambda x: x[0])]
        sorted_frames = dict(sorted(frames.items()))

        imageio.mimsave(f"{self.output_file}", list(sorted_frames.values()), duration=200, palettesize=256, subrectangles=True)
        # imageio.mimsave("animation.mp4", sorted_frames, format="mp4", duration=0.2)  # Save as MP4# Duration per frame (sec)
        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def _generate_png(self):
        """
        Generates a PNG file for the most recent heatmap frame of the specified type.

        This method retrieves the latest datetime, generates the corresponding heatmap frame,
        and saves it as a PNG file to the path specified by self.output_file.

        Returns:
            None
        """
        last_datetimes = self.dataprovider.get_last_datetimes(1)
        frames = self._generate_frames_by_datetimes(last_datetimes)

        imageio.imwrite(f"{self.output_file}", next(iter(frames.values())))
        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def _generate_cache(self):
        """
        Generates and persists heatmap frames for the specified type and time range.

        This method retrieves the last N datetimes, sets the persist flag to True,
        and generates the corresponding heatmap frames, storing them in the persistence layer.

        Returns:
            None
        """
        last_datetimes = self.dataprovider.get_last_datetimes(self.last)
        self.persist = True
        self._generate_frames_by_datetimes(last_datetimes)


    def _generate_webp(self):
        """
        Generates an animated WebP file from the heatmap frames for the specified type and time range.

        This method retrieves the last N datetimes, generates the corresponding heatmap frames,
        sorts them by datetime, and saves them as an animated WebP file using the PIL library.

        The output file is saved to the path specified by self.output_file.

        Returns:
            None
        """
        logger.debug("Generate webp")
        last_date_times = self.dataprovider.get_last_datetimes(self.last)

        cached_frames = dict()
        if self.usedb:
            cached_frames = self.dataprovider.provide_frames_by_type_and_datetimes(heatmap=self.heatmap_type, datetimes=last_date_times)

        map_keys = set(cached_frames.keys())
        list_set = set(last_date_times)
        missing = list(list_set - map_keys)

        generated_frames = self._generate_frames_by_datetimes(missing)

        frames = cached_frames | generated_frames

        sorted_frames = dict(sorted(frames.items()))

        pil_frames = [Image.fromarray(frame) for frame in list(sorted_frames.values())]
        pil_frames[0].save(
            f"{self.output_file}",
            save_all=True,
            append_images=pil_frames[1:],
            duration=200,
            loop=0,
            quality=85  # Adjust quality (0-100)
        )

        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def generate(self):
        """
        Main entry point to generate the heatmap in the specified file format.

        Raises:
            ValueError: If the file format is not supported.
        """
        match self.file_format:
            case 'gif': self._generate_gif()
            case 'png': self._generate_png()
            case 'webp': self._generate_webp()
            case 'cache': self._generate_cache()
            case _: raise ValueError(f"Unsupported file format: {self.file_format}")

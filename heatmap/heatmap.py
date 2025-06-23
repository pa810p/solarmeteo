from concurrent.futures import ProcessPoolExecutor, as_completed

from heatmap.data_provider import TemperatureProvider, PressureProvider, PrecipitationProvider, HumidityProvider, \
    WindProvider
from heatmap.heatmap_creator import TemperatureCreator, PressureCreator, PrecipitationCreator, HumidityCreator, \
    WindCreator

import imageio.v2 as imageio
from datetime import datetime
from logging import getLogger
from tqdm import tqdm
from PIL import Image

logger = getLogger("heatmap")

class HeatMap:

    heatmaps = [
        "temperature", "pressure", "precipitation", "humidity", "wind"
    ]

    display_labels = ['Kraków', 'Warszawa', 'Gdańsk', 'Wrocław', 'Szczecin', 'Poznań', 'Suwałki', 'Zakopane', 'Łódź',
                      'Olsztyn', 'Lublin', 'Rzeszów', 'Zielona Góra', 'Białystok']

    provider_classes = {
        "temperature": (TemperatureProvider, TemperatureCreator),
        "pressure": (PressureProvider, PressureCreator),
        "precipitation": (PrecipitationProvider, PrecipitationCreator),
        "humidity": (HumidityProvider, HumidityCreator),
        "wind": (WindProvider, WindCreator)
    }


    def __init__(self, meteo_db_url, last=1, file_format='png', output_file='png', heatmap_type='temperature', max_workers=16, overwrite=True, cache=True):
        self.meteo_db_url = meteo_db_url
        self.last = last
        self.file_format = file_format
        self.output_file = output_file
        self.heatmap_type = heatmap_type
        self.max_workers = max_workers
        self.overwrite = overwrite
        self.cache = cache

        provider_class = self.provider_classes[self.heatmap_type]
        self.dataprovider = provider_class[0](meteo_db_url=self.meteo_db_url, last=self.last)
        self.heatmap_creator = provider_class[1]()

        logger.debug(f"HeatMap initialized with type: {heatmap_type}, last: {last}, file_format: {file_format}, output_file: {output_file}, max_workers: {max_workers}," \
                + "overwrite: {overwrite}, cache: {cache}")


    def _generate_frames(self):
        """
        Generates a matmplot frames for the specified type and time range.
        :return frame
        """
        if self.heatmap_type not in self.provider_classes:
            raise ValueError(f"Unsupported heatmap type: {self.heatmap_type}")

        logger.debug(f"Starting {self.heatmap_type} heatmap generation at {datetime.now()}")

        #progress_steps = fetching data + generating frames + saving file
        progress_steps = self.last + 3

        with tqdm(total=progress_steps, desc=f"Fetching data for {self.heatmap_type} figures") as pbar:
            pbar.update(1)
            provider_class = self.provider_classes[self.heatmap_type]
            dataprovider = provider_class[0](meteo_db_url=self.meteo_db_url, last=self.last)

            frames = []

            stations = dataprovider.provide()

            pbar.set_description(f"Generating {self.heatmap_type} figures")
            pbar.update(1)
            if len(stations) < self.last:
                pbar.total = len(stations) + 1
                pbar.refresh()

            heatmap_creator = provider_class[1]()

            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(heatmap_creator.generate_image, stations=stations, displaydate=displaydate, display_labels=self.display_labels)
                    for idx, (displaydate, stations) in enumerate(stations)
                ]

                for future in as_completed(futures):
                    frames.append(future.result())
                    pbar.update(1)

            pbar.set_description(f"Saving {self.heatmap_type}.{self.file_format}")
            pbar.update(1)
            return [image for datetime, image in sorted(frames, key=lambda x: x[0])]


    def _generate_frames_by_datetimes(self, datetimes):
        frames = []
        stations = self.dataprovider.provide_stations_by_datetimes(self.heatmap_type, datetimes)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.heatmap_creator.generate_image, stations=stations, displaydate=displaydate, display_labels=self.display_labels)
                for idx, (displaydate, stations) in enumerate(stations)
            ]

            for future in as_completed(futures):
                frames.append(future.result())

        return frames


    def _get_frames_from_cache(self, datetime):
        frames = self.dataprovider.provide_frames_by_type_and_datetimes(self.heatmap_type, datetime)
        return frames


    def _get_frames(self):
        last_datetimes =  self.dataprovider._get_last_datetimes(last=self.last)
        cached_frames = self._get_frames_from_cache(last_datetimes)

        map_keys = set(cached_frames.keys())
        list_set = set(last_datetimes)
        missing = list(list_set - map_keys)

        generated_frames = self._generate_frames_by_datetimes(missing)

        # if self.cache:
        #     self.dataprovider.store_frames(generated_frames)

        return [image for datetime, image in sorted(cached_frames + generated_frames, key=lambda x: x[0])]


    def _generate_gif(self):
        frames = self._generate_frames()
        imageio.mimsave(f"{self.heatmap_type}.{self.file_format}", frames, fps=5, palettesize=256, subrectangles=True)
        # imageio.mimsave("animation.mp4", sorted_frames, format="mp4", duration=0.2)  # Save as MP4# Duration per frame (sec)
        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def _generate_frame(self):
        if self.heatmap_type not in self.provider_classes:
            raise ValueError(f"Unsupported heatmap type: {self.heatmap_type}")

        logger.debug(f"Starting {self.heatmap_type} heatmap generation at {datetime.now()}")

        provider_class = self.provider_classes[self.heatmap_type]
        dataprovider = provider_class[0](meteo_db_url=self.meteo_db_url, last=1)
        stations = dataprovider.provide()

        heatmap_creator = provider_class[1]()
        generated_frame = heatmap_creator.generate_image(stations=stations[0][1], displaydate=stations[0][0], display_labels=self.display_labels)

        if generated_frame is None:
            logger.error(f"Failed to generate heatmap for {self.heatmap_type} with last={self.last}")
            return

        return generated_frame


    def _generate_png(self):
        generated_frame = self._generate_frame()

        imageio.imwrite(f"{self.output_file}.{self.file_format}", generated_frame[1])
        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def _generate_cache(self):
        last_datetimes = self.dataprovider.get_last_datetimes(self.last)
        generated_frame = self._generate_frames_by_datetimes(last_datetimes)
        self.dataprovider.store_frames(self.heatmap_type, generated_frame)


    def _generate_webp(self):
        frames = self._generate_frames()

        pil_frames = [Image.fromarray(frame) for frame in frames]
        pil_frames[0].save(
            f"{self.output_file}.{self.file_format}",
            save_all=True,
            append_images=pil_frames[1:],
            duration=200,
            loop=0,
            quality=85  # Adjust quality (0-100)
        )

        logger.debug(f"{self.heatmap_type.capitalize()} heatmap generation completed at {datetime.now()}")


    def generate(self):
        match self.file_format:
            case 'gif': self._generate_gif()
            case 'png': self._generate_png()
            case 'webp': self._generate_webp()
            case 'cache': self._generate_cache()
            case _: raise ValueError(f"Unsupported file format: {self.file_format}")





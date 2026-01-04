import unittest
from unittest import mock

from solarmeteo.heatmap.heatmap_creator import (
    HeatmapCreator,
    WindCreator,
    PrecipitationCreator,
    PM10Creator,
    PM25Creator,
)


class TestHeatmapCreators(unittest.TestCase):

    def _create_creator(self, creator_cls):
        with mock.patch.object(HeatmapCreator, "_load_poland_geometry", return_value=(None, None)):
            return creator_cls()

    def _assert_creator_defaults(self, creator_cls, label, scale_min, scale_max, vmin, vmax):
        creator = self._create_creator(creator_cls)
        stations = ['station']
        displaydate = "2025-01-01 12:00"
        display_labels = ['Warsaw']

        with mock.patch.object(HeatmapCreator, "generate_heatmap", autospec=True, return_value="generated-frame") as mock_generate:
            result = creator.generate(stations, displaydate, display_labels)

        self.assertEqual("generated-frame", result)
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertIs(args[0], creator)
        self.assertEqual(stations, kwargs['stations'])
        self.assertEqual(displaydate, kwargs['displaydate'])
        self.assertEqual(display_labels, kwargs['display_labels'])
        self.assertIs(kwargs['colormap'], creator._COLORMAP)
        self.assertEqual(label, kwargs['label'])
        self.assertEqual(scale_min, kwargs['scale_min'])
        self.assertEqual(scale_max, kwargs['scale_max'])
        self.assertEqual(vmin, kwargs['vmin'])
        self.assertEqual(vmax, kwargs['vmax'])

    def test_wind_creator_defaults(self):
        self._assert_creator_defaults(
            WindCreator,
            label="Wind (m/s)",
            scale_min=0,
            scale_max=15,
            vmin=0,
            vmax=15,
        )

    def test_precipitation_creator_defaults(self):
        self._assert_creator_defaults(
            PrecipitationCreator,
            label="Precipitation (mm)",
            scale_min=0,
            scale_max=10,
            vmin=0,
            vmax=10,
        )

    def test_pm10_creator_defaults(self):
        self._assert_creator_defaults(
            PM10Creator,
            label="PM 10 (ppm)",
            scale_min=0,
            scale_max=50,
            vmin=0,
            vmax=40,
        )

    def test_pm25_creator_defaults(self):
        self._assert_creator_defaults(
            PM25Creator,
            label="PM 2.5 (ppm)",
            scale_min=0,
            scale_max=50,
            vmin=0,
            vmax=40,
        )


if __name__ == '__main__':
    unittest.main()

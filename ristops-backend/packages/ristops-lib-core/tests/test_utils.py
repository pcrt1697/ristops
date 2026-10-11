import threading
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from ristops_lib_core.utils import Singleton, load_object, to_local_naive, to_utc_instant

ROME = ZoneInfo("Europe/Rome")


class TestSingleton:

    def test_returns_the_same_instance(self):
        class Thing(metaclass=Singleton):
            def __init__(self, value: int = 0) -> None:
                self.value = value

        first = Thing(1)
        second = Thing(2)

        assert first is second
        assert first.value == 1

    def test_each_class_has_its_own_instance(self):
        class First(metaclass=Singleton):
            pass

        class Second(metaclass=Singleton):
            pass

        assert First() is not Second()

    def test_concurrent_creation_builds_one_instance(self):
        created = []

        class Slow(metaclass=Singleton):
            def __init__(self) -> None:
                created.append(self)

        instances = []
        barrier = threading.Barrier(16)

        def build() -> None:
            barrier.wait()
            instances.append(Slow())

        threads = [threading.Thread(target=build) for _ in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(created) == 1
        assert all(instance is created[0] for instance in instances)


class TestLoadObject:

    def test_loads_an_object_from_a_module(self):
        import os.path

        assert load_object("os.path:join") is os.path.join

    @pytest.mark.parametrize("path", ["os.path", "os.path:join:extra", ""])
    def test_rejects_a_path_without_exactly_one_separator(self, path: str):
        with pytest.raises(ValueError, match="Invalid path"):
            load_object(path)

    def test_unknown_module_raises(self):
        with pytest.raises(ModuleNotFoundError):
            load_object("ristops_no_such_module:thing")

    def test_unknown_object_raises(self):
        with pytest.raises(AttributeError):
            load_object("os.path:no_such_function")


class TestTimezoneConversion:

    def test_summer_time_is_two_hours_ahead_of_utc(self):
        instant = to_utc_instant(datetime(2026, 7, 1, 12, 0), ROME)

        assert instant == datetime(2026, 7, 1, 10, 0, tzinfo=UTC)
        assert instant.tzinfo is UTC

    def test_winter_time_is_one_hour_ahead_of_utc(self):
        assert to_utc_instant(datetime(2026, 1, 15, 12, 0), ROME) == datetime(2026, 1, 15, 11, 0, tzinfo=UTC)

    def test_to_local_naive_drops_the_timezone(self):
        local = to_local_naive(datetime(2026, 7, 1, 10, 0, tzinfo=UTC), ROME)

        assert local == datetime(2026, 7, 1, 12, 0)
        assert local.tzinfo is None

    @pytest.mark.parametrize("wall_clock", [datetime(2026, 7, 1, 19, 30), datetime(2026, 12, 31, 23, 59)])
    def test_round_trip_returns_the_original_wall_clock(self, wall_clock: datetime):
        assert to_local_naive(to_utc_instant(wall_clock, ROME), ROME) == wall_clock

    def test_a_utc_wall_clock_is_unchanged(self):
        wall_clock = datetime(2026, 3, 1, 8, 15)

        assert to_utc_instant(wall_clock, UTC) == wall_clock.replace(tzinfo=UTC)

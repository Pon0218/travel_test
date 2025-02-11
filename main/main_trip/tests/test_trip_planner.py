import pytest

from feature.trip import TripPlanningSystem
from feature.trip.sample_data import DEFAULT_LOCATIONS, DEFAULT_REQUIREMENT


def test_trip_planning_basic():
    # Setup
    system = TripPlanningSystem()

    # Execute
    result = system.plan_trip(
        locations=DEFAULT_LOCATIONS,
        requirement=DEFAULT_REQUIREMENT
    )

    # Assert
    assert result is not None  # 可以加入更具體的驗證


def test_print_itinerary():
    # Setup
    system = TripPlanningSystem()
    result = system.plan_trip(
        locations=DEFAULT_LOCATIONS,
        requirement=DEFAULT_REQUIREMENT
    )

    # Execute & Assert (如果 print_itinerary 沒有回傳值，至少確保它能執行不報錯)
    try:
        system.print_itinerary(result, show_navigation=False)
        assert True
    except Exception as e:
        pytest.fail(f"print_itinerary failed with error: {str(e)}")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

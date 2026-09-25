from app.services.cv_service import CVService


def test_lightweight_defect_mapping_direct_classes():
    assert CVService._map_defect_type("tear", [10, 10, 30, 30], 100, 100) == "tear"
    assert CVService._map_defect_type("leakage", [10, 10, 30, 30], 100, 100) == "unknown"
    assert CVService._map_defect_type("anything_else", [10, 10, 30, 30], 100, 100) == "unknown"


def test_squeeze_near_corner_maps_to_crushed_corner():
    assert CVService._map_defect_type("squeeze", [0, 0, 20, 20], 100, 100) == "crushed_corner"


def test_squeeze_away_from_corner_maps_to_dent_or_crush():
    assert CVService._map_defect_type("squeeze", [35, 35, 65, 65], 100, 100) == "dent_or_crush"

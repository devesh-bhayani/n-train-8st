import pytest

from n8st.analysis.wolk_replication import ride_saved_s, score

STOPS = [
    # through-rider saving of 30 s/rider at 30 s and 70 s/rider at 70 s, 100 through-riders
    {"id": "A", "users": 100, "walkLine": 260, "walkAny": 130, "walkStation": 400,
     "rideDelta": [0, -3000, -7000]},
    {"id": "B", "users": 10, "walkLine": 130, "walkAny": 130, "walkStation": 130,
     "rideDelta": [0, -3000, -7000]},
]


def test_interpolates_between_simulated_stop_costs():
    assert ride_saved_s([0, -3000, -7000], 50) == pytest.approx(5000)
    assert ride_saved_s([0, -3000, -7000], 15) == pytest.approx(1500)


def test_ledger_and_ranking():
    out = score(STOPS, stop_cost=50, walk_weight=2, walk_speed=1.3).set_index("stop")
    # A: 5000 s saved; 100 users x 200 s walk x 2 = 40000 s added -> net -35000 s
    assert out.loc["A", "net_hrs"] == pytest.approx((5000 - 40000) / 3600)
    assert out.loc["B", "rank"] == 1

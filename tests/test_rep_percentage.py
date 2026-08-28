from __future__ import annotations
import pytest

from fitness_predictor.prediction.rep_percentage import (
    get_rep_percentage, suggested_working_weight,
    generate_rep_table, format_rep_table
)

def test_get_rep_percentage():
    assert get_rep_percentage(1) == 100.0
    assert get_rep_percentage(5) == 89.0
    assert get_rep_percentage(10) == 75.0
    assert get_rep_percentage(20) == 60.0
    assert get_rep_percentage(30) == 50.0
    assert get_rep_percentage(35) == 50.0

def test_get_rep_percentage_zero():
    with pytest.raises(ValueError):
        get_rep_percentage(0)

def test_suggested_working_weight():
    assert suggested_working_weight(200, 10) == 150.0

def test_generate_rep_table():
    table = generate_rep_table(200)
    assert len(table) == 30
    assert table[0] == (1, 100.0, 200.0)

def test_format_rep_table():
    formatted = format_rep_table(200)
    assert "Reps" in formatted
    assert "100" in formatted

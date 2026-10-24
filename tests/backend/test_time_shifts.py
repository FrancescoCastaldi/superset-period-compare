# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from datetime import datetime
from pandas import DataFrame, Series, Timestamp
from pandas.testing import assert_frame_equal
from pytest import fixture, mark  # noqa: PT013
from unittest.mock import patch

from superset.common.chart_data import ChartDataResultFormat, ChartDataResultType
from superset.common.query_context import QueryContext
from superset.common.query_context_processor import QueryContextProcessor
from superset.connectors.sqla.models import BaseDatasource
from superset.constants import TimeGrain
from superset.models.helpers import ExploreMixin

# Create processor and bind ExploreMixin methods to datasource
processor = QueryContextProcessor(
    QueryContext(
        datasource=BaseDatasource(),
        queries=[],
        result_type=ChartDataResultType.COLUMNS,
        form_data={},
        slice_=None,
        result_format=ChartDataResultFormat.CSV,
        cache_values={},
    )
)

# Bind ExploreMixin methods to datasource for testing
# Type annotation needed because _qc_datasource is typed as Explorable in protocol
_datasource: BaseDatasource = processor._qc_datasource  # type: ignore
_datasource.add_offset_join_column = ExploreMixin.add_offset_join_column.__get__(
    _datasource
)
_datasource.join_offset_dfs = ExploreMixin.join_offset_dfs.__get__(_datasource)
_datasource.is_valid_date_range = ExploreMixin.is_valid_date_range.__get__(_datasource)
_datasource._determine_join_keys = ExploreMixin._determine_join_keys.__get__(
    _datasource
)
_datasource._perform_join = ExploreMixin._perform_join.__get__(_datasource)
_datasource._apply_cleanup_logic = ExploreMixin._apply_cleanup_logic.__get__(
    _datasource
)
# Static methods don't need binding - assign directly
_datasource.generate_join_column = ExploreMixin.generate_join_column
_datasource.is_valid_date_range_static = ExploreMixin.is_valid_date_range_static

# Convenience reference for backward compatibility in tests
query_context_processor = _datasource


@fixture
def make_join_column_producer():
    def join_column_producer(row: Series, column_index: int) -> str:
        return "CUSTOM_FORMAT"

    return join_column_producer


@mark.parametrize(
    ("time_grain", "expected"),
    [
        (TimeGrain.WEEK, "2020-W01"),
        (TimeGrain.MONTH, "2020-01"),
        (TimeGrain.QUARTER, "2020-Q1"),
        (TimeGrain.YEAR, "2020"),
    ],
)
def test_join_column(time_grain: str, expected: str):
    df = DataFrame({"ds": [Timestamp("2020-01-07")]})
    column_name = "join_column"
    query_context_processor.add_offset_join_column(df, column_name, time_grain)
    result = DataFrame({"ds": [Timestamp("2020-01-07")], column_name: [expected]})
    assert_frame_equal(df, result)


def test_join_column_producer(make_join_column_producer):
    df = DataFrame({"ds": [Timestamp("2020-01-07")]})
    column_name = "join_column"
    query_context_processor.add_offset_join_column(
        df, column_name, TimeGrain.YEAR, None, make_join_column_producer
    )
    result = DataFrame(
        {"ds": [Timestamp("2020-01-07")], column_name: ["CUSTOM_FORMAT"]}
    )
    assert_frame_equal(df, result)


def test_join_offset_dfs_no_offsets():
    df = DataFrame({"A": ["2021-01-01", "2021-02-01", "2021-03-01"]})
    offset_dfs = {}
    time_grain = "YEAR"
    join_keys = ["A"]

    result = query_context_processor.join_offset_dfs(
        df, offset_dfs, time_grain, join_keys
    )

    assert_frame_equal(df, result)


def test_join_offset_dfs_with_offsets():
    df = DataFrame({"A": ["2021-01-01", "2021-02-01", "2021-03-01"]})
    offset_df = DataFrame(
        {"A": ["2021-02-01", "2021-03-01", "2021-04-01"], "B": [5, 6, 7]}
    )
    offset_dfs = {"1_YEAR": offset_df}
    time_grain = "YEAR"
    join_keys = ["A"]

    expected = DataFrame(
        {"A": ["2021-01-01", "2021-02-01", "2021-03-01"], "B": [None, 5, 6]}
    )

    result = query_context_processor.join_offset_dfs(
        df, offset_dfs, time_grain, join_keys
    )

    assert_frame_equal(expected, result)


def test_join_offset_dfs_with_multiple_offsets():
    df = DataFrame({"A": ["2021-01-01", "2021-02-01", "2021-03-01"]})
    offset_df1 = DataFrame(
        {"A": ["2021-02-01", "2021-03-01", "2021-04-01"], "B": [5, 6, 7]}
    )
    offset_df2 = DataFrame(
        {"A": ["2021-03-01", "2021-04-01", "2021-05-01"], "C": [8, 9, 10]}
    )
    offset_dfs = {"1_YEAR": offset_df1, "2_YEAR": offset_df2}
    time_grain = "YEAR"
    join_keys = ["A"]

    expected = DataFrame(
        {
            "A": ["2021-01-01", "2021-02-01", "2021-03-01"],
            "B": [None, 5, 6],
            "C": [None, None, 8],
        }
    )

    result = query_context_processor.join_offset_dfs(
        df, offset_dfs, time_grain, join_keys
    )

    assert_frame_equal(expected, result)


def test_join_offset_dfs_with_month_granularity():
    df = DataFrame(
        {
            "A": [
                "2021-01-01",
                "2021-01-15",
                "2021-02-01",
                "2021-02-15",
                "2021-03-01",
                "2021-03-15",
            ],
            "D": [1, 2, 3, 4, 5, 6],
        }
    )
    offset_df = DataFrame(
        {
            "A": [
                "2021-02-01",
                "2021-02-15",
                "2021-03-01",
                "2021-03-15",
                "2021-04-01",
                "2021-04-15",
            ],
            "B": [5, 6, 7, 8, 9, 10],
        }
    )
    offset_dfs = {"1_MONTH": offset_df}
    time_grain = "MONTH"
    join_keys = ["A"]

    expected = DataFrame(
        {
            "A": [
                "2021-01-01",
                "2021-01-15",
                "2021-02-01",
                "2021-02-15",
                "2021-03-01",
                "2021-03-15",
            ],
            "D": [1, 2, 3, 4, 5, 6],
            "B": [None, None, 5, 6, 7, 8],
        }
    )

    result = query_context_processor.join_offset_dfs(
        df, offset_dfs, time_grain, join_keys
    )

    assert_frame_equal(expected, result)


def test_join_offset_dfs_totals_query_no_dimensions():
    """
    Test time offset join for totals query with no dimension columns.

    This simulates a table chart totals query where:
    - columns=[] (no dimensions, only metrics)
    - time_offsets=["1 month ago"]
    - The dataframes only contain metric columns (no datetime column)

    The join should use the __temp_join_key__ fallback mechanism
    to properly join the offset data.
    """
    # Main totals query result - only has metric column, no datetime
    df = DataFrame({"Total Cost": [54211.76]})

    # Offset query result - renamed metric column
    offset_df = DataFrame({"Total Cost__1 month ago": [48000.50]})

    offset_dfs = {"1 month ago": offset_df}
    time_grain = "P1D"  # Daily grain from extras
    join_keys = []  # No dimension columns for totals query

    expected = DataFrame(
        {"Total Cost": [54211.76], "Total Cost__1 month ago": [48000.50]}
    )

    result = query_context_processor.join_offset_dfs(
        df, offset_dfs, time_grain, join_keys
    )

    assert_frame_equal(expected, result)


def test_join_offset_dfs_date_range_with_time_grain_month():
    """
    Test date range interval offset aligned with time grain MONTH.
    Reference: September 2026.
    Comparison: August 2026 with offset '2026-08-01 : 2026-09-01'.
    """
    df = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-15")],
            "sales": [100.0, 200.0],
        }
    )
    offset_df = DataFrame(
        {
            "order_date": [Timestamp("2026-08-01"), Timestamp("2026-08-15")],
            "sales__2026-08-01 : 2026-09-01": [80.0, 150.0],
        }
    )
    offset = "2026-08-01 : 2026-09-01"
    offset_dfs = {offset: offset_df}
    time_grain = TimeGrain.MONTH
    join_keys = ["order_date"]

    expected = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-15")],
            "sales": [100.0, 200.0],
            "sales__2026-08-01 : 2026-09-01": [80.0, 150.0],
        }
    )

    with patch("superset.models.helpers.feature_flag_manager.is_feature_enabled", return_value=True):
        result = query_context_processor.join_offset_dfs(
            df,
            offset_dfs,
            time_grain,
            join_keys,
            offset_shifts={offset: (datetime(2026, 9, 1), datetime(2026, 8, 1))},
        )
    assert_frame_equal(expected, result)


def test_join_offset_dfs_date_range_different_lengths_empty_tail():
    """
    Test date range interval offsets with different period lengths (31 vs 30 days).
    Tail row in reference without matching comparison date results in NaN.
    """
    import numpy as np

    df = DataFrame(
        {
            "order_date": [Timestamp("2026-08-30"), Timestamp("2026-08-31")],
            "sales": [300.0, 310.0],
        }
    )
    # Comparison has only 1 matching day for 2026-08-30 (which was 2026-06-30 shifted by 2 months)
    offset_df = DataFrame(
        {
            "order_date": [Timestamp("2026-06-30")],
            "sales__2026-06-01 : 2026-07-01": [250.0],
        }
    )
    offset = "2026-06-01 : 2026-07-01"
    offset_dfs = {offset: offset_df}
    time_grain = None
    join_keys = ["order_date"]

    expected = DataFrame(
        {
            "order_date": [Timestamp("2026-08-30"), Timestamp("2026-08-31")],
            "sales": [300.0, 310.0],
            "sales__2026-06-01 : 2026-07-01": [250.0, np.nan],
        }
    )

    with patch("superset.models.helpers.feature_flag_manager.is_feature_enabled", return_value=True):
        result = query_context_processor.join_offset_dfs(
            df,
            offset_dfs,
            time_grain,
            join_keys,
            offset_shifts={offset: (datetime(2026, 8, 1), datetime(2026, 6, 1))},
        )
    assert_frame_equal(expected, result)


def test_join_offset_dfs_date_range_with_dimensions():
    """Test date range interval offset with temporal and categorical dimension keys."""
    df = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-01")],
            "category": ["Hardware", "Software"],
            "sales": [500.0, 600.0],
        }
    )
    offset_df = DataFrame(
        {
            "order_date": [Timestamp("2026-08-01"), Timestamp("2026-08-01")],
            "category": ["Hardware", "Software"],
            "sales__2026-08-01 : 2026-09-01": [450.0, 550.0],
        }
    )
    offset = "2026-08-01 : 2026-09-01"
    offset_dfs = {offset: offset_df}
    time_grain = TimeGrain.MONTH
    join_keys = ["order_date", "category"]

    expected = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-01")],
            "category": ["Hardware", "Software"],
            "sales": [500.0, 600.0],
            "sales__2026-08-01 : 2026-09-01": [450.0, 550.0],
        }
    )

    with patch("superset.models.helpers.feature_flag_manager.is_feature_enabled", return_value=True):
        result = query_context_processor.join_offset_dfs(
            df,
            offset_dfs,
            time_grain,
            join_keys,
            offset_shifts={offset: (datetime(2026, 9, 1), datetime(2026, 8, 1))},
        )
    assert_frame_equal(expected, result)


def test_is_valid_date_range_with_time():
    """Test is_valid_date_range supports ISO format with time components."""
    assert query_context_processor.is_valid_date_range("2026-08-01 : 2026-09-01")
    assert query_context_processor.is_valid_date_range(
        "2026-08-01T00:00:00 : 2026-09-01T23:59:59"
    )
    assert query_context_processor.is_valid_date_range_static(
        "2026-08-01T12:00:00 : 2026-09-01T12:00:00"
    )
    assert not query_context_processor.is_valid_date_range("invalid_range")


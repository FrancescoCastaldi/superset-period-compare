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
import pandas as pd
from pandas import DataFrame, Timestamp
from pandas.testing import assert_frame_equal
from unittest.mock import MagicMock, patch

from superset.constants import EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS
from superset.common.query_object import QueryObject
from superset.models.helpers import ExploreMixin


def test_constants_override_mappings():
    """Verify time_compare and comparison_type are in override mappings."""
    assert "time_compare" in EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS
    assert EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS["time_compare"] == "time_compare"
    assert "comparison_type" in EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS
    assert EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS["comparison_type"] == "comparison_type"


def test_query_object_is_valid_date_range():
    """Verify QueryObject date range validation accepts ISO ranges with times."""
    qo = QueryObject(
        metrics=["count"],
        time_offsets=["2026-08-01 : 2026-09-01"],
    )
    assert qo._is_valid_date_range("2026-08-01 : 2026-09-01")
    assert qo._is_valid_date_range("2026-08-01T00:00:00 : 2026-09-01T23:59:59")
    assert not qo._is_valid_date_range("invalid")


def test_explore_mixin_alignment_e2e():
    """Verify ExploreMixin aligns time series offset dataframe cleanly."""
    mixin = ExploreMixin()
    df = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-02")],
            "sales": [1000.0, 1500.0],
        }
    )
    offset_df = DataFrame(
        {
            "order_date": [Timestamp("2026-08-01"), Timestamp("2026-08-02")],
            "sales__2026-08-01 : 2026-09-01": [900.0, 1400.0],
        }
    )
    offset = "2026-08-01 : 2026-09-01"
    offset_dfs = {offset: offset_df}
    join_keys = ["order_date"]
    offset_shifts = {offset: (datetime(2026, 9, 1), datetime(2026, 8, 1))}

    with patch("superset.models.helpers.feature_flag_manager.is_feature_enabled", return_value=True):
        result = mixin.join_offset_dfs(
            df,
            offset_dfs,
            time_grain=None,
            join_keys=join_keys,
            offset_shifts=offset_shifts,
        )

    expected = DataFrame(
        {
            "order_date": [Timestamp("2026-09-01"), Timestamp("2026-09-02")],
            "sales": [1000.0, 1500.0],
            "sales__2026-08-01 : 2026-09-01": [900.0, 1400.0],
        }
    )
    assert_frame_equal(result, expected)

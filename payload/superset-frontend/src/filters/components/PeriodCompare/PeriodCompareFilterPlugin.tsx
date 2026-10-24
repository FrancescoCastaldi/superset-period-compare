/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import {
  ExtraFormData,
  NO_TIME_RANGE,
  getExtensionsRegistry,
} from '@superset-ui/core';
import { styled } from '@apache-superset/core/theme';
import { useCallback, useEffect, useState } from 'react';
import DateFilterControl from 'src/explore/components/controls/DateFilterControl';
import { Select } from '@superset-ui/core/components';
import { t } from '@apache-superset/core/translation';
import { PluginFilterPeriodCompareProps } from './types';
import { FilterPluginStyle } from '../common';
import {
  resolveComparison,
  ComparisonPreset,
} from './resolveComparison';

const PeriodCompareStyles = styled(FilterPluginStyle)`
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;

  .comparison-controls {
    display: flex;
    gap: 8px;
    width: 100%;
  }

  .comparison-select {
    flex: 1;
  }
`;

const ControlContainer = styled.div<{
  validateStatus?: 'error' | 'warning' | 'info';
}>`
  display: flex;
  width: 100%;
  & > div {
    width: 100%;
  }
`;

export default function PeriodCompareFilterPlugin(
  props: PluginFilterPeriodCompareProps,
) {
  const {
    setDataMask,
    setHoveredFilter,
    unsetHoveredFilter,
    setFocusedFilter,
    unsetFocusedFilter,
    setFilterActive,
    width,
    height,
    filterState,
    inputRef,
    isOverflowingFilterBar = false,
    formData,
  } = props;

  const extensionsRegistry = getExtensionsRegistry();
  const DateFilterControlExtension = extensionsRegistry.get(
    'filter.dateFilterControl',
  );
  const DateFilterComponent = DateFilterControlExtension ?? DateFilterControl;

  const initialVal = filterState.value || {};
  const [referenceRange, setReferenceRange] = useState<string>(
    initialVal.referenceRange || NO_TIME_RANGE,
  );
  const [comparisonMode, setComparisonMode] = useState<ComparisonPreset>(
    initialVal.comparisonMode || 'none',
  );
  const [customRange, setCustomRange] = useState<string | null>(
    initialVal.customRange || null,
  );
  const [comparisonType, setComparisonType] = useState<
    'values' | 'difference' | 'percentage' | 'ratio'
  >(initialVal.comparisonType || 'values');

  const updateMask = useCallback(
    (
      refRange: string,
      mode: ComparisonPreset,
      customR: string | null,
      cType: 'values' | 'difference' | 'percentage' | 'ratio',
    ) => {
      const resolved = resolveComparison({
        referenceRange: refRange !== NO_TIME_RANGE ? refRange : '',
        comparisonMode: mode,
        customRange: customR,
      });

      const isSet =
        resolved.referenceRange && resolved.referenceRange !== NO_TIME_RANGE;
      const isComparing = resolved.isActive && !!resolved.comparisonRange;
      const referenceColumn = formData?.reference_column || formData?.groupby?.[0];
      // granularity_sqla accetta solo il nome della colonna, non una colonna ad hoc
      const referenceCol =
        typeof referenceColumn === 'string' ? referenceColumn : undefined;

      // In ExtraFormData time_compare e dichiarato string (ExtraFormDataOverrideExtras)
      // e string[] (ExtraFormDataOverrideRegular): nessun valore soddisfa entrambi.
      // Il valore reale e una lista di intervalli, come legge applyDashboardComparison.
      const extraFormData = (
        isComparing
          ? {
              time_range: resolved.referenceRange,
              time_compare: [resolved.comparisonRange!],
              comparison_type: cType,
              ...(referenceCol ? { granularity_sqla: referenceCol } : {}),
            }
          : isSet
            ? {
                time_range: resolved.referenceRange,
                ...(referenceCol ? { granularity_sqla: referenceCol } : {}),
              }
            : {}
      ) as unknown as ExtraFormData;

      setDataMask({
        extraFormData,
        filterState: {
          value: {
            referenceRange: refRange,
            comparisonMode: mode,
            customRange: customR,
            comparisonType: cType,
          },
          label: resolved.label,
        },
      });
    },
    [setDataMask, formData?.reference_column, formData?.groupby],
  );

  useEffect(() => {
    updateMask(referenceRange, comparisonMode, customRange, comparisonType);
  }, [referenceRange, comparisonMode, customRange, comparisonType, updateMask]);

  return props.formData?.inView ? (
    <PeriodCompareStyles width={width} height={height}>
      <ControlContainer
        ref={inputRef}
        validateStatus={filterState.validateStatus}
        onFocus={setFocusedFilter}
        onBlur={unsetFocusedFilter}
        onMouseEnter={setHoveredFilter}
        onMouseLeave={unsetHoveredFilter}
        tabIndex={-1}
      >
        <DateFilterComponent
          value={referenceRange}
          name={props.formData.nativeFilterId || 'time_range'}
          onChange={(val?: string) => setReferenceRange(val || NO_TIME_RANGE)}
          onOpenPopover={() => setFilterActive(true)}
          onClosePopover={() => {
            setFilterActive(false);
            unsetHoveredFilter();
            unsetFocusedFilter();
          }}
          isOverflowingFilterBar={isOverflowingFilterBar}
        />
      </ControlContainer>

      <div className="comparison-controls">
        <Select
          className="comparison-select"
          value={comparisonMode}
          onChange={(val: any) => setComparisonMode(val as ComparisonPreset)}
          options={[
            { value: 'none', label: t('No comparison') },
            { value: 'previous_period', label: t('Previous period') },
            { value: 'previous_month', label: t('Previous month') },
            { value: 'previous_year', label: t('Previous year') },
            { value: 'custom', label: t('Custom period') },
          ]}
        />

        {comparisonMode !== 'none' && (
          <Select
            className="comparison-select"
            value={comparisonType}
            onChange={(val: any) => setComparisonType(val)}
            options={[
              { value: 'values', label: t('Actual values') },
              { value: 'difference', label: t('Difference') },
              { value: 'percentage', label: t('Percentage change') },
              { value: 'ratio', label: t('Ratio') },
            ]}
          />
        )}
      </div>

      {comparisonMode === 'custom' && (
        <ControlContainer>
          <DateFilterComponent
            value={customRange || NO_TIME_RANGE}
            name={`${props.formData.nativeFilterId || 'time_range'}_custom`}
            onChange={(val?: string) => setCustomRange(val || null)}
            onOpenPopover={() => setFilterActive(true)}
            onClosePopover={() => setFilterActive(false)}
            isOverflowingFilterBar={isOverflowingFilterBar}
          />
        </ControlContainer>
      )}
    </PeriodCompareStyles>
  ) : null;
}

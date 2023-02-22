# Copyright(c) 2023 Jake Fowler
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import pandas as pd
import numpy as np
import typing as tp
from curves._common import ContractsType, _last_period, deconstruct_contract, contract_pandas_periods


class TensionSplineResults(tp.NamedTuple):
    forward_curve: pd.Series
    spline_parameters: tp.Dict


# TODO: ability to specify time zone
def tension_spline(contracts: tp.Union[ContractsType, pd.Series],
            freq: str,
            tension: float, # TODO: time varying tension. Research if this is possible.
            discount_factor: tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float],
            average_weight: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
            mult_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
            add_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
            spline_boundaries = None) \
        -> TensionSplineResults:
    num_contracts = len(contracts)
    if num_contracts < 2:
        raise ValueError('contracts argument must have length at least 2. Length of contract used is {}.'
                         .format(num_contracts))

    standardised_contracts = []  # Contract as tuples of (Period, Period, price)
    if isinstance(contracts, pd.Series):
        for period, price in contracts.items():
            start_period = period.asfreq(freq, 's')
            end_period = _last_period(period, freq)
            standardised_contracts.append((start_period, end_period, price))
    else:
        for contract in contracts:
            period, price = deconstruct_contract(contract)
            start_period, end_period = contract_pandas_periods(period, freq)
            contract_periods = pd.period_range(start_period, end_period)
            standardised_contracts.append((start_period, end_period, price))

    standardised_contracts = sorted(standardised_contracts, key=lambda x: x[0])  # Sort by start
    first_period = standardised_contracts[0][0]
    last_period = standardised_contracts[-1][1]
    if spline_boundaries is None:  # Default to use contract boundaries but check they are contiguous
        # TODO handle gaps
        for i in range(1, num_contracts):
            if standardised_contracts[i-1][1] >= standardised_contracts[i][0]:
                raise ValueError('contracts should not have delivery periods which overlap. Elements '
                                 '{} and {} have overlaps.'.format(i-1, i))
        spline_boundaries = [contract[0] for contract in standardised_contracts]
    else:
        # TODO allow len(spline_boundaries) to have 2 more elements to use as constraints instead of start/end 2nd derivative constraints
        if len(spline_boundaries) != num_contracts:
            raise ValueError('len(spline_boundaries) should equal len(contracts). However, len(spline_boundaries) '
                             'equals {} and len(contracts) equals {}.'.format(len(spline_boundaries), num_contracts))
        if spline_boundaries[0] != first_period:
            raise ValueError('First element of spline_boundaries should equal {}, the start of the first contract.'
                             ' However, it equals {}.'.format(standardised_contracts[0][0], spline_boundaries[0]))
        for i in range(1, num_contracts):
            if spline_boundaries[i] <= spline_boundaries[i-1]:
                raise ValueError('spline_boundaries should be in ascending order. Elements {} and'
                                 '{} have values {} and {}, hence are not in order.'
                                 .format(i-1, i, spline_boundaries[i-1], spline_boundaries[i]))
            if spline_boundaries[i] > last_period:
                raise ValueError('spline_boundaries should not contain items after the latest contract delivery period.'
                     'Element {} contains {} which is after the latest delivery of {}.'
                                 .format(i, spline_boundaries[i], last_period))

    result_curve_index = pd.period_range(start=first_period, end=last_period)
    num_result_curve_points = len(result_curve_index)
    # Construct linear system and solve
    matrix_size = num_result_curve_points * 2 + 2
    constraint_matrix = np.array((matrix_size, matrix_size))
    constraint_vector = np.array((matrix_size, 1))

    # Calculate vectors of coefficients
    # TODO: change these to numpy arrays?
    discount_factors = [discount_factor(key) for key in result_curve_index]
    if average_weight is None:
        average_weights = [1.0] * num_result_curve_points
    else:
        average_weights = [average_weight(key) for key in result_curve_index]

    if mult_season_adjust is None:
        mult_season_adjusts = [1.0] * num_result_curve_points
    else:
        mult_season_adjusts = [mult_season_adjust(key) for key in result_curve_index]

    if add_season_adjust is None:
        add_season_adjusts = [0.0] * num_result_curve_points
    else:
        add_season_adjusts = [add_season_adjust(key) for key in result_curve_index]

    # TODO populate constraints
    solution = np.zeros(matrix_size) # TODO set this to the actual solution

    # Read results off solution
    tension_squared = tension * tension
    result_curve_prices = np.zeros(num_result_curve_points)
    result_idx = 0
    for i, section_start in enumerate(spline_boundaries):
        z_start = solution[i * 2]
        y_start = solution[i * 2 + 1]
        z_end = solution[(i + 1) * 2]
        y_end = solution[(i + 1) * 2 + 1]
        section_end = spline_boundaries[i+1] if i <= num_result_curve_points else last_period + 1
        h = _default_time_func(section_start, section_end)
        while result_idx < num_result_curve_points and result_curve_index[result_idx] < section_start:
            period = result_curve_index[result_idx]
            time_from_section_start = _default_time_func(section_start, period)
            time_to_section_end = _default_time_func(period, section_end)
            # TODO vectorise this
            spline_val = (z_start * np.sinh(tension * time_to_section_end) +
                z_end * np.sinh(tension * time_from_section_start))/(tension_squared * np.sinh(tension * h)) + \
                ((y_start - z_start/tension_squared) * time_to_section_end +
                 (y_end - z_end/tension_squared) * time_from_section_start)/h
            result_curve_prices[result_idx] = (spline_val + add_season_adjusts[result_idx]) * \
                                              mult_season_adjusts[result_idx]
            result_idx += 1

    result_curve = pd.Series(data=result_curve_prices, index=result_curve_index)
    return TensionSplineResults(result_curve, None)


def _default_time_func(period1, period2):
    time_stamp1 = period1.start_time
    time_stamp2 = period2.start_time
    time_delta = time_stamp2 - time_stamp1
    return time_delta.total_seconds() / 60.0 / 60.0 / 24.0 / 365.0  # Convert to years with ACT/365

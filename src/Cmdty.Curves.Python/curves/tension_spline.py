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


def tension_spline(contracts: tp.Union[ContractsType, pd.Series],
            freq: str,
            tension: float,
            mult_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
            add_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
            average_weight: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
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
    if spline_boundaries is None:  # Default to use contract boundaries but check they are contiguous
        # TODO check no overlaps
        # TODO handle gaps
        spline_boundaries = [contract[0] for contract in standardised_contracts]
    else:
        if len(spline_boundaries) != num_contracts:
            raise ValueError('len(spline_boundaries) should equal len(contracts). However, len(spline_boundaries) '
                             'equals {} and len(contracts) equals {}.'.format(len(spline_boundaries), num_contracts))
        if spline_boundaries[0] != standardised_contracts[0][0]:
            raise ValueError('First element of spline_boundaries should equal {}, the start of the first contract.'
                             ' However, it equals {}.'.format(standardised_contracts[0][0], spline_boundaries[0]))
        for i in range(1, num_contracts):
            if spline_boundaries[i] <= spline_boundaries[i-1]:
                raise ValueError('')

    first_period = standardised_contracts[0][0]
    last_period = standardised_contracts[-1][1]
    result_curve_index = pd.period_range(start=first_period, end=last_period)
    num_result_curve_points = len(result_curve_index)
    # Construct linear system and solve
    matrix_size = num_result_curve_points * 2 + 2
    constraint_matrix = np.array((matrix_size, matrix_size))
    constraint_vector = np.array((matrix_size, 1))

    # TODO populate constraints
    solution = np.zeros(matrix_size) # TODO set this to the actual solution

    # Read results off solution
    result_curve_prices = np.zeros(num_result_curve_points)
    result_idx = 0
    for i in range(0, num_contracts):
        z = solution[i * 2]
        y = solution[i * 2 + 1]


    result_curve = pd.Series(data=result_curve_prices, index=result_curve_index)
    return TensionSplineResults(result_curve, None)


def _default_time_func(period1, period2):
    time_stamp1 = period1.start_time
    time_stamp2 = period2.start_time
    time_delta = time_stamp2 - time_stamp1
    return time_delta.total_seconds() / 60.0 / 60.0 / 24.0 / 365.0  # Convert to years with ACT/365

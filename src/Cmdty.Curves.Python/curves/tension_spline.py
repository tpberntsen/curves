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
                    mult_season_adjust: tp.Optional[tp.Callable[[pd.Period], float]] = None,
                    add_season_adjust: tp.Optional[tp.Callable[[pd.Period], float]] = None,
                    average_weight: tp.Optional[tp.Callable[[pd.Period], float]] = None) -> TensionSplineResults:
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

    standardised_contracts = sorted(standardised_contracts, key=lambda x: x[0])  # Sort be start
    # TODO check no overlaps
    first_period = standardised_contracts[0][0]
    last_period = standardised_contracts[-1][1]
    result_curve_index = pd.period_range(start=first_period, end=last_period)

    matrix_size = len(result_curve_index) * 2 + 2
    constraint_matrix = np.array((matrix_size, matrix_size))
    constraint_vector = np.array((matrix_size, 1))
    
    return TensionSplineResults(None, None)


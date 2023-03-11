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
from datetime import date, datetime


class SplineParameters(tp.NamedTuple):
    t: float
    z: float
    y: float


class TensionSplineResults(tp.NamedTuple):
    forward_curve: pd.Series
    spline_parameters: tp.List[SplineParameters]  # TODO change this to pd.DataFrame


_years_per_second = 1.0 / 60.0 / 60.0 / 24.0 / 365.0


def hyperbolic_tension_spline(contracts: tp.Union[ContractsType, pd.Series],
                              freq: str,
                              tension: tp.Union[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float], float],
                              discount_factor: tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float],
                              average_weight: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
                              mult_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
                              add_season_adjust: tp.Optional[tp.Callable[[tp.Union[pd.Period, pd.Timestamp]], float]] = None,
                              time_zone: tp.Optional[tp.Union[str, tp.Type['pytz.timezone'], tp.Type['dateutil.tz.tzfile']]] = None, # TODO test that pytz.timezone and dateutil.tz.tzfile type hints work as expected
                              spline_knots: tp.Optional[tp.Iterable[tp.Union[str, pd.Period, pd.Timestamp, date, datetime]]] = None
                              ) -> TensionSplineResults:
    """
    Creates a smooth interpolated curve from a collection of commodity forward/swap/futures prices using hyperbolic tension spline algorithm.

    Generally this function is used to increase the granularity of a curve from a collection of forward prices.
    The resulting curve will be smooth, and of homogenous granularity. For example a smooth monthly curve can be
    created from a collection of monthly, quarterly and season granularity forward market prices. This algorithm also
    handles input contracts with overlapping delivery periods, i.e. the bootstrapping step of forward curve construction.

    Args:
        contracts (pd.Series or iterable): The input contracts to be interpolated.
            If iterable of tuples, with each tuple describing a forward delivery period and price in one
            of the following forms:
                ([period], [price])
                ([period start], [period end], [price])
                (([period start], [period end]), [price])
            Where:
                [price] is a float, being the price of commodity delivered over the delivery period.
                [period] specifies the delivery period.
                [period start] specifies the start of the contract delivery period.
                [period end] specifies the inclusive end of the contract delivery period.
            [period], [period start] and [period end] can be any of the following types:
                pandas.Period
                pandas.Timestamp
                date
                datetime
            The delivery periods of all input contracts can be contiguous, overlapping or have gaps. If there are
            overlaps then the spline_knots argument must be provided.
        freq (str): Describes the granularity of curve being constructed using pandas Offset Alias notation.
        tension (float or callable): parameter which specifies the "tension" TODO complete this
            A higher tension value makes the curve less smooth, and closer to piecewise linear function.
        discount_factor (callable): Callable which maps from delivery period to the discount factor for the settlement
            date of this period. This function will be called with an argument of either pandas Period or Timestamp to
            describe the delivery period, at the granularity of the interpolated curve.
        average_weight (callable, optional): Mapping from pandas Period or Timestamp instances to float which describes the weighting
            that each forward period contributes to a price for delivery which spans multiple periods. The
            parameter will be at the granularity of the interpolated curve, as specified by the freq argument. An example of such weighting is
            a monthly curve (freq='M') of a commodity which delivers on every calendar day. In this example average_weight would be
            a callable which returns the number of calendar days in the month, e.g.:
                lambda p: p.asfreq('D', 'e').day
            Defaults to None, in which case each period has equal weighting.
        mult_season_adjust (callable, optional): Callable with single parameter of type pandas Period or Timestamp and return type float.
            If this argument is supplied, the value from the underlying spline function is multiplied by the result of mult_season_adjust,
            evaluated for each index period in the resulting curve.
        add_season_adjust (callable, optional): Callable with single parameter of type pandas Period or Timestamp and return type float.
            If this argument is supplied, the value from the underlying spline function has the result of add_season_adjust,
            evaluated for each index period, added to it to derive each price in the resulting curve.
        time_zone (str, pytz.timezone or dateutil.tz.tzfile, optional): Time zone applicable for the delivery periods of
            the interpolated curve. This should be specified if interpolating to higher than daily granularity (e.g. hourly)
            as time zone information is necessary to determine lost or gain hours due to clock changes. If omitted,
            defaults to UTC-like behaviour with no clock changes. It is not advisable to specify time_zone if
            interpolating to daily or lower granularity.
        spline_knots (iterable, optional): Knots of the spline constructed, i.e. the points in time which serve as boundaries
            between the piecewise hyperbolic functions. If provided, must have the same number of elements as contracts, with
            the first element equal to the start of the element of contracts with earliest delivery start. Must be provided
            by caller if contracts argument contains elements with overlapping delivery periods. Defaults to a collection of
            the starts of each input contract plus the end of the last contract.

    Returns:
            (pandas.Series, list of tuples): named tuple with the following elements:
            forward_curve: contiguous forward curve, consistent with the contracts parameter.
                This pandas.Series will have an index of type PeriodIndex or DatetimeIndex (if caller provides time_zone)
                 and freq equal to the freq parameter.
            spline_parameters: list of named tuples, with each tuple containing the time t variable and solved z_i and y_i
                spline parameters solved  at each knot.

    Notes:
        Whether time_zone is provided by the caller determines whether pandas Period or Timestamp type is used to
        represent delivery periods in the returned data and as an argument when calling callable arguments. If time_zone is not specified
        then pandas.Period type is used, as instances of Period are not time zone aware type. If time_zone is specified pandas.Timestamp
        type is as used, with the tz property of instances being set accordingly.

        See the following technical document for full details of the tension spline algorithm:
            https://github.com/cmdty/curves/blob/master/docs/tension_spline/tension_spline.pdf
    """
    num_contracts = len(contracts)
    if num_contracts < 2:
        raise ValueError('contracts argument must have length at least 2. Length of contract used is {}.'
                         .format(num_contracts))

    standardised_contracts = []  # Contract as tuples of (Period or Timestamp, Period or Timestamp, price)
    if isinstance(contracts, pd.Series):
        for period, price in contracts.items(): # TODO check this works with Series of Timestamps
            start_period = _to_index_element(period.asfreq(freq, 's'), freq, time_zone)
            end_period = _to_index_element(_last_period(period, freq), freq, time_zone)
            standardised_contracts.append((start_period, end_period, price))
    else:
        for contract in contracts:
            period, price = deconstruct_contract(contract)
            start_period, end_period = contract_pandas_periods(period, freq)
            start_period = _to_index_element(start_period, freq, time_zone)
            end_period = _to_index_element(end_period, freq, time_zone)
            standardised_contracts.append((start_period, end_period, price))

    standardised_contracts = sorted(standardised_contracts, key=lambda x: x[0])  # Sort by start
    first_period = standardised_contracts[0][0]
    last_period = max((x[1] for x in standardised_contracts))
    if spline_knots is None:  # Default to use contract boundaries but check they are contiguous
        for i in range(1, num_contracts):
            if standardised_contracts[i - 1][1] >= standardised_contracts[i][0]:
                raise ValueError('contracts should not have delivery periods which overlap. Elements '
                                 '{} and {} have overlaps.'.format(i - 1, i))
        spline_knots = [contract[0] for contract in standardised_contracts]
    else:
        # TODO allow len(spline_knots) to have 2 more elements to use as constraints instead of start/end 2nd derivative constraints
        if len(spline_knots) != num_contracts:
            raise ValueError('len(spline_knots) should equal len(contracts). However, len(spline_knots) '
                             'equals {} and len(contracts) equals {}.'.format(len(spline_knots), num_contracts))
        spline_knots = [_to_index_element(sb, freq, time_zone) for sb in spline_knots]
        if spline_knots[0] != first_period:
            raise ValueError('First element of spline_knots should equal {}, the start of the first contract.'
                             ' However, it equals {}.'.format(standardised_contracts[0][0], spline_knots[0]))
        for i in range(1, num_contracts):
            if spline_knots[i] <= spline_knots[i - 1]:
                raise ValueError('spline_knots should be in ascending order. Elements {} and'
                                 '{} have values {} and {}, hence are not in order.'
                                 .format(i - 1, i, spline_knots[i - 1], spline_knots[i]))
            if spline_knots[i] > last_period:
                raise ValueError('spline_knots should not contain items after the latest contract delivery period.'
                                 'Element {} contains {} which is after the latest delivery of {}.'
                                 .format(i, spline_knots[i], last_period))

    if time_zone is None:
        result_curve_index = pd.period_range(start=first_period, end=last_period, freq=freq)
        datetime_index = pd.date_range(start=first_period.start_time, end=last_period.start_time,
                                       freq=freq)
        t_from_start = (datetime_index - first_period.start_time).total_seconds().to_numpy() * _years_per_second
        del datetime_index
    else:
        result_curve_index = pd.date_range(start=first_period, end=last_period,
                                           freq=freq, tz=time_zone)
        t_from_start = (result_curve_index - first_period).total_seconds().to_numpy() * _years_per_second
    num_result_curve_points = len(result_curve_index)

    # Calculate vectors of coefficients
    discount_factors = np.fromiter((discount_factor(key) for key in result_curve_index), dtype=np.float64,
                                   count=num_result_curve_points)
    if average_weight is None:
        average_weights = np.ones(num_result_curve_points)
    else:
        average_weights = np.fromiter((average_weight(key) for key in result_curve_index), dtype=np.float64,
                                      count=num_result_curve_points)
    weights_times_discounts = discount_factors * average_weights
    if mult_season_adjust is None:
        mult_season_adjusts = np.ones(num_result_curve_points)
    else:
        mult_season_adjusts = np.fromiter((mult_season_adjust(key) for key in result_curve_index), dtype=np.float64,
                                          count=num_result_curve_points)
    if add_season_adjust is None:
        add_season_adjusts = np.zeros(num_result_curve_points)
    else:
        add_season_adjusts = np.fromiter((add_season_adjust(key) for key in result_curve_index), dtype=np.float64,
                                         count=num_result_curve_points)
    weights_x_discounts_x_mult_adjust = weights_times_discounts * mult_season_adjusts
    # Precalculate sinh vectors
    if isinstance(tension, float):  # TODO handle case if tension is int type?
        if tension <= 0:
            raise ValueError('tension argument should be a positive number, but value of {} has been provided.'
                             .format(tension))

        def get_tension(p) -> float:
            return tension
    else:
        def get_tension(p) -> float:
            tension_val = tension(p)
            if tension_val <= 0:
                raise ValueError('If callable, tension argument should always returns positive number, but value of {} '
                                 'has been returned for period {}.'
                                 .format(tension_val, p))
            return tension_val

    freq_offset = pd.tseries.frequencies.to_offset(freq)

    def int_index(del_period):
        return round((del_period - first_period) / freq_offset)

    num_sections = len(spline_knots)
    matrix_size = num_sections * 2 + 2
    # Using np.zeros rather than empty because easier to understand when debugging
    h_is = np.zeros((num_sections,))
    tension_by_section = np.zeros((num_sections,))

    section_period_indices = [] # 2-tuples of indices for start and (exclusive) end indices of result periods for each section
    last_section_end_idx = 0
    # TODO vectorise below loop?
    for i, section_start in enumerate(spline_knots):
        section_end = last_period if i == num_sections - 1 else spline_knots[i + 1]
        h_is[i] = _default_time_func(section_start, section_end)
        tension_by_section[i] = get_tension(section_start)
        section_start_idx = last_section_end_idx
        section_end_idx = None if i == num_sections - 1 else int_index(spline_knots[i + 1])
        last_section_end_idx = section_end_idx
        section_period_indices.append((section_start_idx, section_end_idx))

    h_is_expanded = _create_expanded_np_array(h_is, num_result_curve_points, section_period_indices)
    section_end_times = np.cumsum(h_is)
    section_end_t_expanded = _create_expanded_np_array(section_end_times, num_result_curve_points, section_period_indices)
    t_to_section_end = section_end_t_expanded - t_from_start
    t_from_section_start = h_is_expanded - t_to_section_end

    tensions_expanded = _create_expanded_np_array(tension_by_section, num_result_curve_points, section_period_indices)

    tau_sinh = np.sinh(tension_by_section * h_is) * tension_by_section
    tau_sqrd_sinh = tau_sinh * tension_by_section
    tension_by_section_sqrd = tension_by_section * tension_by_section
    tau_sqrd_hi = tension_by_section_sqrd * h_is
    cosh_tau_hi = np.cosh(tension_by_section * h_is)

    tau_sqrd_sinh_expanded = _create_expanded_np_array(tau_sqrd_sinh, num_result_curve_points, section_period_indices)
    tau_sqrd_hi_expanded = _create_expanded_np_array(tau_sqrd_hi, num_result_curve_points, section_period_indices)
    sinh_tau_t_from_start = np.sinh(t_from_section_start * tensions_expanded)
    sinh_tau_t_to_end = np.sinh(t_to_section_end * tensions_expanded)

    # TODO: research allocation-efficient vectorisation with numpy. Probably just make operations in-place.
    # TODO: continuous extension of zi_coeffs and zi_minus1_coeffs if tension is zero?
    # Coefficients used in forward price constraint
    zi_coeffs = (sinh_tau_t_from_start / tau_sqrd_sinh_expanded - t_from_section_start / tau_sqrd_hi_expanded) \
                * weights_x_discounts_x_mult_adjust
    zi_minus1_coeffs = (sinh_tau_t_to_end / tau_sqrd_sinh_expanded - t_to_section_end / tau_sqrd_hi_expanded) \
                * weights_x_discounts_x_mult_adjust
    yi_coeffs = (t_from_section_start / h_is_expanded) * weights_x_discounts_x_mult_adjust
    yi_minus1_coeffs = (t_to_section_end / h_is_expanded) * weights_x_discounts_x_mult_adjust

    # Populate constraint vector
    constraint_vector = np.zeros((matrix_size, 1))
    # Looking online it seems that Pandas index searching isn't particularly efficient, so do this manually
    for i, (start, end, price) in enumerate(standardised_contracts):
        contract_start_idx = int_index(start)
        contract_end_idx = int_index(end) + 1
        weights_times_discounts_slice = weights_times_discounts[contract_start_idx:contract_end_idx]
        add_season_adjusts_slice = add_season_adjusts[contract_start_idx:contract_end_idx]
        weights_x_discounts_x_mult_adjust_slice = weights_x_discounts_x_mult_adjust[contract_start_idx:contract_end_idx]
        constraint_vector[i+1] = price * np.sum(weights_times_discounts_slice) - \
                               np.dot(add_season_adjusts_slice, weights_x_discounts_x_mult_adjust_slice)

    # Populate constraint matrix
    constraint_matrix = np.zeros((matrix_size, matrix_size))  # TODO: make this banded matrix
    constraint_matrix[0, 0] = 1.0  # 2nd derivative zero at start
    constraint_matrix[-1, -2] = 1.0  # 2nd derivative zero at end
    # Forward price constraints
    # This is made more complicated by flexibility of allowing contracts and spline sections to differ
    first_spline_section_idx = 0
    for contract_idx, (contract_start, contract_end, price) in enumerate(standardised_contracts):
        # Find first spline section
        # TODO use quicker search than this linear scan
        while first_spline_section_idx < num_sections and contract_start > spline_knots[first_spline_section_idx]:
            first_spline_section_idx += 1
        # Loop through spline sections which overlap contract
        spline_boundary_idx = first_spline_section_idx
        while spline_boundary_idx < num_sections and spline_knots[spline_boundary_idx] <= contract_end:
            section_start = spline_knots[spline_boundary_idx]
            section_end = spline_knots[spline_boundary_idx + 1] - freq_offset if spline_boundary_idx < num_sections - 1 else last_period
            contract_section_start_period = contract_start if contract_start >= section_start else section_start
            contract_section_end_period = contract_end if contract_end <= section_end else section_end
            contract_section_start_idx = int_index(contract_section_start_period)
            contract_section_end_idx = int_index(contract_section_end_period) + 1
            # Forward price constraints
            constraint_matrix[contract_idx + 1, spline_boundary_idx * 2] += np.sum(zi_minus1_coeffs[contract_section_start_idx:contract_section_end_idx])
            constraint_matrix[contract_idx + 1, spline_boundary_idx * 2 + 1] += np.sum(yi_minus1_coeffs[contract_section_start_idx:contract_section_end_idx])
            constraint_matrix[contract_idx + 1, spline_boundary_idx * 2 + 2] += np.sum(zi_coeffs[contract_section_start_idx:contract_section_end_idx])
            constraint_matrix[contract_idx + 1, spline_boundary_idx * 2 + 3] += np.sum(yi_coeffs[contract_section_start_idx:contract_section_end_idx])
            spline_boundary_idx += 1

    # First derivative continuity constraints
    one_over_h_tau_sqrd = 1.0 / (h_is * tension_by_section * tension_by_section)
    for section_idx in range(0, num_sections - 1):
        row_idx = num_contracts + section_idx + 1
        # TODO doc using 1-based indexing for sections gets annoying now
        next_section_idx = section_idx + 1
        # TODO vectorise these outside of the loop?
        constraint_matrix[row_idx, section_idx * 2] -= (one_over_h_tau_sqrd[section_idx] - 1.0 / tau_sinh[section_idx])  # deriv_z_i_minus2_coff
        constraint_matrix[row_idx, section_idx * 2 + 1] += 1/h_is[section_idx] # deriv_y_i_minus2_coff
        constraint_matrix[row_idx, section_idx * 2 + 2] += one_over_h_tau_sqrd[next_section_idx] - cosh_tau_hi[next_section_idx] / tau_sinh[next_section_idx]  \
                        - cosh_tau_hi[section_idx]/tau_sinh[section_idx] + one_over_h_tau_sqrd[section_idx] # deriv_z_i_minus1_coff
        constraint_matrix[row_idx, section_idx * 2 + 3] -= (1/h_is[next_section_idx] + 1/h_is[section_idx]) # deriv_y_i_minus1_coff
        constraint_matrix[row_idx, section_idx * 2 + 4] += 1.0/tau_sinh[next_section_idx] - one_over_h_tau_sqrd[next_section_idx] # deriv_z_i_coff
        constraint_matrix[row_idx, section_idx * 2 + 5] += 1/h_is[next_section_idx] # deriv_y_i_coff

    # TODO IMPORTANT: GET RID OF THIS TEMPORARY HACK TO ADD ONE MORE CONSTRAINT
    constraint_matrix[-2, -4] = 1  # Temporary hack to set 2nd derive at last knot to zero
    solution = np.linalg.solve(constraint_matrix, constraint_vector)

    # Read results off solution
    knot_t = 0.0
    spline_vals = np.zeros(num_result_curve_points)
    spline_parameters = []
    for i, section_start in enumerate(spline_knots):
        z_start = solution[i * 2][0]
        y_start = solution[i * 2 + 1][0]
        z_end = solution[i * 2 + 2][0]
        y_end = solution[i * 2 + 3][0]

        spline_parameters.append(SplineParameters(knot_t, z_start, y_start))
        knot_t += h_is[i]
        if i == num_sections - 1:
            spline_parameters.append(SplineParameters(knot_t, z_end, y_end))
        tension_squared = tension_by_section_sqrd[i]
        start_idx, end_idx = section_period_indices[i]
        spline_vals[start_idx:end_idx] =(z_start * sinh_tau_t_to_end[start_idx:end_idx] + z_end * sinh_tau_t_from_start[start_idx:end_idx]) \
                    / tau_sqrd_sinh_expanded[start_idx:end_idx] + \
                         ((y_start - z_start / tension_squared) * t_to_section_end[start_idx:end_idx] +
                          (y_end - z_end / tension_squared) * t_from_section_start[start_idx:end_idx]) / h_is_expanded[start_idx:end_idx]
    # TODO: handling of periods with zero weight, e.g. power offpeak hours when interpolating peak. Could be:
    # periods aren't included in index
    # NaN price for zero-weight periods
    # Current behaviour: zero price
    # Controls this behaviour with argument?
    # TODO: skip adjustments if these aren't provided
    result_curve_prices = (spline_vals + add_season_adjusts) * mult_season_adjusts
    result_curve = pd.Series(data=result_curve_prices, index=result_curve_index)
    return TensionSplineResults(result_curve, spline_parameters)


def _default_time_func(period1, period2):
    time_stamp1 = period1.start_time if isinstance(period1, pd.Period) else period1
    time_stamp2 = period2.start_time if isinstance(period2, pd.Period) else period2
    time_delta = time_stamp2 - time_stamp1
    return time_delta.total_seconds() * _years_per_second  # Convert to years with ACT/365


def _to_index_element(period, freq, tz):
    if tz is None:
        return pd.Period(period, freq=freq)
    else:
        if isinstance(period, pd.Period):
            return period.to_timestamp().tz_localize(tz)
        else:
            return pd.Timestamp(period, tz=tz)


def _create_expanded_np_array(array_from, size, copy_slice_indices):
    array_to = np.zeros((size,))
    for i in range(len(array_from)):
        slice_indices = copy_slice_indices[i]
        array_to[slice_indices[0]:slice_indices[1]] = array_from[i]
    return array_to

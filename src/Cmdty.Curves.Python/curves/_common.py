# Copyright(c) 2019 Jake Fowler
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

import clr
from System import DateTime
import System as dotnet
import pandas as pd
import re
from datetime import datetime, date
from typing import Union, Tuple, Iterable
import typing as tp # TODO consolidate with above line
from pathlib import Path
clr.AddReference(str(Path("curves/lib/Cmdty.TimePeriodValueTypes")))
from Cmdty.TimePeriodValueTypes import QuarterHour, HalfHour, Hour, Day, Month, Quarter, TimePeriodFactory

clr.AddReference(str(Path('curves/lib/Cmdty.TimeSeries')))
import Cmdty.TimeSeries as ts


FREQ_TO_PERIOD_TYPE = {
        "15min" : QuarterHour,
        "30min" : HalfHour,
        "H" : Hour,
        "D" : Day,
        "M" : Month,
        "Q" : Quarter
    }
""" dict of str: .NET time period type.
Each item describes an allowable granularity of curves constructed, as specified by the 
freq parameter in the curves public methods.

The keys represent the pandas Offset Alias which describe the granularity, and will generally be used
    as the freq of the pandas Series objects returned by the curve construction methods.
The values are the associated .NET time period types used in behind-the-scenes calculations.
"""


def transform_time_func(freq, py_time_func):
    def wrapper_time_func(net_time_period):
        pandas_period = net_time_period_to_pandas_period(net_time_period, freq)
        return py_time_func(pandas_period)
    return wrapper_time_func


def transform_two_period_func(freq, py_two_period_func):
    def wrapper_time_func(net_time_period1, net_time_period2):
        pandas_period1 = net_time_period_to_pandas_period(net_time_period1, freq)
        pandas_period2 = net_time_period_to_pandas_period(net_time_period2, freq)
        return py_two_period_func(pandas_period1, pandas_period2)
    return wrapper_time_func


def net_datetime_to_py_datetime(net_datetime):
    return datetime(net_datetime.Year, net_datetime.Month, net_datetime.Day, net_datetime.Hour, net_datetime.Minute, net_datetime.Second, net_datetime.Millisecond * 1000)


def net_time_series_to_pandas_series(net_time_series, freq):
    """Converts an instance of class Cmdty.TimeSeries.TimeSeries to a pandas Series"""
    curve_start = net_time_series.Indices[0].Start
    curve_start_datetime = net_datetime_to_py_datetime(curve_start)
    index = pd.period_range(start=curve_start_datetime, freq=freq, periods=net_time_series.Count)
    prices = [net_time_series.Data[idx] for idx in range(0, net_time_series.Count)]
    return pd.Series(prices, index)


def net_time_period_to_pandas_period(net_time_period, freq):
    start_datetime = net_datetime_to_py_datetime(net_time_period.Start)
    return pd.Period(start_datetime, freq=freq)


def deconstruct_contract(contract):
    if len(contract) == 2:
        (period, price) = contract
    elif len(contract) == 3:
        (period, price) = ((contract[0], contract[1]), contract[2])
    else:
        raise ValueError("contract tuple must have either 2 or 3 items")
    return period, price


def contract_period(input_period, freq, time_period_type):
    """Converts inputs specifying the contract period from Python types to .NET TimePeriod Start and End"""
    if isinstance(input_period, tuple):
        start = input_period[0]
        end = input_period[1]
    else:
        if isinstance(input_period, pd.Period):
            start = input_period.asfreq(freq, 's')
            end = _last_period(input_period, freq)
        else:
            start = input_period
            end = input_period
    start_net = from_datetime_like(start, time_period_type)
    end_net = from_datetime_like(end, time_period_type)
    return start_net, end_net


def _last_period(period, freq):
    """Find the last pandas Period instance of a specific frequency within a Period instance"""
    if not freq[0].isdigit():
        return period.asfreq(freq, 'e')
    m = re.match("(\d+)(\w+)", freq)
    num = int(m.group(1))
    sub_freq = m.group(2)
    return (period.asfreq(sub_freq, 'e') - num + 1).asfreq(freq)


def from_datetime_like(datetime_like, time_period_type):
    """ Converts either a pandas Period, datetime or date to a .NET Time Period"""
    if hasattr(datetime_like, 'hour'):
        time_args = (datetime_like.hour, datetime_like.minute, datetime_like.second)
    else:
        time_args = (0, 0, 0)
    date_time = DateTime(datetime_like.year, datetime_like.month, datetime_like.day, *time_args)
    return TimePeriodFactory.FromDateTime[time_period_type](date_time)


def series_to_double_time_series(series, time_period_type):
    """Converts an instance of pandas Series to a Cmdty.TimeSeries.TimeSeries type with Double data type."""
    series_len = len(series)
    net_indices = dotnet.Array.CreateInstance(time_period_type, series_len)
    net_values = dotnet.Array.CreateInstance(dotnet.Double, series_len)
    for i in range(series_len):
        net_indices[i] = from_datetime_like(series.index[i], time_period_type)
        net_values[i] = series.values[i]
    return ts.DoubleTimeSeries[time_period_type](net_indices, net_values)


ContractsType = Iterable[Union[Tuple[date, float], Tuple[datetime, float], Tuple[pd.Period, float],
                               Tuple[pd.Timestamp, float],
                               Tuple[date, date, float], Tuple[datetime, datetime, float],
                               Tuple[pd.Period, pd.Period, float],
                               Tuple[pd.Timestamp, pd.Timestamp, float],
                               Tuple[Tuple[date, date], float], Tuple[Tuple[datetime, datetime], float],
                               Tuple[Tuple[pd.Period, pd.Period], float], Tuple[Tuple[pd.Timestamp, pd.Timestamp], float]]]

ShapingTypes = Iterable[
    Union[Tuple[pd.Period, pd.Period, float], Tuple[date, date, float], Tuple[datetime, datetime, float],
          Tuple[Tuple[pd.Period, pd.Period], float], Tuple[Tuple[date, date], float], Tuple[
              Tuple[datetime, datetime], float]]]


def contract_pandas_periods(input_period, freq) -> tp.Tuple[pd.Period, pd.Period]:
    if isinstance(input_period, tuple):
        start = pd.Period(input_period[0], freq=freq)
        end = pd.Period(input_period[1], freq=freq)
        if start > end: # TODO push this up to get better error message about which argument is causing this?
            raise ValueError('Contract start must be earlier than or equal to contract end. '
                             'However start is {} and end is {}.'.format(start, end))
    else:
        if isinstance(input_period, pd.Period):
            start = input_period.asfreq(freq, 's')
            end = _last_period(input_period, freq)
        else:
            start = pd.Period(input_period, freq=freq)
            end = pd.Period(input_period, freq=freq)
    return start, end

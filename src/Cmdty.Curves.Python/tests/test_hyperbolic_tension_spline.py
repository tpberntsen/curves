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
from datetime import date
import unittest
import pandas as pd
from datetime import date, datetime
from curves import hyperbolic_tension_spline
from curves.contract_period import quarter, winter, summer, gas_year
from math import exp
from tests._test_common import weighted_average_slice_curve
from curves._common import deconstruct_contract


interest_rate = 0.046
val_date = pd.Timestamp(2018, 12, 31)


def discount_factor(delivery_period):
    delivery_period = delivery_period if isinstance(delivery_period, pd.Period) else delivery_period.to_timestamp()
    settle_date = delivery_period.asfreq('M').asfreq('D', 'end') + 20
    time_to_settle = (settle_date.start_time - val_date).days / 365.0
    return exp(-time_to_settle * interest_rate)


class TestHyperbolicTensionSpline(unittest.TestCase):
    flat_tension = 0.75

    contracts_list = [
        (date(2019, 1, 1), 31.39),  # date
        ((date(2019, 1, 2), date(2019, 1, 2)), 32.7),
        ((date(2019, 1, 3), date(2019, 1, 7)), 29.3),
        ((date(2019, 1, 8), date(2019, 1, 31)), 24.66),
        (quarter(year=2019, quarter_num=2), 18.3),
        (quarter(year=2019, quarter_num=3), 17.1),
        (winter(2019), 22.4),
        (summer(2020), 19.9),
        (gas_year(2020), 20.01)
    ]
    contracts_series = pd.Series(data=[23.53, 53.245, 35.56, 39.242, 19.024],
                                 index=pd.period_range(start=pd.Period(year=2020, month=5, freq='M'), periods=5))
    test_case_data = [
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "discount_factor": discount_factor
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "discount_factor": discount_factor
        },
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "discount_factor": discount_factor
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "discount_factor": discount_factor
        },
        {
            "freq": "30min",
            "contracts": [
                (datetime(2019, 6, 7, hour=7, minute=0), datetime(2019, 6, 7, hour=8, minute=30), 56.84),
                (datetime(2019, 6, 7, hour=9, minute=0), datetime(2019, 6, 7, hour=18, minute=0), 57.05),
                (datetime(2019, 6, 7, hour=18, minute=30), datetime(2019, 6, 7, hour=23, minute=30), 60.11),
            ],
            "tension": flat_tension,
            "discount_factor": discount_factor
        },
        {
            "freq": "15min",
            "contracts": [
                (datetime(2019, 6, 7, hour=7, minute=0), datetime(2019, 6, 7, hour=8, minute=45), 56.84),
                (datetime(2019, 6, 7, hour=9, minute=0), datetime(2019, 6, 7, hour=18, minute=0), 57.05),
                (datetime(2019, 6, 7, hour=18, minute=15), datetime(2019, 6, 7, hour=23, minute=45), 60.11),
            ],
            "tension": flat_tension,
            "discount_factor": discount_factor
        }]

    # TODO properly parameterise these tests
    def test_hyperbolic_tension_spline_averages_back_to_inputs(self):
        for test_data in self.test_case_data:
            interp_curve, _ = hyperbolic_tension_spline(**test_data)
            average_weight = test_data['average_weight'] if 'average_weight' in test_data else lambda x: 1.0
            discount_factor_func = test_data['discount_factor']

            def discounted_average_weight(del_period):
                discount_factor = discount_factor_func(del_period)
                return average_weight(del_period) * discount_factor

            test_contracts = test_data['contracts']
            if isinstance(test_contracts, pd.Series):
                for period, contract_price in test_contracts.items():
                    curve_average_price = weighted_average_slice_curve(interp_curve, test_data['freq'], period,
                                                                       discounted_average_weight)
                    self.assertAlmostEqual(curve_average_price, contract_price, delta=1E-10)
            else:
                for contract in test_contracts:
                    (period, contract_price) = deconstruct_contract(contract)
                    curve_average_price = weighted_average_slice_curve(interp_curve, test_data['freq'], period,
                                                                       discounted_average_weight)
                    self.assertAlmostEqual(curve_average_price, contract_price, delta=1E-8)

    # def test_inputs_constant_outputs_constant(self):
    #     # Arrange
    #     freq = 'D'
    #     time_zone = None  # 'Europe/London'
    #     flat_price = 10.5
    #     num_contracts = 3
    #     monthly_index = pd.period_range(start='2023-04-01', periods=num_contracts, freq='M')
    #     monthly_curve = pd.Series(data=[10.2, 11.69, 10.98], index=monthly_index)
    #
    #     def tension(p):
    #         return 0.05
    #
    #     # Act
    #     daily_curve, spline_params = tension_spline(monthly_curve, freq=freq, tension=tension, time_zone=time_zone,
    #                                                 discount_factor=lambda x: 1.0)
    #     # Assert
    #     expect_daily_curve = monthly_curve.resample(freq).fillna('pad')
    #     pd.testing.assert_series_equal(daily_curve, expect_daily_curve)
    #     self.assertEqual(len(spline_params), len(monthly_curve) + 1)

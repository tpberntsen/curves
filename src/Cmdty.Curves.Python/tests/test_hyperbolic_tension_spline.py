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
from curves import contract_period as cp
from math import exp
from tests._test_common import weighted_average_slice_curve
from curves._common import deconstruct_contract

interest_rate = 0.046
val_date = pd.Timestamp(2018, 12, 31)


def discount_factor(delivery_period):
    delivery_period = delivery_period if isinstance(delivery_period, pd.Period) else pd.Period(delivery_period,
                                                                                               freq='D')
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
        (cp.quarter(year=2019, quarter_num=2), 18.3),
        (cp.quarter(year=2019, quarter_num=3), 17.1),
        (cp.winter(2019), 22.4),
        (cp.summer(2020), 19.9),
        (cp.gas_year(2020), 20.01)
    ]
    contracts_series = pd.Series(data=[23.53, 53.245, 35.56, 39.242, 19.024],
                                 index=pd.period_range(start=pd.Period(year=2020, month=5, freq='M'), periods=5))
    daily_test_case_data = [
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "back_1st_deriv": -0.3
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "discount_factor": discount_factor,
        },
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "back_1st_deriv": -0.3
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "discount_factor": discount_factor,
        }
    ]

    intraday_test_case_data = [
        {
            "freq": "30min",
            "contracts": [
                (datetime(2019, 3, 31, hour=0, minute=0), datetime(2019, 3, 31, hour=8, minute=30), 56.84),
                (datetime(2019, 3, 31, hour=9, minute=0), datetime(2019, 3, 31, hour=18, minute=0), 57.05),
                (datetime(2019, 3, 31, hour=18, minute=30), datetime(2019, 3, 31, hour=23, minute=30), 60.11),
                # Covers clock change
                (datetime(2019, 4, 1, hour=0, minute=0), datetime(2019, 4, 1, hour=12, minute=30), 43.11),
            ],
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "time_zone": 'Europe/London',
            # "back_1st_deriv" : 0.0 TODO figure out why adding this constrain causes bigger error
        },
        {
            "freq": "15min",
            "contracts": [
                (datetime(2019, 6, 7, hour=7, minute=0), datetime(2019, 6, 7, hour=8, minute=45), 56.84),
                (datetime(2019, 6, 7, hour=9, minute=0), datetime(2019, 6, 7, hour=18, minute=0), 57.05),
                (datetime(2019, 6, 7, hour=18, minute=15), datetime(2019, 6, 7, hour=23, minute=45), 60.11),
            ],
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "time_zone": 'Europe/Paris',
            "back_1st_deriv": -0.3
        }
    ]

    # TODO properly parameterise these tests
    def test_hyperbolic_tension_spline_daily_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.daily_test_case_data, 1E-9)

    # TODO look into why bigger tolerance required here. Matrix gets poorly conditioned?
    def test_hyperbolic_tension_spline_intraday_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.intraday_test_case_data, 1E-6)

    def test_hyperbolic_tension_spline_contracts_overlap_averages_back_to_inputs(self):
        inputs = [
            {
                "freq": 'D',
                "contracts": [
                    (cp.jan(2020), 21.3),
                    (cp.q_1(2020), 18.66),
                ],
                "spline_knots": ['2020-01-01', '2020-02-01'],
                "tension": 12.5,
                "discount_factor": discount_factor,
                "back_1st_deriv": -0.3
            },
        ]
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-12)

    def test_hyperbolic_tension_spline_knots_specified_averages_back_to_inputs(self):
        inputs = [
            {
                "freq": 'D',
                "contracts": [
                    (cp.q_1(2020), 18.66),
                    (cp.q_2(2020), 19.68),
                ],
                "spline_knots": ['2020-01-01', '2020-02-15'],
                "tension": 12.5,
                "discount_factor": discount_factor
            },
        {
            "freq": 'D',
            "contracts": [
                (cp.cal_year(2020), 21.3),
                (cp.q_1(2020), 18.66),
                (cp.q_2(2020), 19.65),
                (cp.jul(2020), 15.66)
            ],
            "spline_knots": ['2020-01-01', '2020-02-15', '2020-07-12', '2020-12-02'],
            "tension": 12.5,
            "discount_factor": discount_factor
        }
        ]
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-12)

    def _interpolate_and_assert_average_back_to_inputs(self, test_case_data, tol):
        for test_data in test_case_data:
            interp_curve, _ = hyperbolic_tension_spline(**test_data)
            average_weight = test_data['average_weight'] if 'average_weight' in test_data else lambda x: 1.0
            if 'discount_factor' in test_data:
                discount_factor_func = test_data['discount_factor']
            else:
                def discount_factor_func(p):  # PyCharm doesn't like lambdas for some reason
                    return 1.0

            def discounted_average_weight(del_period):
                df = discount_factor_func(del_period)
                return average_weight(del_period) * df

            test_contracts = test_data['contracts']
            if isinstance(test_contracts, pd.Series):
                for period, contract_price in test_contracts.items():
                    curve_average_price = weighted_average_slice_curve(interp_curve, test_data['freq'], period,
                                                                       discounted_average_weight)
                    self.assertAlmostEqual(curve_average_price, contract_price, delta=tol)
            else:
                for contract in test_contracts:
                    (period, contract_price) = deconstruct_contract(contract)
                    curve_average_price = weighted_average_slice_curve(interp_curve, test_data['freq'], period,
                                                                       discounted_average_weight)
                    self.assertAlmostEqual(curve_average_price, contract_price, delta=tol)

    @unittest.skip('This test is currently just used for investigations.')
    def test_inputs_constant_outputs_constant(self):
        # Arrange
        freq = '15min'
        time_zone = None  # 'Europe/London'
        flat_price = 10.5
        num_contracts = 300
        monthly_index = pd.period_range(start='2023-04-01', periods=num_contracts, freq='M')
        monthly_curve = pd.Series(data=[10.2, 11.69, 10.98] * 100, index=monthly_index)
        back_1st_derive = -0.1

        def tension(p):
            return 0.05

        # Act
        daily_curve, spline_params = hyperbolic_tension_spline(monthly_curve, freq=freq, tension=tension, time_zone=time_zone,
                                                               discount_factor=lambda x: 1.0, back_1st_deriv=back_1st_derive)
        print('Curve length:')
        print(len(daily_curve))
        # Assert
        # expect_daily_curve = monthly_curve.resample(freq).fillna('pad')
        # pd.testing.assert_series_equal(daily_curve, expect_daily_curve)
        # self.assertEqual(len(spline_params), len(monthly_curve) + 1)

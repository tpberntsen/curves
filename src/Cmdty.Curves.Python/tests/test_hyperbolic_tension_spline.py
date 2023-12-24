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

import unittest
import pandas as pd
import numpy as np
from datetime import date, datetime
from curves import hyperbolic_tension_spline, KnotPositions
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
        (date(2019, 1, 1), 31.39),
        ((date(2019, 1, 2), date(2019, 1, 2)), 32.7),
        ((date(2019, 1, 1), date(2019, 1, 7)), 29.3),
        ((date(2019, 1, 1), date(2019, 1, 31)), 31.66),
        (cp.quarter(year=2019, quarter_num=1), 18.3),
        (cp.quarter(year=2019, quarter_num=2), 17.1),
        (cp.summer(2019), 19.9),
        (cp.winter(2019), 22.4),
        (cp.summer(2020), 19.9),
        (cp.gas_year(2020), 20.01)
    ]
    # TODO add str to shaping_spreads and shaping_ratios once type hints have been updated
    shaping_spreads = [
        (cp.winter(2020), cp.summer(2021), 4.21),
        ((date(2020, 12, 1), date(2020, 12, 31)), cp.jan(2021), -0.87)
    ]
    shaping_ratios = [
        (cp.q_1(2020), cp.q_4(2019), 1.08)
        # TODO add more
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
            "front_1st_deriv": 0.56,
            "back_1st_deriv": -0.3,
            "shaping_spreads": shaping_spreads,
            "shaping_ratios": shaping_ratios
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "discount_factor": discount_factor,
            "front_1st_deriv": 0.56,
        },
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "back_1st_deriv": -0.3,
            "shaping_spreads" : shaping_spreads,
            "shaping_ratios" : shaping_ratios
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
                (datetime(2019, 3, 31, hour=0, minute=0), datetime(2019, 3, 31, hour=18, minute=0), 57.05),
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
                (datetime(2019, 6, 7, hour=9, minute=0), datetime(2019, 6, 7, hour=23, minute=45), 60.11),
            ],
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "time_zone": 'Europe/Paris',
            "back_1st_deriv": -0.3,
        }
    ]

    # TODO properly parameterise these tests
    def test_hyperbolic_tension_spline_daily_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.daily_test_case_data, 1E-7)

    # TODO look into why bigger tolerance required here. Matrix gets poorly conditioned?
    def test_hyperbolic_tension_spline_intraday_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.intraday_test_case_data, 1E-8)

    def test_hyperbolic_tension_spline_knots_collection_averages_back_to_inputs(self):
        inputs = [
            {
                "freq": 'D',
                "contracts": [
                    (cp.q_1(2020), 18.66),
                    (cp.q_2(2020), 19.68),
                ],
                "knot_positions": KnotPositions.NONE,
                "knots": ['2020-02-15'],
                "tension": 12.5,
                "discount_factor": discount_factor,
            },
            {
                "freq": 'D',
                "contracts": [
                    (cp.cal_year(2020), 21.3),
                    (cp.q_1(2020), 18.66),
                    (cp.q_2(2020), 19.65),
                    (cp.jul(2020), 15.66)
                ],
                "knot_positions": KnotPositions.NONE,
                "knots": ['2020-02-15', '2020-07-12', '2020-12-02'],
                "tension": 12.5,
                "discount_factor": discount_factor,
            }
        ]
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-12)

    def test_hyperbolic_tension_spline_knots_enum_averages_back_to_inputs(self):
        inputs = [
            {
                "freq": 'D',
                "contracts": [
                    (cp.q_1(2020), 18.66),
                    (cp.q_2(2020), 19.68),
                ],
                "knot_positions": KnotPositions.CONTRACT_CENTRE,
                "tension": 12.5,
                "discount_factor": discount_factor,
            },
            {
                "freq": 'D',
                "contracts": [
                    (cp.cal_year(2020), 21.3),
                    (cp.q_1(2020), 18.66),
                    (cp.q_2(2020), 19.65),
                    (cp.jul(2020), 15.66)
                ],
                "knot_positions": KnotPositions.SPACING_CENTRE,
                "tension": 12.5,
                "discount_factor": discount_factor,
            }
        ]
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-10)

    def _interpolate_and_assert_average_back_to_inputs(self, test_case_data, tol):
        for test_data in test_case_data:
            interp_curve = hyperbolic_tension_spline(**test_data)
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

    def test_shaping_spreads_curve_has_expected_spreads(self):
        shaping_spreads = [
            (cp.jan(2024), cp.mar(2024), 2.45),
            (cp.jan(2024), cp.feb(2024), 1.05),
            (cp.mar(2024), cp.jul(2024), 1.68),
        ]
        contracts = [
            (cp.q_4(2023), 58.65),
            (cp.q_1(2024), 57.09),
            (cp.q_2(2024), 53.06),
            (cp.q_3(2024), 52.17),
        ]
        # TODO add weighting and adjustment functions into here
        daily_curve = hyperbolic_tension_spline(contracts, freq='D', shaping_spreads=shaping_spreads,
                                                   discount_factor=discount_factor, tension=0.9)
        for shaping_long_period, shaping_short_period, spread in shaping_spreads:
            long_period_interpolated_price = weighted_average_slice_curve(daily_curve, 'D', shaping_long_period, discount_factor)
            short_period_interpolated_price = weighted_average_slice_curve(daily_curve, 'D', shaping_short_period, discount_factor)
            interpolated_spread = long_period_interpolated_price - short_period_interpolated_price
            self.assertAlmostEqual(interpolated_spread, spread, delta=1E-12)

    def test_shaping_ratios_curve_has_expected_ratios(self):
        shaping_ratios = [
            (cp.jan(2024), cp.mar(2024), 1.11),
            (cp.jan(2024), cp.feb(2024), 1.08),
            (cp.mar(2024), cp.jul(2024), 1.05),
        ]
        contracts = [
            (cp.jan(2023), 35.65),
            (cp.q_2(2024), 30.36),
            (cp.q_3(2024), 29.24),
        ]
        # TODO add weighting and adjustment functions into here
        daily_curve = hyperbolic_tension_spline(contracts, freq='D', shaping_ratios=shaping_ratios,
                                                   discount_factor=discount_factor, tension=0.9)
        for shaping_num_period, shaping_denom_period, ratio in shaping_ratios:
            num_period_interpolated_price = weighted_average_slice_curve(daily_curve, 'D', shaping_num_period, discount_factor)
            denom_period_interpolated_price = weighted_average_slice_curve(daily_curve, 'D', shaping_denom_period, discount_factor)
            interpolated_ratio = num_period_interpolated_price/denom_period_interpolated_price
            self.assertAlmostEqual(interpolated_ratio, ratio, delta=1E-12)


    @unittest.skip('Failures need investigation.')
    def test_input_contracts_in_linear_trend_results_linear(self):
        decimals_tol = 4
        intercept = 45.7
        daily_slope = 0.8
        hourly_slope = daily_slope/24.0
        num_daily_curve_points = 5

        daily_index = pd.period_range(start='2023-03-19', periods=num_daily_curve_points, freq='D')
        daily_prices = [intercept + daily_slope * i for i in range(num_daily_curve_points)]
        daily_curve = pd.Series(data=daily_prices, index=daily_index)

        expected_hourly_diffs = np.repeat(hourly_slope,  num_daily_curve_points*24-1)
        tensions = [0.0001, 0.01, 0.1, 0.5, 1.0, 2.0, 10.0, 100.0]
        for tension in tensions:
            hourly_curve = hyperbolic_tension_spline(daily_curve, freq='H', tension=tension)
            hourly_diffs = np.diff(hourly_curve)
            np.testing.assert_array_almost_equal(expected_hourly_diffs, hourly_diffs, decimal=decimals_tol)

    flat_price = 32.87
    flat_price_test_case_data = [
        {
            "freq": 'D',
            "contracts": [
                (cp.q_1(2020), flat_price),
                (cp.jan(2020), flat_price),
                (cp.q_2(2020), flat_price),
            ],
            "discount_factor": discount_factor,
        },
        {
            "freq": 'D',
            "contracts": [
                (cp.cal_year(2020), flat_price),
                (cp.q_1(2020), flat_price),
                (cp.q_2(2020), flat_price),
                (cp.jul(2020), flat_price)
            ],
            "discount_factor": discount_factor,
        },
        {
            "freq": 'D',
            "contracts": [
                (cp.q_1(2020), flat_price),
                (cp.q_2(2020), flat_price),
            ],
            "knot_positions": KnotPositions.NONE,
            "knots": ['2020-02-15'],
            "discount_factor": discount_factor,
        },
        {
            "freq": 'D',
            "contracts": [
                (cp.cal_year(2020), flat_price),
                (cp.q_1(2020), flat_price),
                (cp.q_2(2020), flat_price),
                (cp.jul(2020), flat_price)
            ],
            "knot_positions": KnotPositions.NONE,
            "knots": ['2020-02-15', '2020-07-12', '2020-12-02'],
            "discount_factor": discount_factor,
        }
    ]

    def test_contracts_all_same_price_flat_curve(self):
        decimals_tol = 11
        flat_tensions = [0.0001, 0.01, 0.1, 0.5, 1.0, 2.0, 10.0, 100.0]
        tension_switch_period = pd.Period('2020-04-01', freq='D')
        time_varying_tensions = [
            lambda day: 0.75 if day < tension_switch_period else 30.5,
            lambda day: 5.6 if day < tension_switch_period else 1.1
        ]
        tensions = flat_tensions + time_varying_tensions
        for data in self.flat_price_test_case_data:
            new_data = dict(data)
            for tension in tensions:
                new_data['tension'] = tension
                interp_curve = hyperbolic_tension_spline(**new_data)
                expected_values = np.repeat(self.flat_price, len(interp_curve))
                np.testing.assert_array_almost_equal(expected_values, interp_curve.values, decimal=decimals_tol)

    def test_back_1st_deriv_as_specified(self):
        tol = 1E-8
        back_1st_deriv = 0.95
        _, spline_params = hyperbolic_tension_spline(freq='D', contracts=self.contracts_list, tension=self.flat_tension,
                                                     back_1st_deriv=back_1st_deriv, return_spline_coeff=True)
        calculated_back_1st_deriv = self._calc_back_1st_deriv(spline_params)
        self.assertAlmostEqual(back_1st_deriv, calculated_back_1st_deriv, delta=tol)

    @staticmethod
    def _calc_back_1st_deriv(spline_params):
        penultimate_params = spline_params.iloc[-2]
        tau = penultimate_params['tension']
        z_i_minus_1 = penultimate_params['z']
        y_i_minus_1 = penultimate_params['y']
        last_params = spline_params.iloc[-1]
        z_i = last_params['z']
        y_i = last_params['y']
        h_i = last_params['t'] - penultimate_params['t']
        tau_h = tau * h_i
        tau_sqrd_h = tau_h * tau
        tau_sinh_tau_h = tau * np.sinh(tau_h)
        return z_i * (np.cosh(tau_h)/tau_sinh_tau_h - 1.0/tau_sqrd_h) + z_i_minus_1 * (1.0/tau_sqrd_h - 1.0/tau_sinh_tau_h) \
                        + y_i/h_i - y_i_minus_1/h_i

    def test_front_1st_deriv_as_specified(self):
        tol = 1E-11
        front_1st_deriv = 0.95
        _, spline_params = hyperbolic_tension_spline(freq='D', contracts=self.contracts_list, tension=self.flat_tension,
                                                     front_1st_deriv=front_1st_deriv, return_spline_coeff=True)
        calculated_front_1st_deriv = self._calc_front_1st_deriv(spline_params)
        self.assertAlmostEqual(front_1st_deriv, calculated_front_1st_deriv, delta=tol)

    @staticmethod
    def _calc_front_1st_deriv(spline_params):
        t_0_params = spline_params.iloc[0]
        tau = t_0_params['tension']
        z_0 = t_0_params['z']
        y_0 = t_0_params['y']
        t_1_params = spline_params.iloc[1]
        z_1 = t_1_params['z']
        y_1 = t_1_params['y']
        h = t_1_params['t'] - t_0_params['t']
        tau_h = tau * h
        tau_sqrd_h = tau_h * tau
        tau_sinh_tau_h = tau * np.sinh(tau_h)
        cosh_tau_h = np.cosh(tau_h)
        return z_1 * (1.0/tau_sinh_tau_h - 1.0/tau_sqrd_h) + z_0 * (1.0/tau_sqrd_h - cosh_tau_h/tau_sinh_tau_h) \
                        + y_1 / h - y_0/h

    @unittest.skip('This test is currently just used for investigations.')
    def test_investigations(self):
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

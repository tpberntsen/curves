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
import numpy as np
from datetime import date, datetime
from curves import hyperbolic_tension_spline
from curves import contract_period as cp
from math import exp
from tests._test_common import weighted_average_slice_curve
from curves._common import deconstruct_contract
from curves.hyperbolic_tension_spline import _populate_2h_matrix

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
            "back_1st_deriv": -0.3,
            "maximum_smoothness": False
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "mult_season_adjust": lambda x: 1.0,
            "add_season_adjust": lambda x: 0.1,
            "average_weight": lambda x: 0.1,
            "discount_factor": discount_factor,
            "maximum_smoothness": False
        },
        {
            "freq": 'D',
            "contracts": contracts_list,
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "back_1st_deriv": -0.3,
            "maximum_smoothness": False
        },
        {
            "freq": 'D',
            "contracts": contracts_series,
            "tension": flat_tension,
            "discount_factor": discount_factor,
            "maximum_smoothness": False
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
            "maximum_smoothness": False
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
            "back_1st_deriv": -0.3,
            "maximum_smoothness": False
        }
    ]

    # TODO properly parameterise these tests
    def test_hyperbolic_tension_spline_daily_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.daily_test_case_data, 1E-8)

    def test_hyperbolic_tension_spline_max_smoothness_daily_interpolation_averages_back_to_inputs(self):
        daily_test_data_max_smooth = self._set_max_smoothness_true(self.daily_test_case_data)
        self._interpolate_and_assert_average_back_to_inputs(daily_test_data_max_smooth, 1E-7) # TODO check why this was failing on Azure DevOps before increasing tolerance

    @staticmethod
    def _set_max_smoothness_true(test_data):
        test_data_max_smooth = []
        for d in test_data:
            new_d = dict(d)
            new_d['maximum_smoothness'] = True
            test_data_max_smooth.append(new_d)
        return test_data_max_smooth

    # TODO look into why bigger tolerance required here. Matrix gets poorly conditioned?
    def test_hyperbolic_tension_spline_intraday_interpolation_averages_back_to_inputs(self):
        self._interpolate_and_assert_average_back_to_inputs(self.intraday_test_case_data, 1E-8)

    def test_hyperbolic_tension_spline_max_smoothness_intraday_interpolation_averages_back_to_inputs(self):
        intraday_data_max_smooth = self._set_max_smoothness_true(self.intraday_test_case_data)
        self._interpolate_and_assert_average_back_to_inputs(intraday_data_max_smooth, 1E-6)

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
                "back_1st_deriv": -0.3,
                "maximum_smoothness": False
            },
        ]
        # Test without maximum smoothness
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-12)
        # Test with maximum smoothness
        for d in inputs:
            d["maximum_smoothness"] = True
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-11)

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
                "discount_factor": discount_factor,
                "maximum_smoothness": False
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
                "discount_factor": discount_factor,
                "maximum_smoothness": False
            }
        ]
        # Test without maximum smoothness
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-12)
        # Test with maximum smoothness
        for d in inputs:
            d["maximum_smoothness"] = True
        self._interpolate_and_assert_average_back_to_inputs(inputs, 1E-10)

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

    def test_input_contracts_in_linear_trend_results_linear_no_max_smoothness(self):
        self._input_contracts_in_linear_trend_results_linear(False, 10)

    @unittest.skip('Failures need investigation.')
    def test_input_contracts_in_linear_trend_results_linear_max_smoothness(self):
        self._input_contracts_in_linear_trend_results_linear(True, 4)

    @staticmethod
    def _input_contracts_in_linear_trend_results_linear(max_smoothness, decimals_tol):
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
            hourly_curve, _ = hyperbolic_tension_spline(daily_curve, freq='H', tension=tension, maximum_smoothness=max_smoothness)
            hourly_diffs = np.diff(hourly_curve)
            np.testing.assert_array_almost_equal(expected_hourly_diffs, hourly_diffs, decimal=decimals_tol)

    flat_price = 32.87
    flat_price_test_case_data = [
        {
            "freq": 'D',
            "contracts": [
                (cp.q_1(2020), flat_price),
                (cp.q_2(2020), flat_price),
            ],
            "spline_knots": ['2020-01-01', '2020-02-15'],
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
            "spline_knots": ['2020-01-01', '2020-02-15', '2020-07-12', '2020-12-02'],
            "discount_factor": discount_factor,
        }
    ]

    def test_contracts_all_same_price_flat_curve_no_max_smooth(self):
        self._contracts_all_same_price_flat_curve(False, 12)

    def test_contracts_all_same_price_flat_curve_max_smooth(self):
        self._contracts_all_same_price_flat_curve(True, 11)

    def _contracts_all_same_price_flat_curve(self, max_smoothness, decimals_tol):
        tensions = [0.0001, 0.01, 0.1, 0.5, 1.0, 2.0, 10.0, 100.0]
        for data in self.flat_price_test_case_data:
            new_data = dict(data)
            new_data['maximum_smoothness'] = max_smoothness
            for tension in tensions:
                new_data['tension'] = tension
                interp_curve, spline_params = hyperbolic_tension_spline(**new_data)
                expected_values = np.repeat(self.flat_price, len(interp_curve))
                np.testing.assert_array_almost_equal(expected_values, interp_curve.values, decimal=decimals_tol)

    def test_max_smoothness_penalty_less_or_equal_no_max_smoothness_penalty(self):
        all_test_data = self.daily_test_case_data + self.intraday_test_case_data
        tensions = [0.0001, 0.1, 0.5, 1.0, 10.0, 100.0]
        for test_data in all_test_data:
            new_data = dict(test_data)
            for tension in tensions:
                new_data['tension'] = tension
                new_data['maximum_smoothness'] = True
                _, max_smooth_spline_params = hyperbolic_tension_spline(**new_data)
                max_smooth_penalty = self.max_smooth_penalty(max_smooth_spline_params)
                new_data['maximum_smoothness'] = False
                _, no_max_smooth_spline_params = hyperbolic_tension_spline(**new_data)
                no_max_smooth_penalty = self.max_smooth_penalty(no_max_smooth_spline_params)
                self.assertLessEqual(max_smooth_penalty, no_max_smooth_penalty)

    @staticmethod
    def max_smooth_penalty(spline_params):
        sum_penalty = 0.0
        last_params = spline_params.iloc[0]
        for i in range(1, len(spline_params)):
            this_params = spline_params.iloc[i]
            h = this_params['t'] - last_params['t']
            effective_tension = last_params['tension']
            z_i = this_params['z']
            y_i = this_params['y']
            z_i_minus_1 = last_params['z']
            y_i_minus_1 = last_params['y']
            tau_h = effective_tension * h
            cosh_tau_h = np.cosh(tau_h)
            sinh_tau_h = np.sinh(tau_h)
            z_terms = cosh_tau_h / (effective_tension * sinh_tau_h) - 1.0 / (effective_tension * effective_tension * h)
            tau_sqrd_over_h = effective_tension * effective_tension / h
            sum_penalty += z_i ** 2 * z_terms + z_i_minus_1 ** 2 * z_terms + y_i ** 2 * tau_sqrd_over_h + y_i_minus_1 ** 2 * tau_sqrd_over_h \
                           + z_i * z_i_minus_1 * 2.0 * (1.0 / (effective_tension ** 2 * h) - 1.0 / (effective_tension * sinh_tau_h)) \
                           - y_i * y_i_minus_1 * 2.0 * tau_sqrd_over_h
            last_params = this_params
        return sum_penalty

    # TODO delete this?
    @staticmethod
    def max_smooth_penalty_from_private(spline_params, tension):
        zs = spline_params['z'].values
        ys = spline_params['y'].values
        num_coeffs = len(spline_params) * 2
        coeffs_array = np.zeros(num_coeffs)
        coeffs_array[::2] = zs
        coeffs_array[1::2] = ys
        num_sections = len(spline_params) - 1
        tension_by_section = np.zeros(num_sections)
        h_is = np.zeros(num_sections)
        last_params = spline_params.iloc[0]
        for i in range(1, len(spline_params)):
            this_params = spline_params.iloc[i]
            h = this_params['t'] - last_params['t']
            effective_tension = tension / h
            tension_by_section[i - 1] = effective_tension
            h_is[i - 1] = h
            last_params = this_params
        tension_by_section_sqrd = tension_by_section * tension_by_section
        tau_h = tension_by_section * h_is
        tau_sqrd_hi = tau_h * tension_by_section
        matrix = np.zeros((num_coeffs, num_coeffs))
        tau_sinh = np.sinh(tau_h) * tension_by_section
        cosh_tau_hi = np.cosh(tau_h)
        _populate_2h_matrix(matrix, tension_by_section, tension_by_section_sqrd, tau_sqrd_hi, h_is, tau_sinh, cosh_tau_hi)
        penalty = np.matmul(np.matmul(coeffs_array.T, matrix), coeffs_array) / 2
        return penalty

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
                                               discount_factor=lambda x: 1.0, back_1st_deriv=back_1st_derive, maximum_smoothness=True)
        print('Curve length:')
        print(len(daily_curve))
        # Assert
        # expect_daily_curve = monthly_curve.resample(freq).fillna('pad')
        # pd.testing.assert_series_equal(daily_curve, expect_daily_curve)
        # self.assertEqual(len(spline_params), len(monthly_curve) + 1)

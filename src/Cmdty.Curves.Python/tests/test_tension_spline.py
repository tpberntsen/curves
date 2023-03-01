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
from curves import tension_spline


class TestTensionSpline(unittest.TestCase):

    def test_inputs_constant_outputs_constant(self):
        # Arrange
        freq = 'H'
        time_zone = 'Europe/London'
        flat_price = 0.0
        num_contracts = 3
        monthly_index = pd.period_range(start='2023-04-01', periods=num_contracts, freq='M')
        monthly_curve = pd.Series(data=[flat_price] * num_contracts, index=monthly_index)
        spline_boundaries = ['2023-04-01', date(2023, 5, 12), pd.Period(freq='D', year=2023, month=6, day=21)]
        def tension(p):
            return 0.5

        # Act
        daily_curve, spline_params = tension_spline(monthly_curve, freq=freq, tension=tension, time_zone=time_zone,
                                                    discount_factor=lambda x: 1.0, spline_boundaries=spline_boundaries)

        # Assert
        expect_daily_curve = monthly_curve.resample(freq).fillna('pad').to_timestamp()
        self.assertEqual(len(daily_curve), len(expect_daily_curve))
        self.assertEqual(len(spline_params), len(monthly_curve) + 1)

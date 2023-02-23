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
from curves import tension_spline


class TestTensionSpline(unittest.TestCase):

    def test_inputs_constant_outputs_constant(self):
        # Arrange
        flat_price = 25.65
        num_contracts = 3
        monthly_index = pd.period_range(start='2023-03-01', periods=num_contracts, freq='M')
        monthly_curve = pd.Series(data=[flat_price]*num_contracts, index=monthly_index)

        # Act
        daily_curve, spline_params = tension_spline(monthly_curve, freq='D', tension=0.5, discount_factor=lambda x: 1.0)

        # Assert
        expect_daily_curve = monthly_curve.resample('D').fillna('pad')
        self.assertEqual(len(daily_curve), len(expect_daily_curve))
        self.assertEqual(len(spline_params), len(monthly_curve)+1)

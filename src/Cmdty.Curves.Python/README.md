## Overview

The curves package contains a set of tools for building commodity forward, swaps, and futures curves.

More specifically, the problem being solved is to take a collection of traded forward prices, and transform these into a 
forward curve of homogenous granularity. Additionally the derived curve can constructed to be in a granularity higher 
than what is traded in the market.

Examples of types of curve which can be constructed using this package:
* Monthly granularity oil products swap curves from traded monthly, quarterly, and calendar yearly granularity
market swap rates.
* Daily granularity natural gas forward curves from traded daily, weekly, monthly, quarterly, seasonal, and
gas year granularity forward and futures prices.
* Half-hourly granularity power forward curves from traded daily, weekly, monthly, quarterly, and seasonal
granularity forward and futures prices.

The resulting curves should be consistent with inputs, in that they average back to the input forward contract prices.
This is a necessary to ensure that there are no arbitrage opportunities introduced between input contracts, and the derived forward curve.

## Usage
Two functions in the curves package are the core of the curve building calculations; bootstrap_contracts and max_smooth_interp.
Some basic examples of both of these function are given below. Both of these methods make extensive use of pandas, with
the pandas.Series type used to represent forward curves, and pandas.Period for the delivery period of an input forward contract
or derived forward curve.

For details of more advanced usage, view the docstrings for either of these functions and the Jupyter Notebook [curves_tutorial](https://github.com/cmdty/curves/blob/master/samples/python/curves_tutorial.ipynb).

### Bootstrapper
The basic functionality of the method bootstrap_contracts is to take a set of forward prices, for contracts with overlapping 
delivery/fixing periods, and return a curve with overlapping periods removed, but with prices consistent with the original inputs.
Below is a basic example showing prices for January and Q1 delivery period periods being bootstrapped into 
consistent January, February and March forward prices.

```python
from curves import bootstrap_contracts
from datetime import date

q1_price = 19.05
contracts = [
    (date(2019, 1, 1), 18.95), # Jan-19
    (date(2019, 1, 1), date(2019, 3, 1), 19.05) # Q1-19
]
piecewise_curve, bootstrapped_contracts = bootstrap_contracts(contracts, freq='M')
print(piecewise_curve)
print()
for bc in bootstrapped_contracts:
    print("{0}, {1}, {2:.3f}".format(repr(bc.start), repr(bc.end), bc.price))

```

The above code prints to the following:
```
2019-01    18.950000
2019-02    19.102542
2019-03    19.102542
Freq: M, dtype: float64

Period('2019-01', 'M'), Period('2019-01', 'M'), 18.950
Period('2019-02', 'M'), Period('2019-03', 'M'), 19.103
```

### Spline Interpolation
In order to facilitate creating a curve with higher granularity than the input contracts, the curves package includes the max_smooth_interp function. 
This uses a maximum smoothness algorithm to interpolate input contracts with a fourth-order spline, whilst maintaining the average price constraints 
inherent in the input contract prices.

The example below creates a daily granularity curve, from input contracts of various granularities. As would usually be the case in a practical scenario, 
the bootstrap_contracts method is first used to remove the overlaps from the contracts. The example below also shows how the input contracts can have gaps 
between them, which the spline will interpolate over, filling in the gaps in the final smooth curve. It also demonstrates the different ways of representing 
the contract delivery period in the contract tuples and use of the helper module contract_period.

```python
from curves import max_smooth_interp
from curves import contract_period as cp
import pandas as pd

contracts = [
    (date(2019, 5, 31), 34.875), 
    (date(2019, 6, 1), date(2019, 6, 2), 32.87),
    ((date(2019, 6, 3), date(2019, 6, 9)), 32.14),
    (pd.Period(year=2019, month=6, freq='M'), 31.08),
    (cp.month(2019, 7), 29.95),
    (cp.q_3(2019), 30.18),
    (cp.q_4(2019), 37.64),
    (cp.winter(2019), 38.05),
    (cp.summer(2020), 32.39),
    (cp.winter(2020), 37.84),
    (cp.gas_year(2020), 35.12)
]

pc_for_spline, bc_for_spline = bootstrap_contracts(contracts, freq='D')
smooth_curve = max_smooth_interp(bc_for_spline, freq='D')
smooth_curve.plot(title='Interpolated Daily Curve', legend=True, label='Daily Forward Price')

```

![Max Smooth Daily Curve](https://github.com/cmdty/curves/raw/master/assets/pypi_readme_max_smooth_daily_curve.png)

### Hyperbolic Tension Spline
The latest addition to the library is the hyperbolic tension spline. This model is intended it supersede
both the bootstrap_contracts and max_smooth_interp at a future date. Apart from the addition of a tension parameter, the 
implementation of the new tension spline differs from the maximum smoothness spline in the following ways:

* Functionality to interpolate overlapping contracts and apply shaping spreads and ratios. 
The bootstrap_contracts needs to be called prior to spline interpolation to remove overlaps and 
apply shaping. However, these aspects of the interpolation are incorporated directly into the linear 
system being solved for the tension spline, as should have been done with the maximum smoothness spline.
* Written purely in Python, rather than the core being implemented in C#. This has many benefits, including:
    * No restriction on the granularity of curves which can be produced, other than what can be represented by a Pandas frequency.
    * Easier to view and debug the core calculations.
* Ability to specify the time zone of the interpolated curve. This is important for sub-daily granularity
interpolation, typically seen for power curve construction.
* Arbitrary positioning of the spline knots, as determined by the caller.



See [tension_spline.pdf](https://github.com/cmdty/curves/blob/master/docs/tension_spline/tension_spline.pdf)
for technical documentation and [hyberbolic_tension_spline.ipynb](https://github.com/cmdty/curves/blob/master/samples/python/hyperbolic_tension_spline.ipynb)
for more details of usage. The docstring to the hyperbolic_tension_spline also contains
comprehensive information on all parameters.

### .NET Dependency For non-Windows OS
As Cmdty.Curves is mostly written in C# it requires the .NET runtime to be installed to execute.
The dlls are targeting [.NET Standard 2.0](https://learn.microsoft.com/en-us/dotnet/standard/net-standard?tabs=net-standard-2-0) which is compatible with .NET Framework versions 4.6.1
upwards. A version of .NET Framework meeting this restriction should be installed on most
Windows computers, so nothing extra is required.

If running on a non-Windows OS then the runtime of a cross-platform type of .NET will be 
required. .NET Standard is compatible with .NET and Mono, with the former being recommended.
For the Python package, by default it will try to use .NET, and if this isn't installed it will
try Mono. See the Microsoft documentation on installing the .NET runtime on [Linux](https://learn.microsoft.com/en-us/dotnet/core/install/linux)
and on [macOS](https://learn.microsoft.com/en-us/dotnet/core/install/macos).

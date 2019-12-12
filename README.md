Commodity Curves
================
[![Build Status](https://dev.azure.com/cmdty/github/_apis/build/status/cmdty.curves?branchName=master)](https://dev.azure.com/cmdty/github/_build/latest?definitionId=1&branchName=master)
![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/cmdty/github/1)
[![NuGet](https://img.shields.io/nuget/v/cmdty.curves.svg)](https://www.nuget.org/packages/Cmdty.Curves/)
[![PyPI](https://img.shields.io/pypi/v/curves.svg)](https://pypi.org/project/curves/)

Set of tools written in C# for constructing commodity forward/futures/swap curves with a fluent API. Python API also provided which integrates with the pandas library time series types.

### Table of Contents
* [Overview](#overview)
* [Getting Started](#getting-started)
    * [Installing](#installing)
        * [Installing For Python on Linux](#installing-for-python-on-linux)
    * [Using From C#](#using-from-c)
    * [Using From Python](#using-from-python)
* [Technical Documentation](#technical-documentation)
* [License](#license)

## Overview

The curves package contains a set of tools for building commodity forward, swaps, and futures curves.

More specifically, the problem being solved is to take a collection of traded forward prices, and tranform these into a 
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

## Getting Started

### Installing
For use from C# install the NuGet package Cmdty.Curves.
```
PM> Install-Package Cmdty.Curves -Version 0.1.0-beta1
```

For use from Python install the curves package from PyPI.
```
> pip install curves
```
### Installing For Python on Linux
Currently only a small amount of testing has been done for the Python package running on Linux (Ubuntu 18.04 LTS running in Windows 10 WSL) via the Mono runtime, using Python version 3.6.8. The following Linux dependencies have to be installed, as listed on [the pythonnet wiki](https://github.com/pythonnet/pythonnet/wiki/Troubleshooting-on-Windows,-Linux,-and-OSX):
* Mono-develop or Mono-complete. Curves was successfully run after installing version 5.20.1.34 of Mono-complete. Note that pythonnet does not work with Mono version 6.x. See [this page](https://www.mono-project.com/docs/getting-started/install/linux/#accessing-older-releases) for instructions on installing older versions of Mono on Linux.
* clang.
* libglib2.0-dev.
* python-dev. Specifically the package python3.6-dev was installed.

It was also found that the PyPI package pycparser had to be installed, in order for the pythonnet PyPI package to install correctly.


### Using From C#
For examples of usage see [samples/csharp/](https://github.com/cmdty/curves/tree/master/samples/csharp).

### Using From Python
A Python API has been created using [pythonnet](https://github.com/pythonnet/pythonnet). See the Jupyter Notebook [curves_quick_start_tutorial](samples/python/curves_quick_start_tutorial.ipynb) for an introduction on how to use this.

## Technical Documentation
The PDF file [max_smoothness_spline.pdf](docs/max_smoothness/max_smoothness_spline.pdf) contains details of the mathematics behind the maximum smoothness algorithm.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

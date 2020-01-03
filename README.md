Commodity Curves
================
[![Build Status](https://dev.azure.com/cmdty/github/_apis/build/status/cmdty.curves?branchName=master)](https://dev.azure.com/cmdty/github/_build/latest?definitionId=1&branchName=master)
![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/cmdty/github/1)
[![NuGet](https://img.shields.io/nuget/v/cmdty.curves.svg)](https://www.nuget.org/packages/Cmdty.Curves/)
[![PyPI](https://img.shields.io/pypi/v/curves.svg)](https://pypi.org/project/curves/)

Set of tools written in C# for constructing commodity forward/futures/swap curves with a fluent API. Python API also provided which integrates with the pandas library time series types.

### Table of Contents
* [Overview](#overview)
* [Installing](#installing)
    * [Installing For Python on Linux](#installing-for-python-on-linux)
    * [Using From C#](#using-from-c)
    * [Using From Python](#using-from-python)
* [Technical Documentation](#technical-documentation)
* [Building](#building)
    * [Build Prerequisites](#build-prerequisites)
    * [Running the Build](#running-the-build)
    * [Build Artifacts](#build-artifacts)
    * [Building from Linux and macOS](#building-from-linux-and-macos)
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

The core of the curves package essentially consists of two models; the bootstrapper and the spline.

* The **bootstrapper** model takes a set of forward prices, for contracts with overlapping delivery/fixing periods, and returns a curve with overlapping periods removed, but with prices consistent with the original inputs. In addition the bootstrapper can be used to apply shaping to the forward prices by applying a predefined spread or ratios between two contract prices.
* The **spline** model allows the creation of a smooth curve with higher granularity than the input contracts. This uses a maximum smoothness algorithm to interpolate input contracts with a fourth-order spline, whilst maintaining the average price constraints inherent in the input contract prices.

See [Getting Started](#getting-started) below for more details on how to use these two model from both C# and Python.

## Installing
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

## Getting Started

### Using From C#
#### Bootstrapper
The C# code below gives an example of user the bootstrapper on overlapping Q1-20 and Jan-20 forward prices.
```c#
(DoubleCurve<Month> pieceWiseCurve, IReadOnlyList<Contract<Month>> bootstrappedContracts) = new Bootstrapper<Month>()
                    .AddContract(Month.CreateJanuary(2020), 19.05)
                    .AddContract(Quarter.CreateQuarter1(2020), 17.22)
                    .Bootstrap();

Console.WriteLine("Derived piecewise flat curve:");
Console.WriteLine(pieceWiseCurve.FormatData("F5"));

Console.WriteLine();

Console.WriteLine("Equivalent bootstrapped contracts:");
PrintBootstrapContracts(bootstrappedContracts);
```

For more sophisticated examples of usage see [samples/csharp/](https://github.com/cmdty/curves/tree/master/samples/csharp).

### Using From Python
A Python API has been created using [pythonnet](https://github.com/pythonnet/pythonnet). See the Jupyter Notebook [curves_quick_start_tutorial](samples/python/curves_quick_start_tutorial.ipynb) for an introduction on how to use this.

## Technical Documentation
The PDF file [max_smoothness_spline.pdf](docs/max_smoothness/max_smoothness_spline.pdf) contains details of the mathematics behind the maximum smoothness algorithm.

## Building
This section describes how to run a scripted build on a cloned repo. Visual Studio 2019 is used for development, and can also be used to build the C# and run unit tests on the C# and Python APIs. However, the scripted build process also creates packages (NuGet and Python), builds the C# samples, and verifies the C# interactive documentation. [Cake](https://github.com/cake-build/cake) is used for running scripted builds. This is relevant for running the scripted build on Windows. For running on a non-Windows OS see [Building from Linux and macOS](#building-from-linux-and-macos).

#### Build Prerequisites
The following are required on the host machine in order for the build to run.
* The .NET Core SDK. Check [global.json file](global.json) for the version necessary, taking into account [the matching rules used](https://docs.microsoft.com/en-us/dotnet/core/tools/global-json#matching-rules).
* The Python interpretter, accessible by being in a file location in the PATH environment variable. Version 3.6 is used, although other 3.x versions might work.
* The following Python packages installed:
    * virtualenv.
    * setuptools.
    * wheel.
* The [Try .NET](https://dotnet.microsoft.com/platform/try-dotnet) global tool. This can be installed by running the following command.
```
> dotnet tool install -g dotnet-try
```

#### Running the Build
The build is started by running the PowerShell script build.ps1 from a PowerShell console, ISE, or the Visual Studio Package Manager Console.

```
PM> .\build.ps1
```

#### Build Artifacts
The following results of the build will be saved into the artifacts directory.
* The NuGet package: Cmdty.Curve.[version].nupkg
* The Python package files:
    * curves-[version]-py3-none-any.whl
    * curves-[version].tar.gz

### Building from Linux and macOS
Running the full build on non-Windows plaforms is still work in progress- the aim to to make it completely plaform agnostic. However, at the moment only the C# parts of the build are functioning cross-plaform. Using the .NET Core SDK the C# code can be built and unit tested by running the following commands in the clone repo.
```
> dotnet build
> dotnet test
```

The Cake build can be invoked using the bootstrapper Bash script build.sh. This requires the .NET SDK and mono to be installed. After first granting it execute permissions as below, the "Pack-NuGet" target results in the building and unit testing of the C#, before the creation of the Cmdty.Curves NuGet package.
```
> chmod +x build.sh
> ./build.sh --target=Pack-NuGet.
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

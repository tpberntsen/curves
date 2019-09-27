# Time Series
This markdown file provides interactive documentation using [Try .NET](https://dotnet.microsoft.com/platform/try-dotnet). If you haven't already, follow the instructions on [README](README.md) to set up and run.

The namespace Cmdty.TimeSeries contains a set of types used to represent an associated map, where the index is always a (Time Period Value Type)(TimePeriodValueTypes.md) from the Cmdty.TimePeriodValueTypes namespace. Time series types objects are immutable, are implicitly ordered by the index time period.

These types are used extensively within the Cmdty library to represent collection of prices for traded commodities, including forward curves. However, there is nothing commodity-specific within the Time Series API, and hence these types could be used in many other non-commodity business contexts.

### Creating Instances
```cs --region creating --source-file ./Cmdty.Curves.Samples.TimeSeries/Program.cs --project ./Cmdty.Curves.Samples.TimeSeries/Cmdty.Curves.Samples.TimeSeries.csproj
```

### Properties
```cs --region properties --source-file ./Cmdty.Curves.Samples.TimeSeries/Program.cs --project ./Cmdty.Curves.Samples.TimeSeries/Cmdty.Curves.Samples.TimeSeries.csproj
```

### Accessing Data
```cs --region accessing_data --source-file ./Cmdty.Curves.Samples.TimeSeries/Program.cs --project ./Cmdty.Curves.Samples.TimeSeries/Cmdty.Curves.Samples.TimeSeries.csproj
```

## Formating
```cs --region formatting --source-file ./Cmdty.Curves.Samples.TimeSeries/Program.cs --project ./Cmdty.Curves.Samples.TimeSeries/Cmdty.Curves.Samples.TimeSeries.csproj
```

## DoubleTimeSeries Type
```cs --region doubletimeseries --source-file ./Cmdty.Curves.Samples.TimeSeries/Program.cs --project ./Cmdty.Curves.Samples.TimeSeries/Cmdty.Curves.Samples.TimeSeries.csproj
```

# Time Period Value Types
The namespace Cmdty.TimePeriodValueTypes contains a set of types used to represent a time period for specific granularity. Examples of such types include Month, Quarter, HalfHour and Hour, but many others are also present.

These types are used extensively within the Cmdty library to represent the delivery periods for traded commodities. However, there is nothing commodity-specific within the Time Period Value Types API, and hence these types could be used in many other non-commodity business contexts.


### Creating Instances
As well as being able to create instances using constructors, many types have helper static factory methods as shown for the Month and Quarter types below.
All Time Period types also have a FromDateTime static methods for
converting instances of .NET System.DateTime to time period types.
```cs --region creating --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Parsing and Formatting
The ToString method is overridden on all types to provide a human readable text representation.
All types also have a static Parse method which can create an intance 
from this text representation. The ToString and Parse methods can be used in a round-trip fashion.

Some of the types also implement IFormattable which means an additional override of the ToString method is provided which includes parameters for a format string and format provider. This is demonstrated below for the Hour type.
```cs --region parsing_formatting --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Comparing Instances
```cs --region comparing --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Offsetting Instances
```cs --region offsetting --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Converting Between Granularities
```cs --region converting_granularity --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Expanding
```cs --region expanding --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Range of Valid Values
```cs --region time_period_ranges --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

### Extension Methods
```cs --region extension_methods --source-file ./Cmdty.Curves.Samples.TimePeriodValueTypes/Program.cs --project ./Cmdty.Curves.Samples.TimePeriodValueTypes/Cmdty.Curves.Samples.TimePeriodValueTypes.csproj
```

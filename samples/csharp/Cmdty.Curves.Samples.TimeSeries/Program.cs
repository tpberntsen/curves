#region License
// Copyright (c) 2019 Jake Fowler
//
// Permission is hereby granted, free of charge, to any person 
// obtaining a copy of this software and associated documentation 
// files (the "Software"), to deal in the Software without 
// restriction, including without limitation the rights to use, 
// copy, modify, merge, publish, distribute, sublicense, and/or sell 
// copies of the Software, and to permit persons to whom the 
// Software is furnished to do so, subject to the following 
// conditions:
//
// The above copyright notice and this permission notice shall be 
// included in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
// OTHER DEALINGS IN THE SOFTWARE.
#endregion

using System;
using System.Collections.Generic;
using System.Globalization;
using Cmdty.TimePeriodValueTypes;
using Cmdty.TimeSeries;

namespace Cmdty.Curves.Samples.TimeSeries
{
    class Program
    {
        static void Main(string region = null)
        {
            if (region == null)
            {
                Creating();
                Console.WriteLine();
                Properties();
                Console.WriteLine();
                AccessingData();
                Console.WriteLine();
                Formatting();
                Console.WriteLine();
                DoubleTimeSeries();
                Console.ReadKey();
            }
            else
            {
                switch (region)
                {
                    case "creating":
                        Creating();
                        break;
                    case "properties":
                        Properties();
                        break;
                    case "accessing_data":
                        AccessingData();
                        break;
                    case "formatting":
                        Formatting();
                        break;
                    case "doubletimeseries":
                        DoubleTimeSeries();
                        break;
                }
            }

        }

        private static void Creating()
        {
            #region creating
            TimeSeries<Quarter, decimal> timeSeriesFromConstructor1 = new TimeSeries<Quarter,decimal>(
                                                        Quarter.CreateQuarter1(2020), 
                                                        new decimal[]{21.3M, 42.4M, 42.5M});
            Console.WriteLine(timeSeriesFromConstructor1);
            Console.WriteLine();

            var timeSeriesFromConstructor2 = new TimeSeries<Day, double>(
                    new []{new Day(2019, 9, 17), new Day(2019, 9, 18), new Day(2019, 9, 19)},
                    new []{242.4, 224.42, 262.04});
            Console.WriteLine(timeSeriesFromConstructor2);
            Console.WriteLine();

            TimeSeries<Month, int> timeSeriesFromBuilder = new TimeSeries<Month, int>.Builder
            {
                {Month.CreateJanuary(2019), 1},
                {Month.CreateFebruary(2019), 2},
                {Month.CreateMarch(2019), 3}
            }.Build();
            Console.WriteLine(timeSeriesFromBuilder);
            Console.WriteLine();

            TimeSeries<Day, string> emptyTimeSeries = TimeSeries<Day, String>.Empty;
            Console.WriteLine(emptyTimeSeries);

            #endregion
        }

        private static void Properties()
        {
            #region properties
            TimeSeries<Month, int> timeSeries = new TimeSeries<Month, int>.Builder
            {
                {Month.CreateJanuary(2019), 45},
                {Month.CreateFebruary(2019), 336},
                {Month.CreateMarch(2019), 846}
            }.Build();

            Console.WriteLine("TimeSeries Scalar Properties");
            Console.WriteLine("Count: " + timeSeries.Count);
            Console.WriteLine("Start: " + timeSeries.Start);
            Console.WriteLine("End: " + timeSeries.End);
            Console.WriteLine("IsEmpty: " + timeSeries.IsEmpty);
            Console.WriteLine();

            Console.WriteLine("TimeSeries Collection Properties");
            IReadOnlyList<Month> timeSeriesIndices = timeSeries.Indices;
            Console.WriteLine("Contents of timeSeries.Indices:");
            foreach (Month month in timeSeriesIndices)
            {
                Console.WriteLine(month);
            }
            Console.WriteLine();

            IReadOnlyList<int> timeSeriesData = timeSeries.Data;
            Console.WriteLine("Contents of timeSeries.Data:");
            foreach (int dataItem in timeSeriesData)
            {
                Console.WriteLine(dataItem);
            }
            
            #endregion
        }

        private static void AccessingData()
        {
            #region accessing_data
            TimeSeries<Month, decimal> timeSeries = new TimeSeries<Month, decimal>.Builder
                        {
                            {Month.CreateJanuary(2019), 22.53M},
                            {Month.CreateFebruary(2019), 19.42M},
                            {Month.CreateMarch(2019), 18.25M}
                        }.Build();

            decimal itemFromTimePeriodIndexer = timeSeries[Month.CreateFebruary(2019)];
            Console.WriteLine("Item from Time Period indexer: " + itemFromTimePeriodIndexer);

            decimal itemFromIntegerIndexer = timeSeries[0];
            Console.WriteLine("Item from int indexer: " + itemFromIntegerIndexer);

            Console.WriteLine();

            Console.WriteLine("Enumerating Over a TimeSeries");
            foreach (TimeSeriesPoint<Month, decimal> timeSeriesPoint in timeSeries)
            {
                Console.WriteLine(timeSeriesPoint);
            }

            #endregion
        }

        private static void Formatting()
        {
            #region formatting
            TimeSeries<Month, decimal> monthlyTimeSeries = new TimeSeries<Month, decimal>.Builder
            {
                {Month.CreateJanuary(2019), 22.53M},
                {Month.CreateFebruary(2019), 19.42M},
                {Month.CreateMarch(2019), 18.25M}
            }.Build();

            string timeSeriesDefaultFormatting = monthlyTimeSeries.ToString();
            Console.WriteLine("Default formatting");
            Console.WriteLine(timeSeriesDefaultFormatting);
            Console.WriteLine();

            string timeSeriesFormattedWithFormatString = monthlyTimeSeries.FormatData("F5");
            Console.WriteLine("Formatted with format string and current thread culture");
            Console.WriteLine(timeSeriesFormattedWithFormatString);
            Console.WriteLine();

            string timeSeriesFormattedWithFormatStringAndCulture =
                monthlyTimeSeries.FormatData("F5", new CultureInfo("fr"));
            Console.WriteLine("Formatted with format string and specified culture");
            Console.WriteLine(timeSeriesFormattedWithFormatStringAndCulture);
            Console.WriteLine();

            // TODO specify max printed rows
            // TODO formatting index
            // TODO formatting index and data


            #endregion
        }

        private static void DoubleTimeSeries()
        {
            #region doubletimeseries

            

            #endregion
        }
        
    }
}

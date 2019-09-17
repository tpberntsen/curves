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

            

            #endregion
        }

        private static void AccessingData()
        {
            #region accessing_data

            

            #endregion
        }

        private static void Formatting()
        {
            #region formatting

            

            #endregion
        }
        
        private static void DoubleTimeSeries()
        {
            #region doubletimeseries

            

            #endregion
        }
        
    }
}

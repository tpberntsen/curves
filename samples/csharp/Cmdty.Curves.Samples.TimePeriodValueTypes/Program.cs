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
using Cmdty.TimePeriodValueTypes;

namespace Cmdty.Curves.Samples.TimePeriodValueTypes
{
    class Program
    {
        static void Main(string[] args)
        {

            // Creating Time Periods

            var mar19 = new Month(2019, 3);
            Console.WriteLine(mar19.ToString());

            // Some types have convenience static methods for creating instances, e.g. for the Month type
            var aug19 = Month.CreateAugust(2019);
            Console.WriteLine(aug19);

            // Instances can be creating by parsing strings
            Month dec19 = Month.Parse("2019-12");
            Console.WriteLine(dec19);
            Console.WriteLine();

            // Or created from DateTimes instances using the FromDateTime
            Day christmas2020 = Day.FromDateTime(new DateTime(2020, 12, 25));
            Console.WriteLine(christmas2020);

            // Comparing
            // All time periods implement IComparable<T>
            var qu119 = new Quarter(2019, 1);
            var qu219 = Quarter.CreateQuarter2(2019);

            Console.WriteLine(qu119.CompareTo(qu219));

            // Comparison operators are also overloaded
            Console.WriteLine(qu119 < qu219);
            Console.WriteLine(qu119 <= qu219);
            Console.WriteLine(qu119 == qu219);
            Console.WriteLine(qu119 != qu219);
            Console.WriteLine(qu119 > qu219);
            Console.WriteLine(qu119 >= qu219);

            // Methods Offset and OffsetFrom from are used to create relative time periods, and calculate the difference
            // between time periods
            var tenAm = new Hour(2019, 8, 30, 10);
            Hour midday = tenAm.Offset(2);
            Console.WriteLine(midday);

            int numHours = midday.OffsetFrom(tenAm);
            Console.WriteLine(numHours);

            // The same logic as Offset and Offset from can be called using the + and - operators respectively
            var calYear19 = new CalendarYear(2019);

            CalendarYear calYear22 = calYear19 + 3;
            Console.WriteLine(calYear22);

            int yearsDifference = calYear22 - calYear19;
            Console.WriteLine(yearsDifference);

            // The increment ++, and decrement --, operators can also be used
            var halfHour = new HalfHour(2019, 8, 30, 22, 0);

            Console.WriteLine();
            Console.WriteLine("Incrementing Half Hour");
            Console.WriteLine(halfHour);
            halfHour++;
            Console.WriteLine(halfHour);
            halfHour++;
            Console.WriteLine(halfHour);
            
            Console.WriteLine();
            Console.WriteLine("Decrementing Half Hour");
            halfHour--;
            Console.WriteLine(halfHour);
            halfHour--;
            Console.WriteLine(halfHour);
            halfHour--;
            Console.WriteLine(halfHour);

            // Can also convert between different granularity time periods using the methods First, Last and Expand
            Console.WriteLine();
            Console.WriteLine("The first month in Q1-19 is " + qu119.First<Month>());
            Console.WriteLine("The last month in Q1-19 is " + qu119.Last<Month>());
            Console.WriteLine();

            IEnumerable<Month> allMonthsInQ119 = qu119.Expand<Month>();
            Console.WriteLine("All the months in Q1-19:");
            foreach (Month month in allMonthsInQ119)
            {
                Console.WriteLine(month);
            }

            // Static properties give information on the valid range for each time period type
            Console.WriteLine();
            Console.WriteLine("Minimum Day: " + Day.MinDay);
            Console.WriteLine("Maximum Day: " + Day.MaxDay);

            // Extension method provide extra useful functionality
            // E.g. the EnumerateTo extension method
            Console.WriteLine();
            var quarterStart = Quarter.CreateQuarter3(2020);
            var quarterEnd = Quarter.CreateQuarter2(2021);
            Console.WriteLine($"All the quarters from {quarterStart} to {quarterEnd}");
            foreach (Quarter quarter in quarterStart.EnumerateTo(quarterEnd))
            {
                Console.WriteLine(quarter);
            }

            // E.g. EnumerateWeekdaysDays extension method
            Console.WriteLine();
            var dayStart = new Day(2019, 8, 30);
            var dayEnd = new Day(2019, 9, 4);
            Console.WriteLine($"All week days from {dayStart} to {dayEnd}");
            foreach (Day weekday in dayStart.EnumerateWeekdays(dayEnd))
            {
                Console.WriteLine(weekday);
            }

            Console.ReadKey();
        }
    }
}

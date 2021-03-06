import operator
import datetime as dt
import pandas as pd
import numpy as np

class Explorer():
    def __init__(self, df, lo=70, up=180, 
            begin_date=dt.datetime(1700, 1, 1, 0, 0), 
            end_date=dt.datetime(2200, 1, 1, 0, 0)):
        """ df: dataframe with all the data this explorer needs
            lo: lower bound for bg care analysis
            up: upper bound for bg care analysis
            begin_date: begin date for studied interval
            end_date: end date for studied interval
        """
        self.df = df
        self.lo = lo
        self.up = up
        self.begin_date = begin_date
        self.end_date = end_date

    def update(self, df=None, lo=None, up=None, begin_date=None, end_date=None):
        """Update attributes in our explorer object"""
        if df:
            self.df = df
        if lo:
            self.lo = lo
        if up:
            self.up = up
        if begin_date:
            self.begin_date = dt.datetime(begin_date.year, begin_date.month,
                begin_date.day) - pd.DateOffset(days=0)
        if end_date:
            self.end_date = dt.datetime(end_date.year, end_date.month,
                end_date.day, 23, 59, 59) - pd.DateOffset(days=0)

    def bg_count(self):
        """Number of non-null blood glucose registries"""
        return self.df.bg.count()

    def interval_filter(self):
        """Returns dataframe of registries inside self.interval"""
        return ((self.df.date >= self.begin_date) &
            (self.df.date <= self.end_date))

    def meal_filter(self, meal='all', moment='before'):
        """Returns boolean dataframe of registries of
        meals based on filters given as parameters.

        moments: before, after, all

        meals: snack, breakfast, lunch, dinner, all, no_meal

        if filtering for meals='no_meal', this algorithm works the same way as if
        meals='all', except it returns the opposite boolean value for each cell
        """
        meals = (['snack', 'dinner', 'lunch', 'breakfast']
                if meal in 'all no_meal'
                else [meal])

        if moment == 'after':
            meals = ['after_'+meal for meal in meals]
        elif moment == 'all' or meal == 'no_meal':
            meals += ['after_'+meal for meal in meals] 

        # test for intersection with meals
        sel = operator.eq if meal == 'no_meal' else operator.gt
        return self.df.tags.apply(lambda tag :
            sel(len([m for m in meals if m in tag]), 0)
            if isinstance(tag, str)
            else sel == operator.eq)

    def basic_stats(self, column, op, meal=None, moment=None,
            operate_on_cumsum=None):
        """Basic stats should handle any operation that depends only
        on a row's value (not on next row, or on a group of rows) and
        uses this class' standard interval and meal filters.
        """
        if not meal:
            filtered_df = self.df
        else:
            filtered_df = self.df[self.meal_filter(meal, moment)]

        # todo: function to group by anything
        if operate_on_cumsum == 'per_day':
            # group by day
            filtered_df = filtered_df.groupby(filtered_df.date.dt.normalize()).sum()
        elif operate_on_cumsum == 'per_week':
            return 1
            # group by week
            pass
        elif operate_on_cumsum == 'per_month':
            return 2
            # group by month
            pass

        filtered_df = filtered_df[column]
        if op == 'cumsum': #cumulative sum
            return filtered_df.sum()
        elif op == 'avg':
            return filtered_df.mean()
        elif op == 'std': #std deviation
            return filtered_df.std()

    def range_time(self, region='in', count=False):
        """Percentage (our count) of registries with bg in, above or below
        range.

        region: below, above, in
        """
        if region == 'below':
            region_df = self.df.bg[self.df.bg < self.lo]
        elif region == 'above':
            region_df = self.df.bg[self.df.bg > self.up]
        else:
            region_df = (self.df.bg[(self.df.bg >= self.lo)
                & (self.df.bg <= self.up)])

        region_df = region_df[self.interval_filter()]

        if count:
            return region_df.count()
        else:
            return region_df.count()*100/self.df.bg.count()

    def HbA1c(self, up_until=None, use_interval=None):
        """Glycated hemoglobin starting 3 months before up_until and ending at
        up_until.

        If up_until == None, calculates HbA1c starting 3 months from today.
        If use_interval, uses explorer's interval.
        """
        if up_until:
            start_date = up_until
        else:
            start_date = dt.datetime.now()

        if use_interval:
            start_date = self.begin_date
        else:
            start_date -= pd.DateOffset(months=3)

        avg_bg = self.df.bg[self.df.date >= start_date].mean()
        return (avg_bg+46.7)/28.7

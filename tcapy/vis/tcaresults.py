from __future__ import print_function

__author__ = 'saeedamen'  # Saeed Amen / saeed@cuemacro.com

#
# Copyright 2019 Cuemacro Ltd. - http//www.cuemacro.com / @cuemacro
#
# See the License for the specific language governing permissions and limitations under the License.
#

from tcapy.conf.constants import Constants

from tcapy.vis.computationresults import ComputationResults

constants = Constants()

class TCAResults(ComputationResults):
    """Holds the results of a TCA computation in a friendly format, splitting out the various dataset which can be used
    for charts. Also converts these datasets to Plotly Figure objects, ready to be plotted in HTML documents by a TCAReport
    object

    """

    def __init__(self, dict_of_df, computation_request, text_preamble='See the below charts for results',
                 chart_width=constants.chart_width, chart_height=constants.chart_height):
        super(TCAResults, self).__init__(dict_of_df, computation_request, text_preamble=text_preamble)

        ticker = computation_request.ticker

        if not(isinstance(ticker, list)):
            ticker = [ticker]

        self.ticker = ticker
        self.trade_order_list = self._util_func.dict_key_list(computation_request.trade_order_mapping.keys())
        
        self.dict_of_df = dict_of_df

        self._chart_width = chart_width
        self._chart_height = chart_height

    def render_computation_charts(self, force_re_render=False):

        if force_re_render or not(self._rendered):
            timeline_charts = {}
            sparse_market_charts = {}
            bar_charts = {}
            dist_charts = {}
            styled_tables = {}

            # timeline charts
            for t in self._util_func.dict_key_list(self.timeline.keys()):
                timeline_charts[t] = self._plot_render.plot_timeline(self.timeline[t], t,
                                                                     width=self._chart_width, height=self._chart_height)

            lines_to_plot = self._util_func.dict_key_list(constants.detailed_timeline_plot_lines.keys())
            lines_to_plot.append('candlestick')

            # sparse market charts
            for s in self._util_func.dict_key_list(self.sparse_market.keys()):
                sparse_ticker = s.split('_')[0]
                sparse_market_charts[s] = self._plot_render.plot_market_trade_timeline(
                    s, self.sparse_market[s], candlestick_fig=self.candlestick_charts[sparse_ticker],
                    lines_to_plot=lines_to_plot, width=self._chart_width, height=self._chart_height)

            # bar charts
            for b in self._util_func.dict_key_list(self.bar.keys()):
                bar_charts[b] = self._plot_render.plot_bar(self.bar[b], b,
                                                                     width=self._chart_width, height=self._chart_height)

            # dist charts
            for d in self._util_func.dict_key_list(self.dist.keys()):
                tag_dict = self._split_df_tag(d)

                dist_charts[d] = self._plot_render.plot_dist(
                    dist_df=self.dist[d], metric=tag_dict['metric'], title=None, split_by=tag_dict['split_by'],
                                                                     width=self._chart_width, height=self._chart_height)

            # styled tables
            for t in self._util_func.dict_key_list(self.table.keys()):
                styled_tables[t] = self._plot_render.generate_table(self.table[t])

            self.timeline_charts = timeline_charts
            self.sparse_market_charts = sparse_market_charts
            self.bar_charts = bar_charts
            self.dist_charts = dist_charts
            self.styled_tables = styled_tables

            self._rendered = True

    def _split_df_tag(self, tag):
        tag_dict = {'split_by' : '', 'trade_order' : '', 'metric' : ''}

        tag_middle = tag

        if '_by_' in tag:
            tag_by_split = tag_middle.split('_by_')
            tag_middle = tag_by_split[0]
            tag_dict['split_by'] = tag_by_split[1]

        if '_df_' in tag:
            tag_df_split = tag_middle.split('_df_')

            tag_dict['trade_order'] = tag_df_split[0]
            tag_dict['metric'] = tag_df_split[1]

        return tag_dict

    @property
    def dict_of_df(self):
        return self.__dict_of_df

    @dict_of_df.setter
    def dict_of_df(self, dict_of_df):
        """Takes the results of a TCARequest given to TCAEngine, which are in the form of a dictionary of DataFrames. The keys
        are in a format which can be parsed easily. Normalizes all the tags, to include ticker name where applicable and
        stores them in variable internal variables, splitting them by several different categories

        trade_order = DataFrames of trades/orders
        timeline = DataFrames of timelines
        sparse_market = DataFrames with a mixture of market data/trade/order data
        bar = DataFrames with bar chart style data
        dist = DataFrames with distribution style data
        table = DataFrames intended to be displayed as tables
        market = DataFrames with high frequency tick market data

        Here are some examples:
            'candlestick_fig' - Plotly Figure of market data in candlestick format
            'trade_df' - trade_df execution data
            'sparse_market_trade_df' - sparse market data alongside trade data
            'timeline_trade_df_slippage_by_all' - a timeline of the slippage from trade data
            'timeline_trade_df_executed_notional_in_reporting_currency_by_all - a timeline of the executed notional
            'bar_trade_df_slippage_by_venue' - bar chart of slippage split by venue
            'dist_trade_df_slippage_by_side' - distribution chart of slippage split by side
            'market_df' - market data for a single ticker
            'EURUSD_df' - market data for EURUSD (when we are doing aggregated TCA analysis)

        Parameters
        ----------
        dict_of_df : DataFrame (dict)
            Output of a large scale computation

        """
        self.__dict_of_df = dict_of_df
        
        trade_order = {}
        timeline = {}
        sparse_market = {}
        bar = {}
        dist = {}
        table = {}
        market = {}

        candlestick_chart = {}
        
        keys = self._util_func.dict_key_list(dict_of_df.keys())
        
        for t in self.trade_order_list:
            if t in keys:
                trade_order[t] = dict_of_df[t]

        for d in keys:

            ## for single/multiple tickers
            # timeline
            if d.find('timeline_') == 0:
                simpler_d = d.replace('timeline_', '')

                timeline[simpler_d] = dict_of_df[d]

            elif d.find('bar_') == 0:

                simpler_d = d.replace('bar_', '')
                bar[simpler_d] = dict_of_df[d]
                
            elif d.find('dist_') == 0:

                simpler_d = d.replace('dist_', '')
                dist[simpler_d] = dict_of_df[d]
                
            elif d.find('table_') == 0:

                simpler_d = d.replace('table_', '')
                table[simpler_d] = dict_of_df[d]

            ## single tickers
            elif d.find('market_df') == 0:

                simpler_d = d.replace('market_df', self.ticker[0])
                market[simpler_d] = dict_of_df[d]

            # sparse charts (candlesticks)
            elif d.find('sparse_market_') == 0:
                simpler_d = d.replace('sparse_market', self.ticker[0])

                sparse_market[simpler_d] = dict_of_df[d]
                
            elif d.find('candlestick_fig') == 0:
                simpler_d = d.replace('candlestick_fig', self.ticker [0])
                candlestick_chart[simpler_d] = dict_of_df[d]

        #### for situations when we have multiple tickers

        # market, candlesticks
        for t in self._computation_request.ticker:
            if t + '_df' in keys:
                market[t] = dict_of_df[t + '_df']
            elif t + '_candlestick_fig' in keys:
                candlestick_chart[t] = dict_of_df[d + '_candlestick_fig']

        # sparse market
        for k in keys:
            for t in self._computation_request.ticker:
                if k.find(t + '_sparse_market_') == 0:
                    sparse_market[k.replace('_sparse_market_', '')] = dict_of_df[k]
        
        self.trade_order = trade_order
        self.timeline = timeline
        self.sparse_market = sparse_market
        self.bar = bar
        self.dist = dist
        self.table = table
        self.market = market

        self.candlestick_charts = candlestick_chart
        
    ##### basic properties (strings) of a TCA request

    @property
    def ticker(self):
        return self.__ticker

    @ticker.setter
    def ticker(self, ticker):
        self.__ticker = ticker

    @property
    def trade_order_list(self):
        return self.__trade_order_list

    @trade_order_list.setter
    def trade_order_list(self, trade_order_list):
        self.__trade_order_list = trade_order_list
        
    ##### dataframes of TCA output
        
    @property
    def trade_order(self):
        return self.__trade_order

    @trade_order.setter
    def trade_order(self, trade_order):
        self.__trade_order = trade_order

    @property
    def timeline(self):
        return self.__timeline

    @timeline.setter
    def timeline(self, timeline):
        self.__timeline = timeline
        
    @property
    def sparse_market(self):
        return self.__sparse_market

    @sparse_market.setter
    def sparse_market(self, sparse_market):
        self.__sparse_market = sparse_market
        
    @property
    def market(self):
        return self.__market

    @market.setter
    def market(self, market):
        self.__market = market
        
    @property
    def bar(self):
        return self.__bar

    @bar.setter
    def bar(self, bar):
        self.__bar = bar
        
    @property
    def dist(self):
        return self.__dist

    @dist.setter
    def dist(self, dist):
        self.__dist = dist
        
    @property
    def table(self):
        return self.__table

    @table.setter
    def table(self, table):
        self.__table = table
        
    ##### charts
    
    @property
    def timeline_charts(self):
        return self.__timeline_charts

    @timeline_charts.setter
    def timeline_charts(self, timeline_charts):
        self.__timeline_charts = timeline_charts

    @property
    def sparse_market_charts(self):
        return self.__sparse_market_charts

    @sparse_market_charts.setter
    def sparse_market_charts(self, sparse_market_charts):
        self.__sparse_market_charts = sparse_market_charts

    @property
    def bar_charts(self):
        return self.__bar_chart

    @bar_charts.setter
    def bar_charts(self, bar_chart):
        self.__bar_chart = bar_chart

    @property
    def dist_charts(self):
        return self.__dist_charts

    @dist_charts.setter
    def dist_charts(self, dist_charts):
        self.__dist_charts = dist_charts

    @property
    def candlestick_charts(self):
        return self.__candlestick_charts

    @candlestick_charts.setter
    def candlestick_charts(self, candlestick_charts):
        self.__candlestick_charts = candlestick_charts
        
    @property
    def styled_tables(self):
        return self.__styled_tables

    @styled_tables.setter
    def styled_tables(self, styled_tables):
        self.__styled_tables = styled_tables




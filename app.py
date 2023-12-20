import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import mplfinance as mpf
from flask import Flask, render_template, request

app = Flask(__name__)

def calculate_change(data):
    data['Change'] = data['Close'].pct_change()
    return data

def find_spike_days(data):
    spike_days = data[abs(data['Change']) > 0.05].index
    return data.loc[spike_days]

def find_extreme_days(data, window=3):
    rolling_max = data['Close'].rolling(window='180D').max()
    rolling_min = data['Close'].rolling(window='180D').min()

    new_high = (data['Close'] == rolling_max)
    new_low = (data['Close'] == rolling_min)

    # 최고치 또는 최저치를 찍은 후 window일 동안은 다시 찍지 않도록 함
    last_high = last_low = pd.NaT
    for i in range(len(data)):
        if new_high.iloc[i] and (last_high is pd.NaT or (data.index[i] - last_high) >= pd.Timedelta(days=window)):
            last_high = data.index[i]
        else:
            new_high.iloc[i] = False
        if new_low.iloc[i] and (last_low is pd.NaT or (data.index[i] - last_low) >= pd.Timedelta(days=window)):
            last_low = data.index[i]
        else:
            new_low.iloc[i] = False

    max_days = data[new_high].index
    min_days = data[new_low].index

    return data.loc[max_days], data.loc[min_days]


def draw_line_chart_interactive(data, spike_days, max_days, min_days):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close'))
    fig.add_trace(go.Scatter(x=spike_days.index, y=spike_days['Close'], mode='markers', name='Spike', marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=max_days.index, y=max_days['Close'], mode='markers', name='6-month High', marker=dict(color='green')))
    fig.add_trace(go.Scatter(x=min_days.index, y=min_days['Close'], mode='markers', name='6-month Low', marker=dict(color='blue')))

    fig.update_layout(hovermode="x", title='Line Chart Interactive')

    return fig.to_html(full_html=False)

def draw_area_chart_interactive(data, spike_days, max_days, min_days):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close', fill='tozeroy'))
    fig.add_trace(go.Scatter(x=spike_days.index, y=spike_days['Close'], mode='markers', name='Spike', marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=max_days.index, y=max_days['Close'], mode='markers', name='6-month High', marker=dict(color='green')))
    fig.add_trace(go.Scatter(x=min_days.index, y=min_days['Close'], mode='markers', name='6-month Low', marker=dict(color='blue')))

    fig.update_layout(hovermode="x", title='Area Chart Interactive')

    return fig.to_html(full_html=False)

def draw_candle_chart_interactive(data, spike_days, max_days, min_days):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'],
                                         high=data['High'],
                                         low=data['Low'],
                                         close=data['Close'],
                                         width=5)])

    fig.add_trace(go.Scatter(x=spike_days.index, y=spike_days['Close'], mode='markers', name='Spike', marker=dict(color='red', size=8)))
    fig.add_trace(go.Scatter(x=max_days.index, y=max_days['Close'], mode='markers', name='6-month High', marker=dict(color='green', size=8)))
    fig.add_trace(go.Scatter(x=min_days.index, y=min_days['Close'], mode='markers', name='6-month Low', marker=dict(color='blue', size=8)))

    fig.update_layout(hovermode="x", title='Candle Chart Interactive')

    return fig.to_html(full_html=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        chart_type = request.form.get('chart_type')

        data = yf.download(ticker, start='2013-01-01', end='2023-12-13')

        if data.empty:
            return render_template('index.html', error_message="Invalid ticker. Please try again.")

        data = calculate_change(data)
        spike_days = find_spike_days(data)
        max_days, min_days = find_extreme_days(data)

        if chart_type == 'line':
            chart = draw_line_chart_interactive(data, spike_days, max_days, min_days)
        elif chart_type == 'area':
            chart = draw_area_chart_interactive(data, spike_days, max_days, min_days)
        elif chart_type == 'candle':
            chart = draw_candle_chart_interactive(data, spike_days, max_days, min_days)
        else:
            return render_template('index.html', error_message="Invalid chart type. Please try again.")

        return render_template('chart.html', chart=chart)
    
    return render_template('index.html')


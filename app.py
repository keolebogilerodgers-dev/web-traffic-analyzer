import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from dash.exceptions import PreventUpdate
from datetime import datetime

# Load CSV file
csv_path = r"C:\Users\fbda21-008\Downloads\web_server_logs.csv"
df = pd.read_csv(csv_path)
df.columns = df.columns.str.strip()  # Clean up column names

# Data preprocessing
df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
df['Date'] = df['Timestamp'].dt.date
df['Hour'] = df['Timestamp'].dt.hour
df['DayOfWeek'] = df['Timestamp'].dt.day_name()
df['Month'] = df['Timestamp'].dt.month_name()

# Business-related flags
df['IsDemoRequest'] = df['Requested URL'].str.contains('scheduledemo', case=False, na=False)
df['IsPromoRequest'] = df['Requested URL'].str.contains('event', case=False, na=False)
df['IsVirtualAssistant'] = df['Requested URL'].str.contains('assistant|prototype', case=False, na=False)

# Browser parsing
def parse_browser(user_agent):
    user_agent = str(user_agent).lower()
    if 'chrome' in user_agent and 'edg' not in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        return 'Safari'
    elif 'edg' in user_agent:
        return 'Edge'
    elif 'opera' in user_agent:
        return 'Opera'
    else:
        return 'Other'

df['Browser'] = df['User-Agent'].apply(parse_browser)

# Response category
if 'Response Code' in df.columns:
    df['Status'] = df['Response Code'].apply(lambda x: 'Success' if x == 200 else 'Error' if x >= 400 else 'Other')

# Dash App
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Product Sales Analytics Dashboard"

# Utility Card
def create_stat_card(title, value, color):
    return html.Div([
        html.Div(title, style={'fontSize': '0.8rem', 'color': '#666'}),
        html.Div(value, style={'fontSize': '1.5rem', 'fontWeight': 'bold', 'color': color})
    ], style={
        'padding': '15px',
        'borderRadius': '5px',
        'backgroundColor': 'white',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'margin': '5px'
    })

# Charts
def generate_country_chart():
    if 'Country' not in df.columns:
        return html.Div("❌ 'Country' column not found.")
    country_data = df['Country'].value_counts().reset_index()
    country_data.columns = ['Country', 'Request Count']
    fig = px.choropleth(country_data, locations='Country', locationmode='country names',
                        color='Request Count', title='🌍 Requests by Country',
                        color_continuous_scale='Plasma', hover_data=['Request Count'])
    return dcc.Graph(figure=fig)

def generate_business_metrics_chart():
    metrics = {
        'Demo Requests': df['IsDemoRequest'].sum(),
        'Promotional Events': df['IsPromoRequest'].sum(),
        'Virtual Assistant': df['IsVirtualAssistant'].sum()
    }
    fig = px.bar(x=list(metrics.keys()), y=list(metrics.values()), title='📊 Key Business Metrics',
                 labels={'x': 'Metric', 'y': 'Count'}, color=list(metrics.keys()),
                 text=list(metrics.values()))
    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
    return dcc.Graph(figure=fig)

def generate_response_analysis():
    if 'Response Code' not in df.columns:
        return html.Div("❌ 'Response Code' column not found.")

    status_data = df['Status'].value_counts(normalize=True).reset_index()
    status_data.columns = ['Status', 'Percentage']
    status_data['Percentage'] *= 100

    fig1 = px.pie(status_data, names='Status', values='Percentage', title='📊 Success vs Error Rates',
                  hole=0.4, color_discrete_map={'Success': '#2ecc71', 'Error': '#e74c3c', 'Other': '#3498db'})

    response_data = df['Response Code'].value_counts().reset_index()
    response_data.columns = ['Response Code', 'Count']
    fig2 = px.bar(response_data, x='Response Code', y='Count', title='📟 Detailed Response Codes',
                  color='Response Code', text_auto=True)

    return html.Div([
        dcc.Graph(figure=fig1, style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(figure=fig2, style={'display': 'inline-block', 'width': '48%'})
    ], style={'display': 'flex'})

def generate_job_analysis():
    if 'Job Type Requested' not in df.columns:
        return html.Div("❌ 'Job Type Requested' column not found.")
    job_data = df['Job Type Requested'].value_counts().reset_index()
    job_data.columns = ['Job Type', 'Count']
    fig = px.bar(job_data, x='Job Type', y='Count', title='👔 Job Type Distribution',
                 color='Job Type', text_auto=True)
    return dcc.Graph(figure=fig)

def generate_temporal_analysis():
    fig1 = px.line(df.groupby('Hour').size().reset_index(name='Count'), x='Hour', y='Count',
                   title='🕒 Hourly Request Pattern', markers=True)

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_data = df.groupby('DayOfWeek').size().reset_index(name='Count')
    daily_data['DayOfWeek'] = pd.Categorical(daily_data['DayOfWeek'], categories=day_order, ordered=True)
    daily_data = daily_data.sort_values('DayOfWeek')
    fig2 = px.line(daily_data, x='DayOfWeek', y='Count', title='📅 Daily Request Pattern', markers=True)

    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data = df.groupby('Month').size().reset_index(name='Count')
    monthly_data['Month'] = pd.Categorical(monthly_data['Month'], categories=month_order, ordered=True)
    monthly_data = monthly_data.sort_values('Month')
    fig3 = px.line(monthly_data, x='Month', y='Count', title='📈 Monthly Request Trend', markers=True)

    return html.Div([
        dcc.Graph(figure=fig1, style={'display': 'inline-block', 'width': '32%'}),
        dcc.Graph(figure=fig2, style={'display': 'inline-block', 'width': '32%'}),
        dcc.Graph(figure=fig3, style={'display': 'inline-block', 'width': '32%'})
    ], style={'display': 'flex'})

def generate_browser_analysis():
    browser_data = df['Browser'].value_counts().reset_index()
    browser_data.columns = ['Browser', 'Count']
    fig = px.pie(browser_data, names='Browser', values='Count', title='🌐 Browser Distribution', hole=0.3)
    return dcc.Graph(figure=fig)

def generate_demo_conversion_analysis():
    if 'Country' not in df.columns:
        return html.Div("❌ 'Country' column not found.")
    demo_data = df.groupby('Country')['IsDemoRequest'].agg(['sum', 'count']).reset_index()
    demo_data.columns = ['Country', 'DemoRequests', 'TotalRequests']
    demo_data['ConversionRate'] = (demo_data['DemoRequests'] / demo_data['TotalRequests']) * 100
    fig = px.choropleth(demo_data, locations='Country', locationmode='country names',
                        color='ConversionRate', title='📈 Demo Request Conversion Rate by Country (%)',
                        hover_data=['DemoRequests', 'TotalRequests'], color_continuous_scale='Viridis')
    return dcc.Graph(figure=fig)

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("📊 Product Sales Analytics Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
        html.P("Business Intelligence Dashboard for Analyzing Web Server Logs",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px'}),

    html.Div([
        create_stat_card("Total Requests", f"{len(df):,}", "#3498db"),
        create_stat_card("Demo Requests", f"{df['IsDemoRequest'].sum():,}", "#2ecc71"),
        create_stat_card("Promo Events", f"{df['IsPromoRequest'].sum():,}", "#e74c3c"),
        create_stat_card("Virtual Assist", f"{df['IsVirtualAssistant'].sum():,}", "#9b59b6"),
        create_stat_card("Success Rate", f"{df[df['Response Code'] == 200].shape[0]/len(df)*100:.1f}%", "#f39c12"),
    ], style={'display': 'flex', 'justifyContent': 'space-around'}),

    dcc.Tabs(id="main-tabs", value='tab-overview', children=[
        dcc.Tab(label='🌍 Overview', value='tab-overview'),
        dcc.Tab(label='📊 Business Metrics', value='tab-business'),
        dcc.Tab(label='📟 Technical Analysis', value='tab-technical'),
        dcc.Tab(label='👔 Job Analysis', value='tab-jobs'),
        dcc.Tab(label='🕒 Temporal Analysis', value='tab-temporal'),
    ]),

    html.Div(id='tabs-content')
])

@app.callback(
    Output('tabs-content', 'children'),
    Input('main-tabs', 'value')
)
def render_content(tab):
    if tab == 'tab-overview':
        return html.Div([generate_country_chart(), generate_browser_analysis()])
    elif tab == 'tab-business':
        return html.Div([generate_business_metrics_chart(), generate_demo_conversion_analysis()])
    elif tab == 'tab-technical':
        return html.Div([generate_response_analysis()])
    elif tab == 'tab-jobs':
        return html.Div([generate_job_analysis()])
    elif tab == 'tab-temporal':
        return html.Div([generate_temporal_analysis()])
    else:
        raise PreventUpdate

# Run Server
if __name__ == '__main__':
    app.run(debug=True)


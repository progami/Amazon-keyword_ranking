import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.express as px
import calendar

def process_data():
    # Load the data
    df = pd.read_csv('helium10-ranks.csv')

    # Drop the unnecessary columns
    df.drop(['Title', 'ASIN', 'Marketplace'], axis=1, inplace=True)

    # Convert 'Search Volume' and 'Organic Rank' to numeric
    df['Search Volume'] = pd.to_numeric(df['Search Volume'], errors='coerce')
    df['Organic Rank'] = pd.to_numeric(df['Organic Rank'], errors='coerce')

    # Replace values greater than 306 with 306
    df['Organic Rank'] = df['Organic Rank'].apply(lambda x: 306 if x > 306 else x)
    # Convert 'Date Added' to datetime
    df['Date Added'] = pd.to_datetime(df['Date Added'])

    # Function to assign each date to a bi-weekly period
    def assign_biweekly_period(date):
        if date.day <= 15:
            return f"1-15 {date.strftime('%b %Y')}"
        else:
            last_day = calendar.monthrange(date.year, date.month)[1]
            return f"16-{last_day} {date.strftime('%b %Y')}"

    # Assign each row to a bi-weekly period
    df['Bi-weekly Period'] = df['Date Added'].apply(assign_biweekly_period)

    # Create the pivot table for Organic Rank
    pivot_or = df.pivot_table(values='Organic Rank', index='Keyword', columns='Bi-weekly Period', aggfunc='mean')

    # Replace '-' back to NaN for computations
    pivot_or.replace('-', np.nan, inplace=True)

    # order the columns chronologically
    pivot_or = pivot_or.reindex(sorted(pivot_or.columns, key=lambda x: pd.to_datetime(' '.join(x.split(' ')[1:]))), axis=1)

    # Create the pivot table for Search Volume
    pivot_sv = df.pivot_table(values='Search Volume', index='Keyword', columns='Bi-weekly Period', aggfunc='mean')

    # Calculate the average search volume for each keyword over the last two periods
    last_two_periods = pivot_sv.columns[-2:]
    avg_sv = pivot_sv[last_two_periods].mean(axis=1).fillna(0)

    # Append a new column to the pivot_or DataFrame with the average search volume for each keyword
    pivot_or['Avg SV'] = avg_sv

    # Sort the rows of the pivot_or DataFrame by search volume in descending order
    pivot_or.sort_values(by='Avg SV', ascending=False, inplace=True)

    # Round all data to one decimal point, except 'Avg SV' to zero decimal places
    pivot_or = pivot_or.round(1)
    pivot_or['Avg SV'] = pivot_or['Avg SV'].round(0)

    return pivot_or


def create_app(pivot_or):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])  # cosmo theme from Bootswatch

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='or-graph')
            ], width=12),
        ], style={'height': '450px'}),
        html.P('Select keywords to plot their Organic Rank by Bi-weekly Period on the graph above.'),
        dbc.Row([
            dbc.Col([
                dcc.Checklist(
                    id='keywords-checklist',
                    options=[{'label': f"{i} ({pivot_or.loc[i, 'Avg SV']:.0f})", 'value': i} for i in pivot_or.index],
                    value=[pivot_or.index[0]],
                )
            ], width=2),
            dbc.Col([
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in pivot_or.reset_index().columns],
                    data=pivot_or.reset_index().to_dict('records'),
                    style_cell={
                        'textAlign': 'left',
                        'padding': '5px'
                    },
                    style_header={
                        'fontWeight': 'bold',
                        'backgroundColor': 'lightgrey',
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'Keyword'},
                            'width': '150px'
                        }
                    ],
                    page_size=20,
                    style_as_list_view=True,
                    style_table={'overflowX': 'auto'},
                )
            ], width=10)
        ])
    ], fluid=True)

    @app.callback(
        Output('or-graph', 'figure'),
        [Input('keywords-checklist', 'value')]
    )
    def update_graph(keywords):
        data = pivot_or.loc[keywords].reset_index().melt(id_vars=['Keyword'], value_vars=pivot_or.columns[:-1], value_name='Organic Rank')
        fig = px.line(data, x='Bi-weekly Period', y='Organic Rank', color='Keyword', hover_data={'Keyword':True, 'Bi-weekly Period': False, 'Organic Rank': True})

        # Customize the appearance of the graph
        fig.update_layout(
            title='Organic Rank by Bi-weekly Period',
            xaxis_title='Bi-weekly Period',
            yaxis_title='Organic Rank',
            font=dict(
                size=14,
                color='black'
            ),
            plot_bgcolor='white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                title='Click to hide/show:',
                itemclick='toggleothers',
                itemdoubleclick='toggle'
            )
        )
        return fig

    return app

if __name__ == '__main__':
    pivot_or = process_data()

    app = create_app(pivot_or)

    app.run_server(debug=True, host='0.0.0.0')


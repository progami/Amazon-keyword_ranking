import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from keyword_ranking_backend import process_data


def create_app(df_final, avg_sv):
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
                    options=[{'label': f"{i} ({avg_sv[i]:.0f})", 'value': i} for i in df_final.index],
                    value=[df_final.index[0]],
                )
            ], width=2),
            dbc.Col([
                dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in df_final.reset_index().columns],
                    data=df_final.reset_index().to_dict('records'),
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
        or_columns = [col for col in df_final.columns if 'Organic Rank' in col]
        data = df_final.loc[keywords].reset_index().melt(id_vars=['Keyword'], value_vars=or_columns, value_name='Organic Rank')
        data['variable'] = data['variable'].str.replace(' Organic Rank', '')
        fig = px.line(data, x='variable', y='Organic Rank', color='Keyword', hover_data={'Keyword':True, 'variable': False, 'Organic Rank': True})
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
    df_final, avg_sv = process_data()
    app = create_app(df_final, avg_sv)
    app.run_server(debug=True, host='0.0.0.0')



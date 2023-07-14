from flask import Flask, jsonify
import pandas as pd
import numpy as np
import calendar
from datetime import datetime
import warnings
from flask_cors import CORS
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

app = Flask(__name__)
CORS(app)  # enable CORS

def assign_biweekly_period(date):
    if date.day <= 15:
        return f"1-15 {date.strftime('%b %y')}"
    else:
        last_day = calendar.monthrange(date.year, date.month)[1]
        return f"16-{last_day} {date.strftime('%b %y')}"

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

    # Assign each row to a bi-weekly period
    df['Bi-weekly Period'] = df['Date Added'].apply(assign_biweekly_period)

    # Create the pivot table for Organic Rank
    pivot_or = df.pivot_table(values='Organic Rank', index='Keyword', columns='Bi-weekly Period', aggfunc='mean')

    # Replace '-' back to NaN for computations
    pivot_or.replace('-', np.nan, inplace=True)

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

    # Load the spend data
    df_spend = pd.read_excel('Sponsored Products Search term report.xlsx')

    # Convert 'Date' to datetime
    df_spend['Date'] = pd.to_datetime(df_spend['Date'])

    # Assign each row to a bi-weekly period
    df_spend['Bi-weekly Period'] = df_spend['Date'].apply(assign_biweekly_period)

    # Group by 'Customer Search Term' and 'Bi-weekly Period' and calculate the sum of 'Spend'
    df_spend = df_spend.groupby(['Customer Search Term', 'Bi-weekly Period'])['Spend'].sum().reset_index()

    # Create the pivot table for Spend
    pivot_spend = df_spend.pivot(index='Customer Search Term', columns='Bi-weekly Period', values='Spend')

    # Fill NaN values with 0
    pivot_spend.fillna(0, inplace=True)

    # Append ' Spend' to the column names
    pivot_spend.columns = [c + ' Spend' for c in pivot_spend.columns]

    # Round to 0 decimal places
    pivot_spend = pivot_spend.round(0)

    # Ensure all keywords have an entry in avg_sv
    all_keywords = set(pivot_or.index).union(set(pivot_spend.index))
    for keyword in all_keywords:
        if keyword not in avg_sv:
            avg_sv[keyword] = 0

    # Ensure both pivot_or and pivot_spend have the same set of periods
    all_periods = sorted(set(pivot_or.columns[:-1]).union(set(c.replace(' Spend', '') for c in pivot_spend.columns)))
    for period in all_periods:
        if period not in pivot_or.columns:
            pivot_or[period] = np.nan
        if period + ' Spend' not in pivot_spend.columns:
            pivot_spend[period + ' Spend'] = 0

    # Combine the two dataframes, alternating between Organic Rank and Spend for each period
    df_final = pd.DataFrame(index=pivot_or.index)
    for period in all_periods:
        df_final[period + ' Organic Rank'] = pivot_or[period]
        df_final[period + ' Spend'] = pivot_spend[period + ' Spend']

    # Break each period into its components
    period_parts = [p.split(' ') for p in all_periods]
    # Convert the month and year part back to a datetime
    for parts in period_parts:
        parts[1] = datetime.strptime(parts[1] + " " + parts[2], "%b %y")
    # Sort by the components
    period_parts.sort(key=lambda x: (x[1], int(x[0].split('-')[0])))
    # Convert the month and year part back to a string
    for parts in period_parts:
        parts[1] = parts[1].strftime("%b %y")
    # Join the parts back together (and remove the year part)
    sorted_periods = [" ".join(parts[:-1]) for parts in period_parts]

    # Create the new order of columns
    new_order = []
    for period in sorted_periods:
        new_order.append(period + ' Organic Rank')
        new_order.append(period + ' Spend')

    # Sort the columns in df_final
    df_final = df_final[new_order]
    

    df_final = df_final.replace({np.nan: None})
    return df_final, avg_sv


@app.route('/data', methods=['GET'])
def get_data():
    print("Received GET request on /data")  # Debugging message
    df_final, avg_sv = process_data()
    # Convert the DataFrame to a dictionary so it can be converted to JSON
    data_dict = df_final.to_dict()
    # Convert the Series to a dictionary so it can be converted to JSON
    avg_sv_dict = avg_sv.to_dict()
    # Print the data
    # print(f"Data: {data_dict}")
    # print(f"Avg SV: {avg_sv_dict}")
    # Return the data as JSON
    return jsonify({'data': data_dict, 'avg_sv': avg_sv_dict})

if __name__ == '__main__':
    print("Starting Flask app")
    app.run(debug=True, port=5001)




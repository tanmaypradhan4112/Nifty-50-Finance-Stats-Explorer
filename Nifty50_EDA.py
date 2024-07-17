import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import requests
import base64

url = 'https://in.tradingview.com/symbols/NSE-NIFTY/components/'

# Fetch the webpage content
response = requests.get(url)
response.raise_for_status()  # Raise an error for bad status codes

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

st. set_page_config(layout="wide")
st.title("Nifty 50 Finance Stats Explorer")

# Web Scraping NSE India Data
@st.cache_data
def load_data():

    # Find the table
    table = soup.find('table')

    # Extract headers
    headers = [header.text for header in table.find_all('th')]

    # Extract rows
    rows = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cells = row.find_all('td')
        row_data = []
        for cell in cells:
            # Check if the cell contains an anchor tag
            anchor = cell.find('a')
            if anchor:
                # Append the text of the anchor tag
                row_data.append(anchor.text)
            else:
                # Append the cell text, ignoring any sup tag text
                text = ''.join(cell.stripped_strings)
                row_data.append(text.split(' ')[0])  # Split and take the first part before any spaces
        rows.append(row_data)

    # Create a DataFrame
    df = pd.DataFrame(rows, columns=headers)


    ## DATA PROCESSING ##

    # rename Symbol column to Company
    df.rename(columns = {'Symbol':'Company'}, inplace = True)
    df.rename(columns = {'Analyst Rating':'AnalystRating'}, inplace = True)
    df.rename(columns = {'Change %':'Change'}, inplace = True)
    df.rename(columns = {'Div yield %TTM':'DivyieldTTM'}, inplace = True)

    # removing the null value
    df['EPS dil growthTTM YoY'] = (
    df['EPS dil growthTTM YoY']
    .str.replace('—', '0')  # Replace em dash with '0'
    .str.replace('%', '')   # Remove '%' sign
    .str.replace('−', '-')  # Replace Unicode minus with regular hyphen-minus
    .str.replace('+', '')   # Remove '+' sign
    .str.replace(',','')
    .astype(float)
)

    # Formatting Market Cap column
    df['Market cap'] = df['Market cap'].str.replace('BUSD', '').str.replace(' ', '').astype(float)

    #Formatting Price Column
    df['Price'] = df['Price'].str.replace('INR','').str.replace(',','').astype(float)

    # Formatting Change % column
    df['Change'] = df['Change'].str.replace('%', '').str.replace('−', '-').astype(float)

    # Formatting Volumn column
    df['Volume'] = df['Volume'].str.replace('\u202fK', '')
    df['Volume'] = df['Volume'].str.replace('M', '').str.replace(' ', '').astype(float)

    # Formmating Rel Volumn
    df['Rel Volume'] = df['Rel Volume'].astype(float)

    # Formmating P/E column
    df['P/E'] = df['P/E'].str.replace('—','0').astype(float)

    # Formatting EPS dilTTM
    df['EPS dilTTM'] = df['EPS dilTTM'].str.replace('—','0').str.replace('USD','').str.replace('−','-').astype(float)

    # Formatting Div yield %TTM column
    df['DivyieldTTM'] = df['DivyieldTTM'].str.replace('%','').astype(float)

    # Return the DataFrame
    return df

def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="nifty50_data_stats.csv"> Download CSV File </a>'
    return href

nifty_data = load_data()

# Multiselect Side bar
st.sidebar.header('User Input Features')
nifty_company_values = sorted(nifty_data.Company.unique())
selected_company = st.sidebar.multiselect('Company',nifty_company_values,nifty_company_values)

nifty_company_Sector = sorted(nifty_data.Sector.unique())
selected_Sector = st.sidebar.multiselect('Sector',nifty_company_Sector,nifty_company_Sector)

nifty_company_Rating = sorted(nifty_data.AnalystRating.unique())
selected_Rating = st.sidebar.multiselect('Sector',nifty_company_Rating,nifty_company_Rating)

nifty_data_stats = nifty_data[(nifty_data.Company.isin(selected_company)) & (nifty_data.Sector.isin(selected_Sector))  & (nifty_data.AnalystRating  .isin(selected_Rating))]

st.write('The Nifty 50 Index constituents can be found in the table below. Sort NIFTY stock components by various financial metrics and data such as performance')
st.write(f'Nifty 50 Results: {nifty_data_stats.shape[0]} rows found')
st.dataframe(nifty_data_stats)

st.markdown(download_csv(nifty_data_stats),unsafe_allow_html=True)

# Data Analysis Section
st.header('Nifty Stocks Analysis/Comparision')

c1,c2,c3 = st.columns(3,gap='small')

with c1:
    stock1 = st.selectbox("Stock 1",selected_company)

with c2:
    stock2 = st.selectbox("Stock 2",reversed(selected_company))

# with c3:
#     stock3 = st.selectbox("Stock 3",selected_company)

if st.button('Analyze and Compare'):
    v1,v2 = st.columns(2,gap='medium')

    with v1:
        st.markdown(f'#### Comparision of Market Cap ({stock1} vs {stock2})')
        # plotting bar plot of Stock 1 and Stock 2
        x = [stock1, stock2]

        stock1_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock1, 'Market cap'].values[0]
        stock2_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock2, 'Market cap'].values[0]

        # Data for plotting
        market_cap_data = {'Company': x, 'Market cap': [stock1_market_cap, stock2_market_cap]}
        market_cap_df = pd.DataFrame(market_cap_data)

        # Bar Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        bars = sns.barplot(x='Company', y='Market cap', data=market_cap_df, palette='viridis', ax=ax)
        for bar in bars.patches:
            bar_value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar_value,
                f'{bar_value:,.0f}M',
                ha='center',
                va='bottom'
            )

        ax.set_title('Market Capitalization of Companies')
        ax.set_xlabel('Company')
        ax.set_ylabel('Market Cap (in Billion USD)')
        st.pyplot(fig)

    with v2:
        st.markdown(f'#### Comparision of Change % ({stock1} vs {stock2})')

        x = [stock1, stock2]

        stock1_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock1, 'Change'].values[0]
        stock2_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock2, 'Change'].values[0]

        # Data for plotting
        change_data = {'Company': x, 'Change': [stock1_market_cap, stock2_market_cap]}
        change_df = pd.DataFrame(change_data)

        # Bar Plot
        colors = ['green' if x > 0 else 'red' for x in change_df['Change']]
        fig, ax = plt.subplots(figsize=(6, 6.2))
        sns.barplot(x='Company', y='Change', data=change_df,palette=colors)
        ax.set_title("Change Percentage of Companies")
        ax.set_xlabel('Company')
        ax.set_ylabel('Change %')
        plt.axhline(0, color='black', linewidth=0.8)
        st.pyplot(fig)

    v3,v4 = st.columns(2,gap='medium')

    with v3:
        st.markdown(f'#### Comparision of Volume ({stock1} vs {stock2})')
        # plotting bar plot of Stock 1 and Stock 2
        x = [stock1, stock2]

        stock1_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock1, 'Volume'].values[0]
        stock2_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock2, 'Volume'].values[0]

        # Data for plotting
        market_volume = {'Company': x, 'Volume': [stock1_market_cap, stock2_market_cap]}
        market_volumne_df = pd.DataFrame(market_volume)

        # Bar Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        bars = sns.barplot(x='Company', y='Volume', data=market_volumne_df, palette='viridis', ax=ax)

        # Add values on top of bars
        for bar in bars.patches:
            bar_value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar_value,
                f'{bar_value:,.0f}M',
                ha='center',
                va='bottom'
            )

        ax.set_title('Stock Volume of Companies')
        ax.set_xlabel('Company')
        ax.set_ylabel('Volume (in Million)')
        st.pyplot(fig)

    with v4:
        st.markdown(f'#### Comparision of Dividend Yield%({stock1} vs {stock2})')

        x = [stock1, stock2]

        stock1_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock1, 'DivyieldTTM'].values[0]
        stock2_market_cap = nifty_data_stats.loc[nifty_data_stats['Company'] == stock2, 'DivyieldTTM'].values[0]

        # Data for plotting
        Divyield_data = {'Company': x, 'DivyieldTTM': [stock1_market_cap * 100, stock2_market_cap * 100]}
        Divyield_df = pd.DataFrame(Divyield_data)

        # Bar Plot
        fig, ax = plt.subplots(figsize=(6, 6))
        bars = sns.barplot(x='Company', y='DivyieldTTM', data=Divyield_df, palette='viridis', ax=ax)
        for bar in bars.patches:
            bar_value = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar_value,
                f'{bar_value:,.0f}%',
                ha='center',
                va='bottom'
            )
        ax.set_title("Change Percentage of Companies")
        ax.set_xlabel('Company')
        ax.set_ylabel('Div yield% TTM')
        plt.axhline(0, color='black', linewidth=0.8)
        st.pyplot(fig)





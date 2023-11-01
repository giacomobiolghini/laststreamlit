import streamlit as st
import plotly.express as px
import pandas as pd
import os
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import warnings
import openpyxl
import plotly.figure_factory as ff
import xlsxwriter
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Exponento", layout="wide")
st.title("Example Exponento data")

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.close()
    processed_data = output.getvalue()
    return processed_data


#streamlit run /Users/giacomobiolghini/Documents/Helper_Zoo/code/Dashboard/Dashboard.py

#upload file excel
fl=st.file_uploader(":file_folder: Upload a file", type=(["xlsx"]))
if fl is not None:
    filename = fl.name
    st.write(filename)
    df = pd.read_excel(filename)
#else:
    #df=pd.read_excel("Prova.xlsx")


    #divide page into 2 columns
    col1, col2 = st.columns((2))
        
    #df["Booking Date"] = pd.to_datetime(["Booking Date"])
    ###################################################################################################
    #FILTER BY DATE
        
    #get min and max date
    #startDate = pd.to_datetime(df["Booking Date"]).min()
    startDate = df["Booking Date"].min()
    #endDate = pd.to_datetime(df["Booking Date"]).min()
    endDate = df["Booking Date"].max()

    #select the dates
    with col1:
        #date1 = pd.to_datetime(st.date_input("Start Date", startDate))
        date1 = st.date_input("Start Date", startDate)

    with col2:
        #date2 = pd.to_datetime(st.date_input("End date", endDate))
        date2 = st.date_input("End date", endDate)

    #filter the databse by the date selected
    df = df[(df["Booking Date"].dt.date >= date1) & (df["Booking Date"].dt.date <= date2)].copy()   #.dt.date needed to compare naive data python with datatime framework
    ###################################################################################################

    ###################################################################################################
    #FILTER BY FEATURE
    st.sidebar.header("Choose your filter: ")

    #Filter by Customer Type
    customertype = st.sidebar.multiselect("Pick the customer type", df["Customer Type"].unique())
    if not customertype:
        df2 = df.copy()
    else:
        df2 = df[df["Customer Type"].isin(customertype)]

    #Filter by Location
    location = st.sidebar.multiselect("Pick the location", df2["Location"].unique())
    if not location:
        df3 = df2.copy()
    else:
        df3 = df2[df2["Location"].isin(location)]

    #filter by intersection
    if not customertype and not location:
        filtered_df=df
    elif not location:
        filtered_df= df[df["Customer Type"].isin(customertype)]
    elif not customertype:
        filtered_df= df[df["Location"].isin(location)]
    else:
        filtered_df= df2[df2["Customer Type"].isin(customertype) & df2["Location"].isin(location)]

    ###################################################################################################
    customertype_df = filtered_df.groupby(by = ["Customer Type"], as_index = False)["Revenue"].sum()
    with col1:
        st.subheader("Revenue by customer type")
        fig = px.bar(customertype_df, x = "Customer Type", y = "Revenue", text= ['${:,.2f}'.format(x) for x in customertype_df["Revenue"]], template = "seaborn")
        st.plotly_chart(fig, use_container_width = True, height = 200) 

    #location_df = filtered_df.groupby(by = ["Location"], as_index = False)["Revenue"].sum()
    with col2:
        st.subheader("Revenue by location")
        fig = px.pie(filtered_df, values = "Revenue", names = "Location", hole = 0.5)
        fig.update_traces(text = filtered_df["Location"], textposition = "outside")
        st.plotly_chart(fig, use_container_width = True)


    cl1, cl2 = st.columns((2))
    with cl1:
        with st.expander("Customer type data"):
            st.write(customertype_df.style.background_gradient(cmap="Blues"))
            csv = customertype_df.to_csv(index = True).encode('utf-8')
            excel = to_excel(customertype_df)
            st.download_button("Download Data CSV", data =csv, file_name= "Customer_Type.csv", mime = "text/cvs", help = "Click here to dowmload the data as CSV file")
            st.download_button("Download Data XLSX", data =excel, file_name= "Customer_Type.xlsx",  help = "Click here to dowmload the data as XLSX file")
            

    location_df = filtered_df.groupby(by = ["Location"], as_index = False)["Revenue"].sum()
    with cl2:
            with st.expander("Location data"):
                st.write(location_df.style.background_gradient(cmap="Blues"))
                csv = location_df.to_csv(index = True).encode('utf-8')
                excel = to_excel(location_df)
                st.download_button("Download Data CSV", data =csv, file_name= "Location.csv", mime = "text/cvs", help = "Click here to dowmload the data as CSV file")
                st.download_button("Download Data XLSX", data =excel, file_name= "Location.xlsx",  help = "Click here to dowmload the data as XLSX file")
            

    #TIME SERIES ANALYSIS
    filtered_df["month_year"] = filtered_df["Booking Date"].dt.to_period("M")
    st.subheader("Time Series Analysis")

    linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Revenue"].sum()).reset_index()
    fig2 = px.line(linechart, x = "month_year", y="Revenue", labels = {"Revenues":"Amount"}, height=500, width=1000, template = "gridon")
    st.plotly_chart(fig2, use_container_wodth=True)

    with st.expander("View Data of TimeSeries"):
        st.write(linechart.T.style.background_gradient(cmap="Blue"))
        csv = linechart.to_csv(index = True).encode('utf-8')
        excel = to_excel(linechart)
        st.download_button("Download Data CSV", data =csv, file_name= "Time_series.csv", mime = "text/cvs", help = "Click here to dowmload the data as CSV file")
        st.download_button("Download Data XLSX", data =excel, file_name= "Time-series.xlsx",  help = "Click here to dowmload the data as XLSX file")

    ###############################################
    #DATA SUMMARY AND SCATTERPLOT
    
    st.subheader(":point_right : Month wise Customer type revenues summary")
    with st.expander("Summary_Table"):
        st.markdown("Month wise sub-Category Table")
        filtered_df["month"]=filtered_df["Booking Date"].dt.month_name()
        customer_type_year = pd.pivot_table(data = filtered_df, values ="Revenue", index = ["Customer Type"], columns = "month")
        st.write(customer_type_year.style.background_gradient(cmap="Blues"))

    #SCATTER PLOT
    data1= px.scatter(filtered_df, x="Revenue", y= "Profit")
    data1['layout'].update(title="Relationship between Revenue and Profit",
                           titlefont = dict(size=20), xaxis = dict(title = "Revenue", titlefont = dict(size=19)),
                           yaxis =dict(title = "Profit", titlefont = dict(size=19)))
    st.plotly_chart(data1, use_container_width=True)

    data2= px.scatter(filtered_df, x="Revenue", y= "Hotel Nights")
    data2['layout'].update(title="Relationship between Revenue and Hotel nights",
                           titlefont = dict(size=20), xaxis = dict(title = "Revenue", titlefont = dict(size=19)),
                           yaxis =dict(title = "Hotel nights", titlefont = dict(size=19)))
    st.plotly_chart(data2, use_container_width=True)





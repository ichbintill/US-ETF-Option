import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import einstellung
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

start=time.time()
Zeitpunkt=datetime.now().strftime("%Y-%m-%d %H:%M")

raum=einstellung.raum
ETF_list_link=einstellung.ETF_list_link
Option_datum_list_link=einstellung.Option_datum_list_link
google_sheet_link=einstellung.google_sheet_link
google_sheet_ID=einstellung.google_sheet_ID
google_sheet_name=einstellung.google_sheet_name
json_link=einstellung.json_link

# CSV-Daten laden
ETF_list= pd.read_csv(ETF_list_link)
Option_datum_list=pd.read_csv(Option_datum_list_link)

# Option-Datum filtern  
AB=(pd.to_datetime(Option_datum_list["Daten"],errors="coerce")<datetime.now()).sum()
BIS=AB+4


# Option-Data rechnen und zusammenstellen 
Option_datas=[]
for i in range(ETF_list.shape[0]):
    etf= yf.Ticker(ETF_list.iloc[i,0])

    for d in range(AB,BIS):
        Option_datum=datetime.strptime(Option_datum_list.iloc[d,0],"%Y/%m/%d").strftime("%Y-%m-%d")
        try:
            chain=etf.option_chain(Option_datum)
        except ValueError as e:
            row=[Zeitpunkt,Option_datum,ETF_list.iloc[i,0],"kein_daten","kein_daten","kein_daten"]
            Option_datas.append(row)
            continue
            
        alles_open= chain.calls.loc[(chain.calls["ask"]>raum),"openInterest"].sum()+chain.puts.loc[(chain.puts["ask"]>raum),"openInterest"].sum()
        ask_callpreise= (chain.calls.loc[(chain.calls["ask"]>raum),"openInterest"]*chain.calls.loc[(chain.calls["ask"]>raum),"ask"]).sum()
        ask_putpreise= (chain.puts.loc[(chain.puts["ask"]>raum),"openInterest"]*chain.puts.loc[(chain.puts["ask"]>raum),"ask"]).sum()
        strike_call=(chain.calls.loc[(chain.calls["ask"]>raum),"openInterest"]*chain.calls.loc[(chain.calls["ask"]>raum),"strike"]).sum()
        strike_put=(chain.puts.loc[(chain.puts["ask"]>raum),"openInterest"]*chain.puts.loc[(chain.puts["ask"]>raum),"strike"]).sum()
        ask_call=ask_callpreise/alles_open
        ask_put=ask_putpreise/alles_open
        strike=(strike_call+strike_put)/alles_open
    
        preis=etf.fast_info["last_price"]
        
        row=[Zeitpunkt,Option_datum,ETF_list.iloc[i,0],ask_call-ask_put,ask_call-ask_put+strike,preis]
        Option_datas.append(row)
        
print(Option_datas)


# google_sheet
creds = Credentials.from_service_account_file(json_link, scopes=google_sheet_link)
service= build('sheets','v4',credentials=creds)

## Wie viele data hatte google_sheet im Moment ? 
Option_data_google= service.spreadsheets().values().get(
    spreadsheetId=google_sheet_ID,
    range=google_sheet_name
).execute()
Option_data_google_values=len(Option_data_google.get("values",[]))

## google_sheet macht ein Update 
service.spreadsheets().values().update(
    spreadsheetId=google_sheet_ID,
    range=google_sheet_name+"!A"+str(int(Option_data_google_values)+1),
    valueInputOption="USER_ENTERED",  
    body={"values":Option_datas}
).execute()


end=time.time()
print(end-start,"Sekunden")
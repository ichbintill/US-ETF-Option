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
list_link=einstellung.list_link
daten_link=einstellung.daten_link
google_sheet_link=einstellung.google_sheet_link
google_sheet_ID=einstellung.google_sheet_ID
google_sheet_name=einstellung.google_sheet_name
json_link=einstellung.json_link
AB=einstellung.AB
BIS=einstellung.BIS
list= pd.read_csv(list_link)
daten=pd.read_csv(daten_link)

creds = Credentials.from_service_account_file(json_link, scopes=google_sheet_link)
service= build('sheets','v4',credentials=creds)


Option_daten=[]
for i in range(list.shape[0]):
    etf= yf.Ticker(list.iloc[i,0])

    for d in range(AB,BIS):
        Option_date=datetime.strptime(daten.iloc[d,0],"%Y/%m/%d").strftime("%Y-%m-%d")
        try:
            chain=etf.option_chain(Option_date)
        except ValueError as e:
            row=[Zeitpunkt,Option_date,list.iloc[i,0],"kein_daten","kein_daten","kein_daten"]
            Option_daten.append(row)
            ## print(Zeitpunkt,Option_date,list.iloc[i,0],"kein_daten","kein_daten","kein_daten")
            ## print("Error:",e)
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
        
        row=[Zeitpunkt,Option_date,list.iloc[i,0],ask_call-ask_put,ask_call-ask_put+strike,preis]
        Option_daten.append(row)
        ## print(Zeitpunkt,Option_date,list.iloc[i,0],ask_call-ask_put,ask_call-ask_put+strike,preis)

print(Option_daten)

Option_data= service.spreadsheets().values().get(
    spreadsheetId=google_sheet_ID,
    range=google_sheet_name
).execute()

Option_data_values=len(Option_data.get("values",[]))



service.spreadsheets().values().update(
    spreadsheetId=google_sheet_ID,
    range=google_sheet_name+"!A"+str(int(Option_data_values)+1),
    valueInputOption="USER_ENTERED",  
    body={"values":Option_daten}
).execute()


end=time.time()
print(end-start,"Sekunden")

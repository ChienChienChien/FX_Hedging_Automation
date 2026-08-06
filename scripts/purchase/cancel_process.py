import pandas as pd
from getLib import CancelLib, PASLib

df = CancelLib.get_cancel_order()
df['CommodityId'] = df['採購單號'] + '-' + df['採購單項次']
pas_outstanding = PASLib.get_outstanging_amount_by_account('P2')

df = pd.merge(df, pas_outstanding, on=['CommodityId'], how='left')
df = df[df['Qty']!=0]
df = df.dropna(subset=['Qty'])
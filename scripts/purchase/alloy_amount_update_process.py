from getLib import PASLib
from config import GlobalVar
from insert_format import pas_tradehty
import utils
import coil_process
import pandas as pd

def update_process(basedate):
    # 抓取PAS中的採購單金額(含已調整)
    pas_amount = PASLib.get_pas_update_amount()
    pas_amount = pas_amount[['採購單號','採購單項次','Qty']]
    pas_amount.columns = ['採購單號','採購單項次','pas_amount']
    pas_amount['pas_amount'] = abs(pas_amount['pas_amount'])
    
    # 抓取鋼捲最新採購單金額
    new_amount_coil = coil_process.order_process()
    new_amount_coil = new_amount_coil[['採購單號','採購單項次','發行日期','預估採購金額']]
    # 合併合金與鋼捲資訊
    # new_amount = pd.concat([new_amount_alloy,new_amount_coil], axis=0)
    new_amount = new_amount_coil
    new_amount['發行日期'] = pd.to_datetime(new_amount['發行日期'])
    new_amount.rename(columns={'預估採購金額':'new_amount'}, inplace=True)
    
    # 篩選出outstanding不為零的採購單
    pas_outstanding = PASLib.get_outstanging_amount_by_account('P1')
    pas_outstanding = pas_outstanding[pas_outstanding['Qty']!=0]
    pas_open = set(pas_outstanding['CommodityId'])
    
    # 比對Notes抓取的最新採購金額和PAS中的採購金額
    # 若有差異，則進行調整
    update = pd.merge(pas_amount, new_amount, how='left', on=['採購單號','採購單項次'])
    update['CommodityId'] = update['採購單號'] + '-' + update['採購單項次']
    update = update[update['CommodityId'].isin(pas_open)]
    update['diff'] = update['new_amount'] - update['pas_amount']
    bool_diff = abs(update['diff']) >= 0.000001
    update = update[bool_diff]
    update['匯率offer'] = update['CommodityId'].apply(lambda x:PASLib.get_issue_price_by_comdty(x))
    update['tradeDate'] = basedate
    
    return update


class Update:
    
    def Init():
        Update.df = update_process(GlobalVar.basedate)
        
    def update_insert():
        for insert_type in ['P1']:
            trade = pas_tradehty.update_amount_format(Update.df)
            store, errmsg = utils.insert_tradehty(trade)

    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Update.df, 'Update')
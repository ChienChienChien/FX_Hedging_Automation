from getLib import OrderLib, SettleLib, ContractLib
import utils
import pandas as pd
from insert_format import pas_tradehty
from utils import float2date, float2str
from config import GlobalVar


def process(str_basedate, date_filter=True):
    # 取得合約至訂單資訊，並調整格式
    order = OrderLib.get_order_csv(str_basedate)
    order = order.dropna(subset=['訂單日期'])
    order['項次'] = order['項次'].astype(int).astype(str)
    order['訂單日期'] = pd.to_datetime(order['訂單日期'].astype(int).astype(str))
    
    # 取得結清明細，並調整格式
    settle = SettleLib.get_settle_csv(str_basedate)
    settle['項次'] = settle['項次'].astype(int).astype(str)
    settle['發票日期'] = settle['發票日期'].apply(lambda x: float2date(x))
    settle['發票編號'] = settle['發票編號'].apply(lambda x: float2str(x))
    settle['發票項次'] = settle['發票項次'].apply(lambda x: float2str(x))
    
    # 合約至訂單與結清明細合併
    df = pd.merge(order, settle, on=['訂單','項次'], how='left')
    df = df.dropna(subset=['發票日期'])
    
    if date_filter:
        df = df[df['發票日期']==str_basedate]
        df = df[~df['會計匯率'].isnull()]
        
    return df
        

class Settle:
    
    def Init():
        # 取得所有合約的結清明細
        Settle.settleDF = process(GlobalVar.str_basedate)
        
        # 取得各內部帳號(S1,S2,Z4)的合約清單
        Settle.order_s1 = ContractLib.get_contract_id_by_account('S1')
        Settle.order_s2 = ContractLib.get_contract_id_by_account('S2')
        Settle.order_z4 = ContractLib.get_contract_id_by_account('Z4')
        
        # 取得各內部帳號(S1,S2,Z4)的已取消合約清單
        Settle.order_canceled_s1 = ContractLib.get_contract_id_canceled_by_account('S1')
        Settle.order_canceled_s2 = ContractLib.get_contract_id_canceled_by_account('S2')
        Settle.order_canceled_z4 = ContractLib.get_contract_id_canceled_by_account('Z4')
        
        # 合約清單剔除已取消的部分
        settle_order_set_s1 = set(Settle.order_s1['合約號碼']).difference(Settle.order_canceled_s1['合約號碼'])
        settle_order_set_s2 = set(Settle.order_s2['合約號碼']).difference(Settle.order_canceled_s2['合約號碼'])
        settle_order_set_z4 = set(Settle.order_z4['合約號碼']).difference(Settle.order_canceled_z4['合約號碼'])
        
        # 依不同內部帳號的合約清單，對應出各內部帳號的結清明細
        Settle.settle_s1 = Settle.settleDF[Settle.settleDF['合約號碼'].isin(settle_order_set_s1)]
        Settle.settle_s2 = Settle.settleDF[Settle.settleDF['合約號碼'].isin(settle_order_set_s2)]
        Settle.settle_z4 = Settle.settleDF[Settle.settleDF['合約號碼'].isin(settle_order_set_z4)]
    
    def settle_insert():
        # 轉成trade格式，並寫入DB
        for insert_type in ['S1']:
            trade_settle = pas_tradehty.settle_format(Settle.settle_s1, insert_type)
            store, errmsg = utils.insert_tradehty(trade_settle)
        
        for insert_type in ['S2']:
            trade_settle = pas_tradehty.settle_format(Settle.settle_s2, insert_type)
            store, errmsg = utils.insert_tradehty(trade_settle)
            
        for insert_type in ['Z4']:
            trade_settle = pas_tradehty.settle_format(Settle.settle_z4, insert_type)
            store, errmsg = utils.insert_tradehty(trade_settle)
    
    def push_msg():
        gp = Settle.settle_s1.groupby(by=['幣別','產品類別']).sum()['結清金額'].to_frame().reset_index()
        msg = ''
        if not gp.empty:
            msg = '結清部位：\n'
            for index, row in gp.iterrows():
                msg += row['幣別'] + '\t'
                msg += row['產品類別'] + '\t' 
                msg += '{:,.2f}'.format(row['結清金額']) + '\n'
            
        msg += '\n'
        return msg
        
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Settle.settle_s1, 'Settle_s1')
        save_obj.save(Settle.settle_s2, 'Settle_s2')
        save_obj.save(Settle.settle_z4, 'Settle_z4')

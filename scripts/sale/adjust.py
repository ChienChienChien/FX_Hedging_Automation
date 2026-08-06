from getLib import ContractLib, OrderLib, FxTools
import pandas as pd
import datetime
import utils
from config import GlobalVar
from insert_format import pas_tradehty


class Adj:
        
    def Init():
        
        # 取得合約至訂單資訊
        Adj.order = OrderLib.get_order_csv(GlobalVar.str_basedate)
        Adj.order = Adj.order.dropna(subset=['訂單日期'])
        Adj.order['項次'] = Adj.order['項次'].astype(int).astype(str)
        Adj.order['訂單日期'] = pd.to_datetime(Adj.order['訂單日期'].astype(int).astype(str))
        
        # 依不同內部帳號(S1,S2,Z4)，取得調整項的資訊
        Adj.contract_adj_s1 = Adj.process(GlobalVar.str_basedate, 'S1')
        Adj.contract_adj_s2 = Adj.process(GlobalVar.str_basedate, 'S2')
        Adj.contract_adj_z4 = Adj.process(GlobalVar.str_basedate, 'Z4')
                
    def adj_insert():
        # 轉成trade格式，並寫入DB
        for iaccount in ['S1']:
            trade = pas_tradehty.adjustment_format(Adj.contract_adj_s1, iaccount)
            store, errmsg = utils.insert_tradehty(trade)
        
        for iaccount in ['S2']:
            trade = pas_tradehty.adjustment_format(Adj.contract_adj_s2, iaccount)
            store, errmsg = utils.insert_tradehty(trade)
            
        for iaccount in ['Z4']:
            trade = pas_tradehty.adjustment_format(Adj.contract_adj_z4, iaccount)
            store, errmsg = utils.insert_tradehty(trade)
    
    def process(str_basedate, iaccount):
        # 每筆合約的總交易金額加總(訂單成立+立帳結清+調整項)
        contract_sum = ContractLib.get_contract_total_sum(iaccount)
        
        # 若加總金額不為0，則需要進行調整
        contract_adj = contract_sum[contract_sum['Amount']!=0]
        
        res = []
        basedate = datetime.datetime.strptime(str_basedate, '%Y%m%d')
        
        # 依每筆需調整的合約，確認合約下的每筆訂單狀態皆為完成(狀態=C)
        # 若訂單狀態皆為完成，則將調整金額、價格等資訊儲存在res中
        for index, row in contract_adj.iterrows():
            contract_id = row['CommodityId']
            order_subset = Adj.order.query('合約號碼==@contract_id')
            if order_subset['狀態'].eq('C').all() and not order_subset.empty:
                amount = row['Amount']
                bs = 'B' if amount < 0 else 'S'
                currency = row['Currency']
                rate = FxTools.get_spot_rate(str_basedate, currency)
                res.append([contract_id, basedate, currency, bs, abs(amount), rate])
        
        # 將res轉成DataFrame
        df = pd.DataFrame(res, columns=['contract_id','basedate','currency','bs','amount','rate'])
        df.basedate = pd.to_datetime(df.basedate)
        
        return df
    
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Adj.contract_adj_s1, 'Adjustemnt_s1')
        save_obj.save(Adj.contract_adj_s2, 'Adjustemnt_s2')
        save_obj.save(Adj.contract_adj_z4, 'Adjustemnt_z4')
        
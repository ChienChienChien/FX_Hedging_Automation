from getLib import PASLib, SettleLib, FxTools, AlloyLib, CoilLib
from config import GlobalVar
from insert_format import pas_tradehty
import utils
import pandas as pd
import alloy_process
import coil_process


def combine_order_process():
    sap_weight = SettleLib.get_settle_weight_sum_by_order()
    alloy_order = AlloyLib.get_alloy()
    coil_order = CoilLib.get_coil_track()
    combine = pd.concat([alloy_order,coil_order], axis=0, sort=False)
    combine = combine[['採購單號','採購單項次','WAP發票重']]
    res = pd.merge(combine, sap_weight, on=['採購單號','採購單項次'], how='left')
    res['diff_sap'] = abs(res['WAP發票重'] - res['發票重量'])
    res['diff percentage'] = res['diff_sap'] / res['WAP發票重']
    
    return res


class Adj:
    
    def Init():
        Adj.combine = combine_order_process()
        Adj.adjsut_p1 = Adj.adjust_process('P1', GlobalVar.basedate)
        Adj.adjsut_p2 = Adj.adjust_process('P2', GlobalVar.basedate)
        Adj.adjsut_y4 = Adj.adjust_process('Y4', GlobalVar.basedate)

    def adjust_insert():
        # 轉成trade格式，並寫入DB
        for insert_type in ['P1']:
            trade = pas_tradehty.adjustment_format(Adj.adjsut_p1, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
        
        for insert_type in ['P2']:
            trade = pas_tradehty.adjustment_format(Adj.adjsut_p2, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
        for insert_type in ['Y4']:
            trade = pas_tradehty.adjustment_format(Adj.adjsut_y4, insert_type)
            store, errmsg = utils.insert_tradehty(trade)

    def adjust_process(iaccount, basedate=None):
        df = PASLib.get_outstanging_amount_by_account(iaccount)
        df[['order_no','order_item']] = df['CommodityId'].str.rsplit('-', n=1, expand=True)
        df['status'] = df['Qty'].apply(lambda x: 'O' if abs(round(x,6))!=0 else 'C')

        m = pd.merge(df, Adj.combine, how='inner', 
                     left_on=['order_no','order_item'],
                     right_on=['採購單號','採購單項次'])
        bool1 = m['diff percentage'] < 0.1
        bool4 = m['status'] == 'O'
        res = m[bool1 & bool4].copy()
        res['date'] = basedate
        res['rate_adj'] = FxTools.get_spot_rate(basedate)
            
        return res
    
    def push_msg():
        
        msg = ''
        if not Adj.adjsut_p1.empty:
            msg += '調整項：\n'
            for index, row in Adj.adjsut_p1.iterrows():
                msg += row['CommodityId'] + '\t'
                msg += '{:,.2f}'.format(row['Qty']) + '\n'
            msg += '\n'    
        
        return msg
        
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Adj.adjsut_p1, 'Adjust_p1')
        save_obj.save(Adj.adjsut_p2, 'Adjust_p2')
        save_obj.save(Adj.adjsut_y4, 'Adjust_y4')
        
    
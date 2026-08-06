from getLib import CoilLib, SettleLib, PASLib, FxTools
import pandas as pd
import utils
from insert_format import pas_tradehty
from config import TRADE_COL_NAME, GlobalVar, INTERNAL_DEAL_DICT_ADJ
from utils import OPTools

def pre_order_settle_process(basedate, iaccount):
    # 取得鋼捲點價的資訊
    track_order = CoilLib.get_coil_pre_order_track()
    
    # 取得PAS中的採購單
    pas_order = CoilLib.get_coil_pre_order_remaining_amount(iaccount)

    # PAS有, Notes有 -> 比對金額差異，結清差異金額
    # PAS有, Notes沒有 -> 將PAS中剩餘的金額全部結清
    settle_pre_order = pd.merge(pas_order, track_order, on=['採購單號','採購單項次'], how='left')
    settle_pre_order['剩餘金額'] = settle_pre_order.apply(lambda x:OPTools.pre_order_amount_cal(x), axis=1)
    settle_pre_order['剩餘金額'] = settle_pre_order['剩餘金額'].fillna(0)
    settle_pre_order['差異金額'] = settle_pre_order['總金額'] - settle_pre_order['剩餘金額']
    settle_pre_order = settle_pre_order[settle_pre_order['差異金額']!=0]
    if iaccount in ('P1','Y4'):
        settle_pre_order['BS'] = settle_pre_order['差異金額'].apply(lambda x:'B' if x>=0 else 'S')
    else:
        settle_pre_order['BS'] = settle_pre_order['差異金額'].apply(lambda x:'S' if x>=0 else 'B')
    settle_pre_order['statement'] = settle_pre_order['差異金額'].apply(lambda x:'鋼捲點價結清' if x>=0 else '鋼捲點價更新')
    settle_pre_order['差異金額'] = abs(settle_pre_order['差異金額'])
    settle_pre_order['匯率offer'] = FxTools.get_spot_rate(basedate)
    settle_pre_order['交易日期'] = basedate
    
    
    return settle_pre_order

def settle_process(basedate):
    
    df = SettleLib.get_settle()
    df['發票過帳日期'] = pd.to_datetime(df['發票過帳日期'])
    df = df[df['發票過帳日期']==basedate]
    
    return df


class Settle:
    
    def Init():
        # 取得所以採購單的結清資料
        Settle.df = settle_process(GlobalVar.basedate)
        
        # 依內部帳號的採購單號清單，對應出各內部帳號的結清明細 
        Settle.settle_p1 = Settle.settle_process('P1')
        Settle.settle_p2 = Settle.settle_process('P2')
        Settle.settle_y4 = Settle.settle_process('Y4')

        # 鋼捲點價結清資料
        Settle.pre_order_p1 = pre_order_settle_process(GlobalVar.basedate, 'P1')
        Settle.pre_order_p2 = pre_order_settle_process(GlobalVar.basedate, 'P2')
        Settle.pre_order_y4 = pre_order_settle_process(GlobalVar.basedate, 'Y4')
        
        # 調整項沖轉資料
        Settle.adj_reverse_p1 = Settle.check_adj(Settle.settle_p1, 'P1')
        Settle.adj_reverse_p2 = Settle.check_adj(Settle.settle_p2, 'P2')
        Settle.adj_reverse_y4 = Settle.check_adj(Settle.settle_y4, 'Y4')
        
    def settle_insert():
        # 轉成trade格式，並寫入DB
        for insert_type in ['P1']:
            trade = pas_tradehty.settle_format(Settle.settle_p1, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
        
        for insert_type in ['P2']:
            trade = pas_tradehty.settle_format(Settle.settle_p2, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
        for insert_type in ['Y4']:
            trade = pas_tradehty.settle_format(Settle.settle_y4, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
    def pre_order_settle():
        # 轉成trade格式，並寫入DB
        for insert_type in ['P1']:
            trade = pas_tradehty.pre_order_settle_format(Settle.pre_order_p1, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
        
        for insert_type in ['P2']:
            trade = pas_tradehty.pre_order_settle_format(Settle.pre_order_p2, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
            
        for insert_type in ['Y4']:
            trade = pas_tradehty.pre_order_settle_format(Settle.pre_order_y4, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
            
    def adj_reverse_insert():
        # Settle.adj_reverse已經為trade格式，直接寫入
        store_order, errmsg_order = utils.insert_tradehty(Settle.adj_reverse_p1)
        store_order, errmsg_order = utils.insert_tradehty(Settle.adj_reverse_p2)
        store_order, errmsg_order = utils.insert_tradehty(Settle.adj_reverse_y4)

    def settle_process(iaccount):

        # 依內部帳號的採購單號清單，對應出各內部帳號的結清明細 
        # 若該單號已經剩餘部位已經為0，則不再使用SAP資料結清
        df = PASLib.get_outstanging_amount_by_account(iaccount)
        df = df[df['Qty']!=0]
        df[['採購單號','採購單項次']] = df['CommodityId'].str.rsplit('-', n=1, expand=True)
        df = pd.merge(df, Settle.df, on=['採購單號','採購單項次'], how='inner')

        return df

    def check_adj(res, iaccount):
        # 抓取所有結清的採購單號
        comdty_set = set(res['CommodityId'])
        note_adjust = INTERNAL_DEAL_DICT_ADJ.get(iaccount).get('Notes')
        dfs = []
        for comdty in comdty_set:
            # 抓取以寫入TradeHty的調整項
            df = PASLib.get_pas_trade_adj(iaccount, comdty)
            # 調整項為基數，代表結清前已經先調整過了，所以須將先前調整的部位沖轉掉
            if len(df)%2 == 1:
                df = df[df['Notes']==note_adjust]
                df = df.sort_values(by='TradeDate', ascending=False)
                df = df.iloc[0,:].to_frame().T
                df = df[TRADE_COL_NAME]
                df['TradeDate'] = GlobalVar.basedate
                df = pas_tradehty.adjustment_reverse_format(df, iaccount)
                dfs.append(df)
            
        if len(dfs) != 0:
            trade = pd.concat(dfs)
        else:
            trade = pd.DataFrame(columns=[TRADE_COL_NAME])
            
        return trade
    
    def push_msg():
        gp = Settle.settle_p1.groupby(by=['鋼種']).sum()['發票金額'].to_frame().reset_index()
        msg = ''
        if not gp.empty:
            msg += '結清部位：\n'
            for index, row in gp.iterrows():
                msg += row['鋼種'] + '\t'
                msg += '{:,.2f}'.format(row['發票金額']) + '\n'
                
            msg += '\n'
            
        if not Settle.pre_order_p1.empty:
            msg += '鋼捲點價結清部位：\n'
            for index, row in Settle.pre_order_p1.iterrows():
                msg += row['採購單號'] + '\t'
                msg += '{:,.2f}'.format(row['差異金額']) + '\n'
        
        return msg

    def push_msg_2nd():
        msg = ''
        if not Settle.pre_order_p1.empty:
            msg += '鋼捲點價結清部位：\n'
            for index, row in Settle.pre_order_p1.iterrows():
                msg += row['採購單號'] + '\t'
                msg += '{:,.2f}'.format(row['差異金額']) + '\n'
        
        return msg

    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Settle.df, 'Settle_all')
        save_obj.save(Settle.settle_p1, 'Settle_p1')
        save_obj.save(Settle.settle_p2, 'Settle_p2')
        save_obj.save(Settle.settle_y4, 'Settle_y4')
        save_obj.save(Settle.adj_reverse_p1, 'Adj_reverse_p1')
        save_obj.save(Settle.adj_reverse_p1, 'Adj_reverse_p2')
        save_obj.save(Settle.adj_reverse_p1, 'Adj_reverse_y4')
        save_obj.save(Settle.pre_order_p1, 'Settle_pre_order_p1')
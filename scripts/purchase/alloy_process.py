from getLib import AlloyLib, PASLib, FxTools
from config import GlobalVar, ALLOY_SWITCH
from insert_format import pas_tradehty
import pandas as pd
import utils
from utils import OPTools
import comdty_process
import datetime

def order_process(incremental=True):
    df = AlloyLib.get_alloy()
    df['發行日期']=pd.to_datetime(df['發行日期'])
    df['CGId'] = df['合金'].apply(lambda x:OPTools.comdty_group_filter(x))
    
    df['單價'] = df['料號'].apply(lambda x: OPTools.map_material_price(x))
    df['預估採購金額'] = df['重量'] * df['單價']
    df['預估採購金額'] = df['預估採購金額'].astype(float)
    df = df.dropna(subset=['預估採購金額'])
    df = df[df['預估採購金額']!=0]
    df['OrderNo'] = df['採購單號'] + '-' + df['採購單項次']

    # 將重複的項次篩選掉
    df = df.drop_duplicates(subset=['採購單號','採購單項次'])
    df['OrderNo'] = df['採購單號'] + '-' + df['採購單項次']

    if not df.empty:
        if incremental:
            # 判斷合金採購是否計入部位
            df['if_pos'] = df.apply(lambda x: OPTools.alloy_position_filter(x), axis=1)
            df = df[df['if_pos']=='Y']

    return df
    

class Alloy:
    
    def Init():
        Alloy.notes_order = order_process()
        Alloy.notes_order_all = order_process(False)
        Alloy.new_p1, Alloy.cancel_p1 = Alloy.process(GlobalVar.basedate, 'P1')
        Alloy.new_p2, Alloy.cancel_p2 = Alloy.process(GlobalVar.basedate, 'P2')
        Alloy.new_y4, Alloy.cancel_y4 = Alloy.process(GlobalVar.basedate, 'Y4')
        
    def commodity_insert():
        # 寫入Commodity, CommodityGroup, CommodityGroupLink
        comdty_process.write_comdty(Alloy.new_p1, Group=False)
        
    def alloy_insert():
        # 轉成trade格式，寫入DB
        for df, insert_type in zip([Alloy.new_p1],['P1']):
            # 寫入新的合金採購單
            trade = pas_tradehty.order_format(df, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
            
        # 合金部位拋轉的開關
        if ALLOY_SWITCH:
            for df, insert_type in zip([Alloy.new_p2,Alloy.new_y4],['P2','Y4']):
                # 寫入新的合金採購單
                trade = pas_tradehty.order_format(df, insert_type)
                store_order, errmsg_order = utils.insert_tradehty(trade)

    def alloy_cancel_insert():
        cancel_list = [Alloy.cancel_p1,Alloy.cancel_p2,Alloy.cancel_y4]
        iaccount_list = ['P1','P2','Y4']
        
        for df, insert_type in zip(cancel_list,iaccount_list):
            trade = pas_tradehty.cancel_format(df, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)

    def process(basedate, iaccount):
        pas_order = PASLib.get_alloy_outstanding_amount_by_account(iaccount)
        
        # 比較PAS與Notes的採購單, 留下Notes中新增的採購單
        notes_set = set(Alloy.notes_order['OrderNo'])
        notes_all_set = set(Alloy.notes_order_all['OrderNo'])
        pas_set = set(pas_order['CommodityId'])
        
        # Notes有，PAS沒有 -> 新增部位
        only_notes = notes_set.difference(pas_set)
        filter_1 = Alloy.notes_order['OrderNo'].isin(only_notes)
        order_incremental = Alloy.notes_order[filter_1].copy()

        # 以新增當日作為成交日期,當日的匯率作為成本與拋轉匯率
        order_incremental['成交日期'] = basedate
        order_incremental['匯率offer'] = FxTools.get_spot_rate(basedate)

        # Notes沒有，PAS有 -> 取消部位
        only_pas = pas_set.difference(notes_all_set)
        filter_1 = pas_order['CommodityId'].isin(only_pas)
        filter_2 = pas_order['Qty']!=0
        filter_3 = pas_order['CommodityId'].str.len()<14
        order_cancel = pas_order[filter_1 & filter_2 & filter_3].copy()
        order_cancel['basedate'] = basedate
        order_cancel['匯率'] = FxTools.get_spot_rate(basedate)
        
        return order_incremental, order_cancel

     
    def push_msg():
        # 鋼捲採購單
        gp = Alloy.new_p1.groupby(by=['合金']).sum()['預估採購金額'].to_frame().reset_index()
        msg = ''
        if not gp.empty:
            msg = '合金新增部位：\n'
            for index, row in gp.iterrows():
                msg += row['合金'] + '\t'
                msg += '{:,.2f}'.format(row['預估採購金額']) + '\n'
            msg += '\n'

        # 取消
        if not Alloy.cancel_p1.empty:
            msg += '取消部位：\n'
            for index, row in Alloy.cancel_p1.iterrows():
                msg += row['UnderlyingId'] + '\t' + row['CommodityId'] + '\t'
                msg += '{:,.2f}'.format(row['Qty']) + '\n'
                
            msg += '\n'
            
        return msg
                
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Alloy.new_p1, 'alloy_new_p1')
        save_obj.save(Alloy.cancel_p1, 'alloy_cancel_p1')

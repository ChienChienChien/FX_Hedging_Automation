from getLib import CoilLib, PASLib, FxTools
from config import GlobalVar, COIL_SWITCH
import pandas as pd
import comdty_process
import utils
from utils import OPTools
from insert_format import pas_tradehty
import datetime


def order_process(incremental=True):
    # 取得鋼捲採購資訊
    df = CoilLib.get_coil_track()
    
    df['預估採購金額'] = df.apply(lambda x:OPTools.order_amount_cal(x) ,axis=1)
    df = df.drop_duplicates(subset=['採購單號','採購單項次'])
    df = df.dropna(subset=['預估採購金額'])
    
    df = df[df['預估採購金額']!=0]
    df['OrderNo'] = df['採購單號'] + '-' + df['採購單項次']

    if not df.empty:
        if incremental:
            df['if_pos'] = df.apply(lambda x: OPTools.coil_position_filter(x), axis=1)
            df = df[df['if_pos']=='Y']
            df = df.dropna(subset=['採購單項次'])
    
    return df


def pre_order_process(basedate):
    # 取得鋼捲點價的資訊
    track_order = CoilLib.get_coil_pre_order_track()
    track_order = track_order[track_order['合約單價']!=0]
    track_order_set = set(track_order['採購單號'])
    
    # 取得PAS中的採購單
    pas_order = CoilLib.get_coil_pre_order_remaining_amount('P1')
    pas_order_set = set(pas_order['採購單號'])
    
    # Notes有,PAS沒有 -> 新增點價
    track_only = track_order_set.difference(pas_order_set)
    new_pre_order = track_order[track_order['採購單號'].isin(track_only)].copy()
    new_pre_order['成交日期'] = basedate
    new_pre_order['匯率offer'] = FxTools.get_spot_rate(basedate)
    new_pre_order['預估採購金額'] = new_pre_order.apply(lambda x:OPTools.pre_order_amount_cal(x), axis=1)
    new_pre_order['預估採購金額'] = new_pre_order['預估採購金額'].astype(float)
    new_pre_order = new_pre_order.dropna(subset=['預估採購金額'])

    return new_pre_order


class Coil:
    
    def Init():
        # 抓取鋼捲點價與採購單資訊
        Coil.notes_order = order_process()
        Coil.notes_order_all = order_process(False)
        Coil.pre_order = pre_order_process(GlobalVar.basedate)
        Coil.new_p1, Coil.cancel_p1 = Coil.process(GlobalVar.basedate, 'P1')
        Coil.new_p2, Coil.cancel_p2 = Coil.process(GlobalVar.basedate, 'P2')
        Coil.new_y4, Coil.cancel_y4 = Coil.process(GlobalVar.basedate, 'Y4')
        
    def commodity_insert():
        # 新增的鋼捲需寫入Commodity, CommodityGroup, CommodityGroupLink
        comdty_process.write_comdty(Coil.new_p1, Group=False)
        comdty_process.write_comdty(Coil.pre_order, Group=False)
    
    def coil_insert():
        # 轉成trade格式，寫入DB
        for df, insert_type in zip([Coil.new_p1],['P1']):
            # 寫入新的鋼捲採購單
            trade = pas_tradehty.order_format(df, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
            
        # 鋼捲部位拋轉的開關
        if COIL_SWITCH:
            for df, insert_type in zip([Coil.new_p2,Coil.new_y4],['P2','Y4']):
                # 寫入新的鋼捲採購單
                trade = pas_tradehty.order_format(df, insert_type)
                store_order, errmsg_order = utils.insert_tradehty(trade)
                
    def pre_order_insert():
        # 鋼捲/圓胚點價寫入
        for insert_type in ['P1','P2','Y4']:
            # 寫入新的鋼捲點價
            trade = pas_tradehty.order_format(Coil.pre_order, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
    
    def coil_cancel_insert():
        cancel_list = [Coil.cancel_p1,Coil.cancel_p2,Coil.cancel_y4]
        iaccount_list = ['P1','P2','Y4']
        
        for df, insert_type in zip(cancel_list,iaccount_list):
            trade = pas_tradehty.cancel_format(df, insert_type)
            store_order, errmsg_order = utils.insert_tradehty(trade)
    
    def process(basedate, iaccount):
        pas_order = PASLib.get_coil_outstanding_amount_by_account(iaccount)
        
        # 比較PAS與Notes的採購單, 留下Notes中新增的採購單
        notes_set = set(Coil.notes_order['OrderNo'])
        notes_all_set = set(Coil.notes_order_all['OrderNo'])
        pas_set = set(pas_order['CommodityId'])
        
        # Notes有，PAS沒有 -> 新增部位
        only_notes = notes_set.difference(pas_set)
        filter_1 = Coil.notes_order['OrderNo'].isin(only_notes)
        order_incremental = Coil.notes_order[filter_1].copy()
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
        gp = Coil.new_p1.groupby(by=['合金']).sum()['預估採購金額'].to_frame().reset_index()
        msg = ''
        if not gp.empty:
            msg += '鋼捲新增部位：\n'
            for index, row in gp.iterrows():
                msg += row['合金'] + '\t'
                msg += '{:,.2f}'.format(row['預估採購金額']) + '\n'
            msg += '\n'    
        
        # 鋼捲點價
        gp = Coil.pre_order.groupby(by=['合金']).sum()['預估採購金額'].to_frame().reset_index()
        
        if not gp.empty:
            msg += '點價新增部位：\n'
            for index, row in gp.iterrows():
                msg += row['合金'] + '\t'
                msg += '{:,.2f}'.format(row['預估採購金額']) + '\n'
                
            msg += '\n'
        
        # 取消
        if not Coil.cancel_p1.empty:
            msg += '取消部位：\n'
            for index, row in Coil.cancel_p1.iterrows():
                msg += row['UnderlyingId'] + '\t' + row['CommodityId'] + '\t'
                msg += '{:,.2f}'.format(row['Qty']) + '\n'
                
            msg += '\n'
        
        return msg

    def push_msg_2nd():

        # 鋼捲點價
        msg = ''
        gp = Coil.pre_order.groupby(by=['合金']).sum()['預估採購金額'].to_frame().reset_index()
        
        if not gp.empty:
            msg += '點價新增部位：\n'
            for index, row in gp.iterrows():
                msg += row['合金'] + '\t'
                msg += '{:,.2f}'.format(row['預估採購金額']) + '\n'
                
            msg += '\n'

        return msg

    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Coil.new_p1, 'coil_new_p1')
        save_obj.save(Coil.pre_order, 'Coil_pre_order')
        save_obj.save(Coil.cancel_p1, 'coil_cancel_p1')


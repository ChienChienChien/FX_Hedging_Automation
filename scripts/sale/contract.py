from getLib import ContractLib, OrderLib, FxTools
import pandas as pd
import utils
from insert_format import pas_tradehty
from config import INTERNAL_SWITCH, INTERNAL_CURRENCY, INTERNAL_TYPE, INTERNAL_ALL
from config import GlobalVar
import datetime
import settle

class CTools:
    
    def Init():
        CTools.settle_df = settle.process(GlobalVar.str_basedate, date_filter=False)
        CTools.order = OrderLib.get_order_csv(GlobalVar.str_basedate)
        CTools.order = CTools.order.dropna(subset=['訂單日期'])
        CTools.order['項次'] = CTools.order['項次'].astype(int).astype(str)
        CTools.order['訂單日期'] = pd.to_datetime(CTools.order['訂單日期'].astype(int).astype(str))
        CTools.contract_order = ContractLib.get_contract_order()
        
    def currency_rate_setter_new(x, date_str, iaccount):
        # 設定新增合約時使用的匯率
        # S1：Spot
        # S2：USD Spot/EUR Forward
        # Z4：USD Spot/EUR Forward
        if len(x)!=0:
            if iaccount == 'S1':
                return FxTools.get_spot_rate(date_str, x['幣別'])
            else:
                if x['幣別'] == 'USD':
                    return FxTools.get_spot_rate(date_str, x['幣別'])
                else:
                    return FxTools.get_forward_rate(date_str, x['幣別'], x['天期'])
    
    def currency_rate_setter_update(x, date_str, iaccount):
        # 設定更新合約金額時使用的匯率
        # S1：Spot
        # S2：Buy為多拋，使用Spot結清；Sell為補拋，USD使用Spot/EUR使用Forward
        # Z4：Buy為補拋，USD使用Spot/EUR使用Forward；Sell為多拋，使用Spot結清
        
        if len(x)!=0:
            if iaccount == 'S1':
                return FxTools.get_spot_rate(date_str, x['幣別'])
            elif iaccount == 'S2':
                if x['bs'] == 'B':
                    return FxTools.get_spot_rate(date_str, x['幣別'])
                else:
                    if x['幣別'] == 'USD':
                        return FxTools.get_spot_rate(date_str, x['幣別'])
                    else:
                        return FxTools.get_forward_rate(date_str, x['幣別'], x['天期'])
            else:
                if x['bs'] == 'S':
                    return FxTools.get_spot_rate(date_str, x['幣別'])
                else:
                    if x['幣別'] == 'USD':
                        return FxTools.get_spot_rate(date_str, x['幣別'])
                    else:
                        return FxTools.get_forward_rate(date_str, x['幣別'], x['天期'])

    def currency_rate_setter_cancel(x, date_str):
        # 合約取消的匯率皆使用Spot

        if len(x)!=0:
            return FxTools.get_spot_rate(date_str, x['幣別'])
                
    def position_ar_filter(contract_id):
        # 判斷合約是否已有AR立帳
        # Y:已立帳 / N:未立帳
        sub_settle = CTools.settle_df.query('合約號碼==@contract_id')
        sub_settle = sub_settle.dropna(subset=['發票日期'])
        if len(sub_settle)==0:
            return 'N'
        else:
            return 'Y'
    
    def position_close_filter(contract_id):
        # 判斷合約是否已經Close
        # Y:已全部結清 / N:尚未完全結清
        sub_order = CTools.order.query('合約號碼==@contract_id')
        if sub_order['狀態'].eq('C').all() and not sub_order.empty:
            return 'Y'
        else:
            return 'N'
        
    def buy_sell_direction(x, iaccount):
        # 判斷更新合約金額於不同iaccount的Buy/Sell方向
        # (x)為301F合約金額減去PAS的合約金額
        # x>=0：原本拋得不夠，要增加合約金額
        # x<0：原本拋得太多，要減少合約金額
        if iaccount in ['S1','Z4']:
            return 'B' if x>=0 else 'S'
        else:
            return 'S' if x>=0 else 'B'
        
    def contract_cancel_filter(contract_id):
        # 1. 先判斷呈核狀態是否為"已駁回"
        # 2. 再判斷合約狀態與訂單狀態
        #   (a) 合約狀態為已結案且沒有訂單
        #   (b) 合約狀態為已結案且訂單已刪除
        # Y:已刪除合約 / N:未刪除合約
        sub_order = CTools.contract_order.query('合約號碼==@contract_id')
        if sub_order['呈核狀態'].eq('已駁回').all():
            return 'Y'
        else:
            if sub_order['合約狀態'].eq('已結案').all():
                sub_order = sub_order.dropna(subset=['訂單號碼'])
                if sub_order['狀態'].eq('刪除     已核准').all() or sub_order.empty:
                    return 'Y'
                else:
                    return 'N'
            else:
                return 'N'

class Contract:
    
    def Init():
        # 初始化CTools
        CTools.Init()
        
        # 取得當日(basedate)的合約資訊
        Contract._301F = ContractLib.get_contract()
        Contract._301F_set = set(Contract._301F['合約號碼'])
        
        Contract.new_s1, Contract.update_s1, Contract.cancel_s1 = Contract.process(GlobalVar.str_basedate, 'S1')
        Contract.new_s2, Contract.update_s2, Contract.cancel_s2 = Contract.process(GlobalVar.str_basedate, 'S2')
        Contract.new_z4, Contract.update_z4, Contract.cancel_z4 = Contract.process(GlobalVar.str_basedate, 'Z4')
        
    def commodity_insert():
        # 新合約需先寫入Commodity, CommodityGroup, CommodityGroupLink
        for df in [Contract.new_s1]:
            comdty = pas_tradehty.commodity_fornmat(df)
            comdtyLink = pas_tradehty.commodityGroupLink_fornmat(df)
            comdtyGroup = pas_tradehty.commodityGroup_fornmat(df)
            store, errmsg = utils.insert_commodity(comdty)
            store, errmsg = utils.insert_commodity_group_link(comdtyLink)
            store, errmsg = utils.insert_commodity_group(comdtyGroup)
        
    def contract_insert():
        # 轉成trade格式，並寫入DB
        for df, insert_type in zip([Contract.new_s1],['S1']) :
            # 寫入新的合約
            trade = pas_tradehty.contract_format(df, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
        # 內部交易與沖轉部位
        if INTERNAL_SWITCH:
            new_list = [Contract.new_s2,Contract.new_z4]
            iaccount_list = ['S2','Z4']
            for df, insert_type in zip(new_list,iaccount_list):
                trade = pas_tradehty.contract_format(df, insert_type)
                store, errmsg = utils.insert_tradehty(trade)
                
    def update_insert():
        update_list = [Contract.update_s1,Contract.update_s2,Contract.update_z4]
        iaccount_list = ['S1','S2','Z4']
        
        for df, insert_type in zip(update_list,iaccount_list):
            trade = pas_tradehty.update_format(df, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
    def cancel_insert():
        cancel_list = [Contract.cancel_s1,Contract.cancel_s2,Contract.cancel_z4]
        iaccount_list = ['S1','S2','Z4']
        
        for df, insert_type in zip(cancel_list,iaccount_list):
            trade = pas_tradehty.cancel_format(df, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
    
    def process(str_basedate, iaccount):
        
        basedate = datetime.datetime.strptime(str_basedate, '%Y%m%d')
        basedate_3days = basedate + datetime.timedelta(days=-3)
        str_basedate_3days = datetime.datetime.strftime(basedate_3days, '%Y%m%d')
        # 取得PAS合約拋轉總金額
        contract_PAS = ContractLib.get_contract_amount_pas(iaccount)
        contract_PAS_set = set(contract_PAS['合約號碼'])
        # PAS Outstanding Position
        outstanding_PAS = ContractLib.get_contract_total_sum(iaccount)
        outstanding_PAS = outstanding_PAS.rename(columns={'CommodityId':'合約號碼','Amount':'Outstanding'})
        
        # 1. 更新金額
        # 301F與PAS皆有，過濾掉未呈核的合約後，比對合約金額並更新
        # 會去判斷是否已經有AR立帳，沒有才會更新合約金額
        both = Contract._301F_set.intersection(contract_PAS_set)
        filter_1 = Contract._301F['合約號碼'].isin(both)
        filter_2 = Contract._301F['呈核狀態'].isin(['呈核中','呈核通過'])
        update = Contract._301F[filter_1 & filter_2].copy()
        update = pd.merge(update, contract_PAS, on=['合約號碼'], how='left')
        update = pd.merge(update, outstanding_PAS, on=['合約號碼'], how='left')
        
        # 計算金額差異，並依不同iaccount判斷Buy/Sell方向，最後金額差異取絕對值
        update['diff'] = update['合約總金額'] - update['PAS合約總金額']
        update = update[update['diff']!=0]
        update['bs'] = update['diff'].apply(lambda x:CTools.buy_sell_direction(x, iaccount))
        update['diff'] = abs(update['diff'])
        
        # 不調整合約金額
        # (a) 已全部結清的合約
        # (b) Outstanding position不為0
        # (c) 尚未取消的合約
        update['if_close'] = update['合約號碼'].apply(lambda x:CTools.position_close_filter(x))
        update['if_cancel'] = update['合約號碼'].apply(lambda x:CTools.contract_cancel_filter(x))
        filter_close = update['if_close']=='N'
        filter_zero = update['Outstanding']!=0
        filter_cancel = update['if_cancel'] == 'N'
        update = update[filter_close & filter_zero & filter_cancel]
        update['天期'] = GlobalVar.tenor
        if update.empty:
            update['匯率'] = None
        else:
            update['匯率'] = update.apply(lambda x:CTools.currency_rate_setter_update(x, str_basedate, iaccount), axis=1)
        update['basedate'] = basedate
        
        # 2. 合約新增
        # 僅301F有 -> 合約新增
        # 會去判斷是否已經有AR立帳，沒有才會計入部位
        # 建立日期於基準日(basedate)3日內的才算部位
        only_301F = Contract._301F_set.difference(contract_PAS_set)
        new = Contract._301F[Contract._301F['合約號碼'].isin(only_301F)].copy()
        new['天期'] = GlobalVar.tenor
        if new.empty:
            new['匯率'] = None
        else:
            new['匯率'] = new.apply(lambda x:CTools.currency_rate_setter_new(x, str_basedate, iaccount), axis=1)
        new['if_ar'] = new['合約號碼'].apply(lambda x:CTools.position_ar_filter(x))
        new['basedate'] = datetime.datetime.strptime(str_basedate, '%Y%m%d')
        filter_1 = new['if_ar']=='N'
        filter_2 = new['合約總金額']!=0
        filter_3 = ~new['合約總金額'].isnull()
        filter_4 = new['建立日期'] <= str_basedate
        filter_5 = new['建立日期'] >= str_basedate_3days
        new = new[filter_1 & filter_2 & filter_3 & filter_4 & filter_5]
        
        # 3. 合約刪除
        # (a) 僅PAS有
        # (b) 依CTools.contract_cancel_filter的篩選邏輯
        only_PAS = contract_PAS_set.difference(Contract._301F_set)
        contract_cancel_set = set([c for c in contract_PAS_set if CTools.contract_cancel_filter(c)=='Y'])
        cancel_set = only_PAS.union(contract_cancel_set)
        cancel = contract_PAS[contract_PAS['合約號碼'].isin(cancel_set)].copy()
        cancel = cancel[cancel['PAS合約總金額']!=0]
        cancel['幣別'] = cancel['合約號碼'].apply(lambda x:ContractLib.get_contract_currency_pas(x))
        cancel['產品類別'] = cancel['合約號碼'].apply(lambda x:ContractLib.get_contract_type_pas(x))
        if cancel.empty:
            cancel['匯率'] = None
        else:
            cancel['匯率'] = cancel.apply(lambda x:CTools.currency_rate_setter_cancel(x, str_basedate), axis=1)
        cancel['basedate'] = basedate
        cancel = cancel.rename(columns={'PAS合約總金額':'結清金額'})
        
        # 判斷Outstanding不為0，才取消
        cancel = pd.merge(cancel, outstanding_PAS, on=['合約號碼'], how='left')
        cancel = cancel[cancel['Outstanding']!=0]
        
        return new, update, cancel
        
    def push_msg():
        gp = Contract.new_s1.groupby(by=['幣別','產品類別']).sum()['合約總金額'].to_frame().reset_index()
        msg = ''
        if not gp.empty:
            msg = '合約成立：\n'
            for index, row in gp.iterrows():
                msg += row['幣別'] + '\t'
                msg += row['產品類別'] + '\t' 
                msg += '{:,.2f}'.format(row['合約總金額']) + '\n'
        
        gp = Contract.update_s1.groupby(by=['幣別','產品類別','bs']).sum()['diff'].to_frame().reset_index()
        if not gp.empty:
            msg += '合約金額調整：\n'
            for index, row in gp.iterrows():
                msg += row['幣別'] + '\t'
                msg += row['產品類別'] + '\t' 
                msg += row['bs'] + '\t' 
                msg += '{:,.2f}'.format(row['diff']) + '\n'
                
        gp = Contract.cancel_s1.groupby(by=['幣別','產品類別']).sum()['結清金額'].to_frame().reset_index()
        if not gp.empty:
            msg += '合約取消：\n'
            for index, row in gp.iterrows():
                msg += row['幣別'] + '\t'
                msg += row['產品類別'] + '\t' 
                msg += '{:,.2f}'.format(row['結清金額']) + '\n'
        
        msg += '\n'
        return msg
        
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Contract.new_s1, 'Contract_s1')
        if INTERNAL_SWITCH:
            save_obj.save(Contract.new_s2, 'Contract_s2')
            save_obj.save(Contract.new_z4, 'Contract_z4')
            
        save_obj.save(Contract.update_s1, 'Update_s1')
        save_obj.save(Contract.update_s2, 'Update_s2')
        save_obj.save(Contract.update_z4, 'Update_z4')
        
        save_obj.save(Contract.cancel_s1, 'Cancel_s1')
        save_obj.save(Contract.cancel_s2, 'Cancel_s2')
        save_obj.save(Contract.cancel_z4, 'Cancel_z4')

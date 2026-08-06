import pandas as pd
import contract
from getLib import ContractLib, FxLib
from config import GlobalVar
from insert_format import pas_tradehty
import utils
import datetime

def process(str_basedate):
    # 取得合約資訊
    contract_df = contract.process('')
    contract_set = set(contract_df['合約號碼'])
    
    # 取得PAS中合約成立的總金額(計入調整後的金額)
    pas_amount = ContractLib.get_contract_amount_pas()
    pas_set = set(pas_amount['合約號碼'])
    
    # 1. S1更新金額(contract_set/pas_set皆有)
    update_set = contract_set.intersection(pas_set)
    update_df = pd.merge(contract_df, pas_amount, on=['合約號碼'], how='left')
    update_df = update_df[update_df['合約號碼'].isin(update_set)]
    update_df['diff'] = update_df['合約總金額'] - update_df['PAS合約總金額']
    update_df = update_df[update_df['diff']!=0]
    update_df['bs'] = update_df['diff'].apply(lambda x: 'B' if x>0 else 'S')
    update_df['diff'] = abs(update_df['diff'])
    update_df['成交日期'] = datetime.datetime.strptime(str_basedate, '%Y%m%d')
    
    # 2. S1合約新增(contract_set有/pas_set沒有)
    new_set = contract_set.difference(pas_set)
    new_df = contract_df[contract_df['合約號碼'].isin(new_set)]
    new_df = new_df.dropna(subset=['匯率'])
    new_df = new_df[new_df['合約總金額']!=0]
    new_df['成交日期'] = datetime.datetime.strptime(str_basedate, '%Y%m%d')
    
    # 3. 合約取消刪除(contract_set沒有/pas_set有)
    cancel_set = pas_set.difference(contract_set)
    cancel_df = pas_amount[pas_amount['合約號碼'].isin(cancel_set)].copy()
    cancel_df = cancel_df[cancel_df['PAS合約總金額']!=0]
    cancel_df['幣別'] = cancel_df['合約號碼'].apply(lambda x:ContractLib.get_contract_currency_pas(x))
    cancel_df['匯率'] = cancel_df['幣別'].apply(lambda x:FxLib.get_fx_forward_by_tenor(str_basedate, x, GlobalVar.tenor))
    cancel_df['basedate'] = datetime.datetime.strptime(str_basedate, '%Y%m%d')
    cancel_df = cancel_df.rename(columns={'PAS合約總金額':'結清金額'})
    
    return update_df, new_df, cancel_df


class Update:
    
    def Init():
        # 分出更新金額/延遲入DB/取消刪除的合約
        Update.update_df, Update.new_df, Update.cancel_df = process(GlobalVar.str_basedate)
        
        # 取得各內部帳號(S1,S2,Z4)的合約清單
        Update.order_s1 = ContractLib.get_contract_id_by_account('S1')
        Update.order_s2 = ContractLib.get_contract_id_by_account('S2')
        Update.order_z4 = ContractLib.get_contract_id_by_account('Z4')
        
        # 依不同內部帳號的合約清單，對應出各內部帳號的結清明細
        Update.cancel_s1 = pd.merge(Update.order_s1, Update.cancel_df, how='inner', on=['合約號碼'])
        Update.cancel_s2 = pd.merge(Update.order_s2, Update.cancel_df, how='inner', on=['合約號碼'])
        Update.cancel_z4 = pd.merge(Update.order_z4, Update.cancel_df, how='inner', on=['合約號碼'])
        
    def commodity_insert():
        # 新合約需先寫入Commodity, CommodityGroup, CommodityGroupLink
        comdty = pas_tradehty.commodity_fornmat(Update.new_df)
        comdtyLink = pas_tradehty.commodityGroupLink_fornmat(Update.new_df)
        comdtyGroup = pas_tradehty.commodityGroup_fornmat(Update.new_df)
        store, errmsg = utils.insert_commodity(comdty)
        store, errmsg = utils.insert_commodity_group_link(comdtyLink)
        store, errmsg = utils.insert_commodity_group(comdtyGroup)
        
    def update_insert():
        
        for insert_type in ['S1']:
            # 寫入延遲寫入DB的新合約
            trade = pas_tradehty.contract_format(Update.new_df, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            # 更新已寫入的合約金額
            trade_update = pas_tradehty.update_format(Update.update_df)
            store, errmsg = utils.insert_tradehty(trade_update)
            
    def cancel_insert():
        
        for insert_type in ['S1']:
            trade = pas_tradehty.cancel_format(Update.cancel_s1, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
        for insert_type in ['S2']:
            trade = pas_tradehty.cancel_format(Update.cancel_s2, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
        for insert_type in ['Z4']:
            trade = pas_tradehty.cancel_format(Update.cancel_z4, insert_type)
            store, errmsg = utils.insert_tradehty(trade)
            
    def save_result():
        # 將相關資訊存成Excel檔
        save_obj = utils.DailyInsertReport(GlobalVar.basedate)
        save_obj.save(Update.update_df, 'Update')
        save_obj.save(Update.new_df, 'Delay_new_contract')
        save_obj.save(Update.cancel_df, 'Cancel')
        
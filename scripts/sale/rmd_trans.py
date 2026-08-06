import pandas as pd
from config import PAS_CONN, FX_TEST_CONN
from config import GlobalVar, INTERNAL_RMD_TABLE
from getLib import OrderLib, ContractLib
from dglib.log.nlogE import Elog
import utils

def contract_trans(str_basedate):
    sqlstr = f'''
    select 
    	CommodityId as contract_id
    	, TradeDate as trade_date
    	, BaseCurrencyId + 'TWD' as ccypair
    	, case when BS = 'B' then 'buy'
    		else 'sell' end as bs
    	, Qty as amount
    	, Price as rate
    	, 'O' as status
    from vwTrade
    where IAccountId = 'Z4'
    and TradeDate = '{str_basedate}'
    and Notes in ('合約成立','合約金額調整')
    '''
    df = pd.read_sql(sqlstr, PAS_CONN)
    store, errmsg = utils.insert_dataframe(df, 'ssbg_internal_sales', FX_TEST_CONN)
    
    return df

def contract_settle_trans(str_basedate):
    sqlstr = f'''
    select 
    	KeyId as key_id
    	,CommodityId as contract_id
    	, TradeDate as settle_date
    	, case when BS = 'B' then 'buy'
    		else 'sell' end as bs
    	, Qty as amount
    	, Price as settle_rate
    	, Notes as comment
    from vwTrade
    where IAccountId = 'Z4'
    and TradeDate = '{str_basedate}'
    and Notes in ('立帳結清','調整項')
    '''
    df = pd.read_sql(sqlstr, PAS_CONN)
    store, errmsg = utils.insert_dataframe(df, 'ssbg_internal_settle_sales', FX_TEST_CONN)
    
    return df

def contract_cancel_trans(str_basedate):
    sqlstr = f'''
    select 
    	KeyId as key_id
    	,CommodityId as contract_id
    	, TradeDate as settle_date
    	, case when BS = 'B' then 'buy'
    		else 'sell' end as bs
    	, Qty as amount
    	, Price as settle_rate
    	, Notes as comment
    from vwTrade
    where IAccountId = 'Z4'
    and TradeDate = '{str_basedate}'
    and Notes = '合約取消'
    '''
    df = pd.read_sql(sqlstr, PAS_CONN)
    store, errmsg = utils.insert_dataframe(df, 'ssbg_internal_settle_sales', FX_TEST_CONN)
    for index, row in df.iterrows():
        contract_id = row['contract_id']
        utils.update_rmd_contract_status(contract_id)
        

def contract_status_trans(str_basedate):
    order = OrderLib.get_order_csv(str_basedate)
    order = order.dropna(subset=['訂單日期'])
    order['項次'] = order['項次'].astype(int).astype(str)
    order['訂單日期'] = pd.to_datetime(order['訂單日期'].astype(int).astype(str))
    contract_status = ContractLib.get_contract_status()
    for index, row in contract_status.iterrows():
        contract_id = row['contract_id']
        status = row['status']
        order_subset = order[order['合約號碼']==contract_id]
        if order_subset['狀態'].eq('C').all() and not order_subset.empty and status=='O':
            utils.update_rmd_contract_status(contract_id)
            
            
def trans_exec():
    if INTERNAL_RMD_TABLE:
        Elog.info('RMD轉檔開啟')
        contract_trans(GlobalVar.str_basedate)
        contract_settle_trans(GlobalVar.str_basedate)
        contract_cancel_trans(GlobalVar.str_basedate)
        contract_status_trans(GlobalVar.str_basedate)
    else:
        Elog.info('RMD轉檔關閉')
    
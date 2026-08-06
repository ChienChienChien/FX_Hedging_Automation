# -*- coding: utf-8 -*-
"""
Created on Wed Nov 24 14:41:51 2021

從PAS轉內部交易資料至風管的資料庫

@author: ur08173
"""
from config import GlobalVar, RMD_TABLE_SWITCH
from config import RMD_TABLE, RMD_SETTLE_TABLE
from getLib import PASLib
from dglib.db.dbutils import DB
from dglib.log.nlogE import Elog
from tqdm import tqdm
import utils
import pyodbc
import datetime

def contract_trans(basedate):
    now = datetime.datetime.now()
    now_before_30m = now - datetime.timedelta(minutes=30)
    sqlstr = f'''
    select 
        CommodityId
        , TradeDate as trade_date
        , BaseCurrencyId + 'TWD' as ccypair
        , case when BS = 'B' then 'buy'
        	else 'sell' end as bs
        , Qty as amount
        , Price as rate
        , 'O' as status
    from vwTrade
    where IAccountId = 'Y4'
    and TradeDate = '{basedate.date()}'
    and Notes = '風管接BG之外匯部位-訂單成立'
    and MDate between '{format(now_before_30m, '%Y-%m-%d %H:%M:%S')}' and '{format(now, '%Y-%m-%d %H:%M:%S')}'
    '''
    df = DB.query(sqlstr, GlobalVar.PAS_connstr)
    if not df.empty:
        df[['order_no','order_item']] = df['CommodityId'].str.rsplit('-', n=1, expand=True)
        df = df[['order_no','order_item','trade_date','ccypair','bs','amount','rate','status']]
        store, errmsg = utils.insert_dataframe(df, RMD_TABLE, GlobalVar.dglib_DBConnStr_RMD)
    
    return df

def contract_settle_trans(basedate):
    now = datetime.datetime.now()
    now_before_30m = now - datetime.timedelta(minutes=30)
    sqlstr = f'''
    select 
        CommodityId
        , TradeDate as settle_date
        , case when BS = 'B' then 'buy'
        	else 'sell' end as bs
        , Qty as amount
        , Price as settle_rate
        , right(notes, len(notes)-CHARINDEX('-', notes)) as comment
    from vwTrade
    where IAccountId = 'Y4'
    and TradeDate = '{basedate.date()}'
    and Notes in ('風管接BG之外匯部位-立帳結清','風管接BG之外匯部位-調整項',
                  '風管接BG之外匯部位-調整項-沖轉','風管接BG之外匯部位-更新金額')
    and MDate between '{format(now_before_30m, '%Y-%m-%d %H:%M:%S')}' and '{format(now, '%Y-%m-%d %H:%M:%S')}'
    '''
    df = DB.query(sqlstr, GlobalVar.PAS_connstr)
    if not df.empty:
        df[['order_no','order_item']] = df['CommodityId'].str.rsplit('-', n=1, expand=True)
        df = df[['order_no','order_item','settle_date','bs','amount','settle_rate','comment']]
        store, errmsg = utils.insert_dataframe(df, RMD_SETTLE_TABLE, GlobalVar.dglib_DBConnStr_RMD)
    
    return df

def contract_status_trans():
    df = PASLib.get_outstanging_amount_by_account('Y4')
    df[['order_no','order_item']] = df['CommodityId'].str.rsplit('-', n=1, expand=True)
    df['status'] = df['Qty'].apply(lambda x: 'O' if abs(round(x,6))!=0 else 'C')
    cursor = pyodbc.connect(GlobalVar.dglib_DBConnStr_RMD).cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        order_no = row['order_no']
        order_item = row['order_item']
        order_status = row['status']
        sqlstr = f'''
        update {RMD_TABLE}
        set status = '{order_status}'
        where order_no = '{order_no}'
        and order_item = '{order_item}'
        '''
        try:
            cursor.execute(sqlstr)
            cursor.commit()
        except Exception as err:
            cursor.rollback()
            err_str = str(err)
            Elog.info(err_str)
    cursor.close()

        
            
def trans_exec():
    if RMD_TABLE_SWITCH:
        Elog.info('RMD轉檔開啟')
        contract_trans(GlobalVar.basedate)
        contract_settle_trans(GlobalVar.basedate)
        contract_status_trans()
    else:
        Elog.info('RMD轉檔關閉')
    
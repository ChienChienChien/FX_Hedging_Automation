from config import ORDER_DIR, SETTLE_DIR, DAILY_INSERT_REPORT_DIR
from config import TRADE_COL_NAME
from config import PAS_CONN, FX_TEST_CONN
from config import COMMODITY_COL_NAME, COMMODITYGROUPLINK_COL_NAME, COMMODITYGROUP_COL_NAME
from config import TEAMS_URL
from dateutil.parser import parse
import math, os
import numpy as np
from tqdm import tqdm
from dglib.log.nlogE import Elog
from dglib.message.TeamsMsg import TeamsMsg
import datetime
import sys
        

class SaveReport:
    def __init__(self, df, basedate):
        if basedate == '':
            self.basedate_str = '重轉資料'
        else:
            self.basedate_str = basedate
        self.df = df
    
    def save_order_csv(self):
        if not os.path.isdir(ORDER_DIR):
            os.makedirs(ORDER_DIR)
        if not self.df.empty:
            fileName = 'order_' + self.basedate_str + '.csv'
            self.df.to_csv(os.path.join(ORDER_DIR,fileName))
            
    def save_settle_csv(self):
        if not os.path.isdir(SETTLE_DIR):
            os.makedirs(SETTLE_DIR)
        if not self.df.empty:
            fileName = 'settle_' + self.basedate_str + '.csv'
            self.df.to_csv(os.path.join(SETTLE_DIR,fileName))

class DailyInsertReport:
    def __init__(self, basedate):
        if basedate is None:
            self.basedate_str = '重轉資料'
        else:
            self.basedate_str = datetime.datetime.strftime(basedate, '%Y-%m-%d')
        self.dir = DAILY_INSERT_REPORT_DIR
        self.sub_dir = os.path.join(self.dir, self.basedate_str)
    
    def save(self, df, df_name):
        if not os.path.isdir(self.sub_dir):
            os.makedirs(self.sub_dir) 
        file_name = df_name + '.xlsx'
        save_path = os.path.join(self.sub_dir, file_name)
        if df.empty:
            file_name = df_name + '-empty' + '.xlsx'
            save_path = os.path.join(self.sub_dir, file_name)
            df.to_excel(save_path)
        else:
            file_name = df_name + '.xlsx'
            save_path = os.path.join(self.sub_dir, file_name)
            df.to_excel(save_path)
      
        
def check_db_empty(df):
    if df.empty:
        TeamsMsg.send('', TEAMS_URL, '<fx_sales>運作終止，無法從DB中獲取資料')
        sys.exit(0)
    else:
        return True

            
def float2date(x):
    if math.isnan(x):
        return np.nan
    else:
        return parse(str(int(x)))
    
    
def float2str(x):
    if math.isnan(x):
        return np.nan
    else:
        return str(int(x))


def insert_tradehty(trade):
    store, errmsg = [],[]
    sqlstr_col = ','.join(TRADE_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(TRADE_COL_NAME))
    cursor_pas = PAS_CONN.cursor()
    for index, row in tqdm(trade.iterrows(), total=trade.shape[0]):
        sqlstr = f'''insert into TradeHty({sqlstr_col}) 
                            values({sqlstr_val})'''
        tradeindex = row['KeyId']
        values = list(row)
        try:
            cursor_pas.execute(sqlstr, values)
            cursor_pas.commit()
        except Exception as error:
            cursor_pas.rollback()
            error_str = str(error)
            msg = tradeindex + error_str
            errmsg.append(msg)
            Elog.info(msg)
            TeamsMsg.send(msg, TEAMS_URL)
        else:
            store.append(row)      
    cursor_pas.close()

    return store, errmsg
        

def insert_dataframe(df, table_name, CONN):
    store, errmsg = [],[]
    sqlstr_col = ','.join(df.columns)
    sqlstr_val = ','.join(['?'] * len(df.columns))
    cursor = CONN.cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        sqlstr = f'''insert into {table_name}({sqlstr_col}) 
                     values({sqlstr_val})'''
        values = list(row)
        try:
            cursor.execute(sqlstr, values)
            cursor.commit()
        except Exception as error:
            cursor.rollback()
            error_str = str(error)
            Elog.info(error_str)
            TeamsMsg.send(error_str, TEAMS_URL)
            errmsg.append(error_str)
        else:
            store.append(row)       
    cursor.close()
    
    return store, errmsg


def insert_commodity(comdty):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITY_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITY_COL_NAME))
    cursor_pas = PAS_CONN.cursor()
    for index, row in tqdm(comdty.iterrows(), total=comdty.shape[0]):
        sqlstr = f'''insert into Commodity({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CommodityId']
        values = list(row)
        try:
            cursor_pas.execute(sqlstr, values)
            cursor_pas.commit()
        except Exception as error:
            cursor_pas.rollback()
            error_str = str(error)
            msg = index + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor_pas.close()

    return store, errmsg


def insert_commodity_group_link(df):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITYGROUPLINK_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITYGROUPLINK_COL_NAME))
    cursor_pas = PAS_CONN.cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        sqlstr = f'''insert into CommodityGroupLink({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CommodityId']
        values = list(row)
        try:
            cursor_pas.execute(sqlstr, values)
            cursor_pas.commit()
        except Exception as error:
            cursor_pas.rollback()
            error_str = str(error)
            msg = index + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor_pas.close()

    return store, errmsg


def insert_commodity_group(df):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITYGROUP_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITYGROUP_COL_NAME))
    cursor_pas = PAS_CONN.cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        sqlstr = f'''insert into CommodityGroup({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CGId']
        values = list(row)
        try:
            cursor_pas.execute(sqlstr, values)
            cursor_pas.commit()
        except Exception as error:
            cursor_pas.rollback()
            error_str = str(error)
            msg = index + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
            
    cursor_pas.close()

    return store, errmsg

def update_rmd_contract_status(contract_id):
    sqlstr = f'''
    update ssbg_internal_sales
    set status = 'C'
    where contract_id = '{contract_id}'
    '''
    cursor = FX_TEST_CONN.cursor()
    try:
        cursor.execute(sqlstr)
        cursor.commit()
    except Exception as err:
        cursor.rollback()
        err_str = str(err)
        Elog.error(err_str)
    cursor.close()
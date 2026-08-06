from config import TRADE_COL_NAME, COMMODITY_COL_NAME
from config import COMMODITYGROUPLINK_COL_NAME, COMMODITYGROUP_COL_NAME
from config import ALLOY_ORDER_DIR, ALLOY_SETTLE_DIR
from config import COIL_ORDER_DIR, COIL_SETTLE_DIR, TOTAL_SETTLE_DIR
from config import DAILY_INSERT_REPORT_DIR
from config import TEAMS_URL
import os
from tqdm import tqdm
import datetime
from dglib.log.nlogE import Elog
from dglib.message.TeamsMsg import TeamsMsg
from config import GlobalVar
import pyodbc
from getLib import AlloyLib, SettleLib
import calendar

class OPTools:
    
    settle = SettleLib.get_settle()
    material_price_dict = AlloyLib.get_alloy_price(GlobalVar.basedate)
    
    def alloy_position_filter(x):
        # 比對是否已經先立AP
        # 若已經先立AP則不計入部位
        order_no = x['採購單號']
        order_item = x['採購單項次']
        sub_settle = OPTools.settle.query('(採購單號==@order_no) & (採購單項次==@order_item)')
        sub_settle = sub_settle.dropna(subset=['發票過帳日期'])
        
        # 判斷已有入帳的AP，不計入部位
        if len(sub_settle)==0:
            # 若發行日期落在近14日內，則計入部位
            deal_date = x['發行日期']
            start_date = GlobalVar.basedate - datetime.timedelta(days=14)
            if deal_date >= start_date:
                return 'Y'
            else:
                return 'N'
        else:
            return 'N'

    def coil_position_filter(x):
        # 比對是否已經先立AP
        # 若已經先立AP則不計入部位
        order_no = x['採購單號']
        order_item = x['採購單項次']
        sub_settle = OPTools.settle.query('(採購單號==@order_no) & (採購單項次==@order_item)')
        sub_settle = sub_settle.dropna(subset=['發票過帳日期'])
        
        if len(sub_settle)==0:
            return 'Y'
        else:
            # 判斷已有入帳的AP，不計入部位
            return 'N'
            
    def comdty_group_filter(x):
        if '鎳' in x:
            return '含鎳原料'
        elif '鉻' in x:
            return '含鉻原料'
        elif '鉬' in x:
            return '含鉬原料'
        elif '不鏽鋼' in x:
            return '廢不鏽鋼原料'
        else:
            return '其他原料'
    
    def map_material_instrument(x):
        dic = AlloyLib.get_material_map()
        return dic.get(x)
    
    def map_material_price(x):

        return OPTools.material_price_dict.get(x)
        
    def pre_order_amount_cal(x):
        if x['合金'] == '鋼捲點價':
            amount = x['重量'] * (x['合約單價']-60)
        else:
            amount = x['重量'] * x['合約單價']
        return amount

    def order_amount_cal(x):
        if x['合金'] == '圓胚':
            amount = x['採購重量'] * x['合約單價']
        else:
            amount = x['採購重量'] * (x['合約單價']-60)
        return amount
    
def insert_tradehty(trade):
    store, errmsg = [],[]
    sqlstr_col = ','.join(TRADE_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(TRADE_COL_NAME))
    cursor = pyodbc.connect(GlobalVar.PAS_connstr).cursor()
    for index, row in tqdm(trade.iterrows(), total=trade.shape[0]):
        sqlstr_pasuat = f'''insert into TradeHty({sqlstr_col}) 
                            values({sqlstr_val})'''
        tradeindex = row['KeyId']
        values = list(row)
        try:
            cursor.execute(sqlstr_pasuat, values)
            cursor.commit()
        except Exception as error:
            cursor.rollback()
            error_str = str(error)
            msg = str(tradeindex) + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor.close()

    return store, errmsg


def insert_dataframe(df, table_name, conn_str):
    store, errmsg = [],[]
    sqlstr_col = ','.join(df.columns)
    sqlstr_val = ','.join(['?'] * len(df.columns))
    cursor = pyodbc.connect(conn_str).cursor()
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
            errmsg.append(error_str)
        else:
            store.append(row)       
    cursor.close()
    
    return store, errmsg


def insert_commodity(comdty):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITY_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITY_COL_NAME))
    cursor = pyodbc.connect(GlobalVar.PAS_connstr).cursor()
    for index, row in tqdm(comdty.iterrows(), total=comdty.shape[0]):
        sqlstr_pasuat = f'''insert into Commodity({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CommodityId']
        values = list(row)
        try:
            cursor.execute(sqlstr_pasuat, values)
            cursor.commit()
        except Exception as error:
            cursor.rollback()
            error_str = str(error)
            msg = str(index) + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor.close()

    return store, errmsg


def insert_commodityGtoupLink(df):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITYGROUPLINK_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITYGROUPLINK_COL_NAME))
    cursor = pyodbc.connect(GlobalVar.PAS_connstr).cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        sqlstr_pasuat = f'''insert into CommodityGroupLink({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CommodityId']
        values = list(row)
        try:
            cursor.execute(sqlstr_pasuat, values)
            cursor.commit()
        except Exception as error:
            cursor.rollback()
            error_str = str(error)
            msg = str(index) + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor.close()

    return store, errmsg


def insert_commodityGtoup(df):
    store, errmsg = [],[]
    sqlstr_col = ','.join(COMMODITYGROUP_COL_NAME)
    sqlstr_val = ','.join(['?'] * len(COMMODITYGROUP_COL_NAME))
    cursor = pyodbc.connect(GlobalVar.PAS_connstr).cursor()
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        sqlstr_pasuat = f'''insert into CommodityGroup({sqlstr_col}) 
                            values({sqlstr_val})'''
        index = row['CGId']
        values = list(row)
        try:
            cursor.execute(sqlstr_pasuat, values)
            cursor.commit()
        except Exception as error:
            cursor.rollback()
            error_str = str(error)
            msg = str(index) + error_str
            Elog.info(msg)
            errmsg.append(msg)
        else:
            store.append(row)
    cursor.close()

    return store, errmsg


class save_report:
    def __init__(self):
        today = datetime.datetime.today()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        basedate = today - datetime.timedelta(days=1)
        basedate_str = datetime.datetime.strftime(basedate, '%Y%m%d')
        self.basedate_str = basedate_str
    
    def alloy_order(self, df):
        if not os.path.isdir(ALLOY_ORDER_DIR):
            os.makedirs(ALLOY_ORDER_DIR)
        if not df.empty:
            file_name = 'Alloy Order-' + self.basedate_str + '.xlsx'
            file_path = os.path.join(ALLOY_ORDER_DIR, file_name)
            df.to_excel(file_path)

    def alloy_settle(self, df):
        if not os.path.isdir(ALLOY_SETTLE_DIR):
            os.makedirs(ALLOY_SETTLE_DIR)
        if not df.empty:
            file_name = 'Alloy Settle-' + self.basedate_str + '.xlsx'
            file_path = os.path.join(ALLOY_SETTLE_DIR, file_name)
            df.to_excel(file_path)
            
    def coil_order(self, df):
        if not os.path.isdir(COIL_ORDER_DIR):
            os.makedirs(COIL_ORDER_DIR)
        if not df.empty:
            file_name = 'Coil Order-' + self.basedate_str + '.xlsx'
            file_path = os.path.join(COIL_ORDER_DIR, file_name)
            df.to_excel(file_path)

    def coil_settle(self, df):
        if not os.path.isdir(COIL_SETTLE_DIR):
            os.makedirs(COIL_SETTLE_DIR)
        if not df.empty:
            file_name = 'Coil Settle-' + self.basedate_str + '.xlsx'
            file_path = os.path.join(COIL_SETTLE_DIR, file_name)
            df.to_excel(file_path)
            
    def total_settle(self, df):
        if not os.path.isdir(TOTAL_SETTLE_DIR):
            os.makedirs(TOTAL_SETTLE_DIR)
        if not df.empty:
            file_name = 'Total Settle-' + self.basedate_str + '.xlsx'
            file_path = os.path.join(TOTAL_SETTLE_DIR, file_name)
            df.to_excel(file_path)

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
    
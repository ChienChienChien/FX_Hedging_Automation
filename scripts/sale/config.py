import os
import configparser
import ast
import pyodbc
from dglib.config.globalvar import GlobalVar

GlobalVar.Init(GlobalVar.dglib_DBConnStr_QUANTDATA)

config = configparser.ConfigParser()
config.read('switch.txt', encoding="utf-8")

# 正式/測試區
Area = config.get('SWITCH','Area')

if Area == 'Formal':
    PAS_CONN = pyodbc.connect(GlobalVar.dglib_DBConnStr_PAS)
else:
    PAS_CONN = pyodbc.connect(GlobalVar.dglib_DBConnStr_PAS_TEST)
    
    
# 拋轉開關
INTERNAL_SWITCH = config.getboolean('SWITCH','INTERNAL_SWITCH')
INTERNAL_CURRENCY = ast.literal_eval(config.get('SWITCH','INTERNAL_CURRENCY'))
INTERNAL_TYPE = ast.literal_eval(config.get('SWITCH','INTERNAL_TYPE'))
INTERNAL_RMD_TABLE = config.getboolean('SWITCH','INTERNAL_RMD_TABLE')
INTERNAL_ALL = config.getboolean('SWITCH','INTERANL_ALL')

# BIDATA
BIDATA_CONN = pyodbc.connect(GlobalVar.dglib_DBConnStr_BIDATA)

# QUANTDATA測試區
QUANT_TEST_CONN = pyodbc.connect(GlobalVar.dglib_DBConnStr_QUANTDATA)

# RMD-FX測試區
FX_TEST_CONN = pyodbc.connect(GlobalVar.dglib_DBConnStr_RMD)



# 欄位
TRADE_COL_NAME = ['KeyId','TradeDate','CounterPartyId','TraderId',
                  'EAccountId','IAccountId','CombinationId','CommodityId',
                  'CommodityNm','TradeType','OrderType','BS','Qty',
                  'Price','DataSource','Notes','OrderNo','MUser','CUser']
ORDER_COL_NAME = ['CounterPartyId','TraderId','EAccountId','IAccountId',
                  'CombinationId','CommodityNm','TradeType','OrderType',
                  'BS','DataSource','Notes','MUser','CUser']
ORDER_COL_VALUE = ['','SSBG','0000000','S1','','','Normal','New','B',
                   'SapOrder','訂單成立','UR08173','UR08173']
SETTLE_COL_NAME = ['CounterPartyId','TraderId','EAccountId','IAccountId',
                   'CombinationId','CommodityNm','TradeType','OrderType','BS',
                   'DataSource','Notes','MUser','CUser']
SETTLE_COL_VALUE = ['','SSBG','0000000','S1','','','Normal','New','S','SapOrder',
                    '立帳結清','UR08173','UR08173']
ADJUST_COL_NAME = ['CounterPartyId','TraderId','EAccountId','IAccountId',
                   'CombinationId','CommodityNm','TradeType','OrderType',
                   'DataSource','Notes','MUser','CUser']
ADJUST_COL_VALUE = ['','SSBG','0000000','S1','','','Normal','New','SapOrder',
                    '調整項','UR08173','UR08173']


RMD_ORDER_DF_NAME = ['訂單','項次','定價日期','幣別','訂單預估金額',
                     '建立匯率']
RMD_ORDER_TABLE_NAME = ['order_no','order_item','trade_date','ccypair',
                        'amount','rate','bs']

RMD_SETTLE_DF_NAME = ['訂單','項次','發票日期','實際銷貨金額(外幣)','會計匯率']
RMD_SETTLE_TABLE_NAME = ['order_no','order_item','settle_date','amount',
                         'settle_rate','bs','comment']

RMD_ADJ_DF_NAME = ['訂單','項次','date','Amount','rate_adj']
RMD_ADJ_TABLE_NAME = ['order_no','order_item','settle_date','amount',
                      'settle_rate','bs','comment']

COMMODITY_COL_NAME = ['CommodityId', 'CommodityNm', 'QuoteCommodityId', 'CommodityKind',
                      'UnderlyingId', 'PricingUnderlyingId', 'CurrencyId', 'BaseCurrencyId',
                      'ProductKind', 'IssueDate', 'IssuePrice', 'Notes', 'DataSource', 'MUser', 'CUser']

COMMODITYGROUPLINK_COL_NAME = ['CGId', 'CGNm', 'CommodityId', 'MUser']

COMMODITYGROUP_COL_NAME = ['CGId', 'CGNm', 'Notes', 'Muser']



# 資料夾路徑
DAILY_INSERT_REPORT_DIR = os.path.join(os.getcwd(), 'Daily Insert Report')
ORDER_DIR = os.path.join(os.getcwd(),'dailyOrderData')
SETTLE_DIR = os.path.join(os.getcwd(),'dailySettlementData')


# Internal Deal Parameters Dictionary
ORIGINAL_ORDER = {'KeyId':'Original','TraderId':'SSBG',
                  'BS':'B','IAccountId':'S1'}
BG_INTERNAL_ORDER = {'KeyId':'BGInternal','TraderId':'SSBG',
                     'BS':'S','IAccountId':'S2'}
RMD_INTERNAL_ORDER = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                      'BS':'B','IAccountId':'Z4'}
INTERNAL_DEAL_DICT_ORDER = {'S1':ORIGINAL_ORDER,
                            'S2':BG_INTERNAL_ORDER,
                            'Z4':RMD_INTERNAL_ORDER}

ORIGINAL_SETTLE = {'KeyId':'Original','TraderId':'SSBG',
                   'BS':'S','IAccountId':'S1'}
BG_INTERNAL_SETTLE = {'KeyId':'BGInternal','TraderId':'SSBG',
                      'BS':'B','IAccountId':'S2'}
RMD_INTERNAL_SETTLE = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                       'BS':'S','IAccountId':'Z4'}
INTERNAL_DEAL_DICT_SETTLE = {'S1':ORIGINAL_SETTLE,
                             'S2':BG_INTERNAL_SETTLE,
                             'Z4':RMD_INTERNAL_SETTLE}

ORIGINAL_ADJ = {'KeyId':'Original','TraderId':'SSBG','BS':'B',
                'IAccountId':'S1'}
BG_INTERNAL_ADJ = {'KeyId':'BGInternal','TraderId':'SSBG',
                   'BS':'B','IAccountId':'S2'}
RMD_INTERNAL_ADJ = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                    'BS':'S','IAccountId':'Z4'}
INTERNAL_DEAL_DICT_ADJ = {'S1':ORIGINAL_ADJ,
                          'S2':BG_INTERNAL_ADJ,
                          'Z4':RMD_INTERNAL_ADJ}

INSERT_TYPES = ['S1','S2','Z4']

# Table名稱
SSBG_INTERNAL_TABLE = 'ssbg_internal'
SSBG_INTERNAL_SETTLE_TABLE = 'ssbg_internal_settle'
SSBG_INTERNAL_UAT_TABLE = 'ssbg_internal_uat'
SSBG_INTERNAL_SETTLE_UAT_TABLE = 'ssbg_internal_settle_uat'

# 結帳DataSource
DATASOURCE = 'FxSales'


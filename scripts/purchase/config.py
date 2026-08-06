import pyodbc
import os
import configparser
import datetime
from dglib.config.globalvar import GlobalVar

GlobalVar.Init(GlobalVar.dglib_DBConnStr_QUANTDATA)

# basedate設定
today = datetime.datetime.today()
today = today.replace(hour=0, minute=0, second=0, microsecond=0)
basedate = today - datetime.timedelta(days=1)
GlobalVar.basedate = basedate

config = configparser.ConfigParser()
config.read('switch.txt')

AREA = config.get('SWITCH','Area')

GlobalVar.BIDATA_connstr = GlobalVar.dglib_DBConnStr_BIDATA

if AREA == 'Formal':
    GlobalVar.PAS_connstr = GlobalVar.dglib_DBConnStr_PAS
    RMD_TABLE = 'ssbg_internal'
    RMD_SETTLE_TABLE  = 'ssbg_internal_settle'
else:
    GlobalVar.PAS_connstr = GlobalVar.dglib_DBConnStr_PAS_TEST
    RMD_TABLE = 'ssbg_test'
    RMD_SETTLE_TABLE = 'ssbg_settle_test'

"---拋轉開關---"
INTERNAL_SWITCH = config.getboolean('SWITCH','INTERNAL_SWITCH')
ALLOY_SWITCH = config.getboolean('SWITCH','ALLOY_SWITCH')
COIL_SWITCH = config.getboolean('SWITCH','COIL_SWITCH')
RMD_TABLE_SWITCH = config.getboolean('SWITCH','RMD_TABLE_SWITCH')


"---欄位---"
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

RMD_ORDER_DF_NAME = ['採購單號','採購單項次','成交日期','幣別','預估採購金額',
                     '匯率offer']
RMD_ORDER_TABLE_NAME = ['order_no','order_item','trade_date','ccypair',
                        'amount','rate','bs']

RMD_SETTLE_DF_NAME = ['採購單號','採購單項次','發票過帳日期','發票金額','會計匯率']
RMD_SETTLE_TABLE_NAME = ['order_no','order_item','settle_date','amount',
                         'settle_rate','bs','comment']

RMD_ADJ_DF_NAME = ['order_no','order_item','date','diff','rate_adj']
RMD_ADJ_TABLE_NAME = ['order_no','order_item','settle_date','amount',
                      'settle_rate','bs','comment']

UNSPLIT_ADJ_ORDER = ['採購單號','採購單項次','成交日期','鋼種','預估採購金額',
                     '匯率offer','幣別']
UNSPLIT_ADJ_SETTLE = ['採購單號','採購單項次','發票過帳日期','發票金額',
                      '會計匯率','發票文件號碼','發票文件項次','CommodityId']

COMMODITY_COL_NAME = ['CommodityId','CommodityNm','QuoteCommodityId','CommodityKind',
                      'UnderlyingId','PricingUnderlyingId','CurrencyId',
                      'BaseCurrencyId','ProductKind','IssueDate','IssuePrice','Notes',
                      'DataSource','MUser','CUser']

COMMODITYGROUPLINK_COL_NAME = ['CGId', 'CGNm', 'CommodityId', 'MUser']

COMMODITYGROUP_COL_NAME = ['CGId', 'CGNm', 'Notes', 'Muser']

"---資料夾路徑---"
SPECIAL_CASE_DIR = os.path.join(os.getcwd(), 'coil special case record')
ALLOY_ORDER_DIR = os.path.join(os.getcwd(), 'Daily Report', 'Alloy Order')
ALLOY_SETTLE_DIR = os.path.join(os.getcwd(), 'Daily Report', 'Alloy Settle')
COIL_ORDER_DIR = os.path.join(os.getcwd(), 'Daily Report', 'Coil Order')
COIL_SETTLE_DIR = os.path.join(os.getcwd(), 'Daily Report', 'Coil Settle')
TOTAL_SETTLE_DIR = os.path.join(os.getcwd(), 'Daily Report', 'Total Settle')
DAILY_INSERT_REPORT_DIR = os.path.join(os.getcwd(), 'Daily Insert Report')


"---Internal Deal Parameters Dictionary---"
ORIGINAL_ORDER = {'KeyId':'Original','TraderId':'SSBG',
                  'Notes':'訂單成立','BS':'S','IAccountId':'P1'}
BG_INTERNAL_ORDER = {'KeyId':'BGInternal','TraderId':'SSBG',
                     'Notes':'內部交易拋轉至風管-訂單成立','BS':'B',
                     'IAccountId':'P2'}
RMD_INTERNAL_ORDER = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                      'Notes':'風管接BG之外匯部位-訂單成立','BS':'S',
                      'IAccountId':'Y4'}
INTERNAL_DEAL_DICT_ORDER = {'P1':ORIGINAL_ORDER,
                            'P2':BG_INTERNAL_ORDER,
                            'Y4':RMD_INTERNAL_ORDER}

ORIGINAL_SETTLE = {'KeyId':'Original','TraderId':'SSBG',
                   'Notes':'立帳結清','BS':'B','IAccountId':'P1'}
BG_INTERNAL_SETTLE = {'KeyId':'BGInternal','TraderId':'SSBG',
                      'Notes':'內部交易拋轉至風管-立帳結清','BS':'S',
                      'IAccountId':'P2'}
RMD_INTERNAL_SETTLE = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                       'Notes':'風管接BG之外匯部位-立帳結清','BS':'B',
                       'IAccountId':'Y4'}
INTERNAL_DEAL_DICT_SETTLE = {'P1':ORIGINAL_SETTLE,
                             'P2':BG_INTERNAL_SETTLE,
                             'Y4':RMD_INTERNAL_SETTLE}

ORIGINAL_ADJ = {'KeyId':'Original','TraderId':'SSBG','BS':'S',
                'Notes':'調整項','IAccountId':'P1'}
BG_INTERNAL_ADJ = {'KeyId':'BGInternal','TraderId':'SSBG',
                   'Notes':'內部交易拋轉至風管-調整項','BS':'S',
                   'IAccountId':'P2'}
RMD_INTERNAL_ADJ = {'KeyId':'RMDInternal','TraderId':'RMD-WLC',
                    'Notes':'風管接BG之外匯部位-調整項','BS':'B',
                    'IAccountId':'Y4'}
INTERNAL_DEAL_DICT_ADJ = {'P1':ORIGINAL_ADJ,
                          'P2':BG_INTERNAL_ADJ,
                          'Y4':RMD_INTERNAL_ADJ}

INSERT_TYPES = ['P1','P2','Y4']

"---Table名稱---"
SSBG_INTERNAL_TABLE = 'ssbg_internal'
SSBG_INTERNAL_SETTLE_TABLE = 'ssbg_internal_settle'

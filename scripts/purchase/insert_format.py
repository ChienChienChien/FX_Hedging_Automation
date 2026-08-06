from config import INTERNAL_DEAL_DICT_ORDER
from config import INTERNAL_DEAL_DICT_SETTLE
from config import RMD_ORDER_TABLE_NAME, RMD_ORDER_DF_NAME
from config import RMD_SETTLE_DF_NAME, RMD_SETTLE_TABLE_NAME
from config import RMD_ADJ_DF_NAME, RMD_ADJ_TABLE_NAME
from config import INTERNAL_DEAL_DICT_ADJ
import pandas as pd
import datetime


class pas_tradehty:
    @staticmethod
    def order_format(order, insert_type):
        type_dict = INTERNAL_DEAL_DICT_ORDER[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        notes = type_dict['Notes']
        bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (order['採購單號'] + '-' + order['採購單項次'] + '-'
                             + order['成交日期'].dt.strftime('%Y%m%d') + '-' 
                             + keyid )
        trade['TradeDate'] = order['成交日期']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = order['採購單號'] + '-' + order['採購單項次']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = bs
        trade['Qty'] = round(order['預估採購金額'],6)
        trade['Price'] = order['匯率offer']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = notes
        trade['OrderNo'] = order['採購單號'] + '-' + order['採購單項次']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def cancel_format(df, insert_type):
        type_dict = INTERNAL_DEAL_DICT_SETTLE[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        notes = type_dict['Notes']
        bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (df['CommodityId'] + '-cancel' + '-' + df['basedate'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = df['basedate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = df['CommodityId']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = bs
        trade['Qty'] = abs(round(df['Qty'],6))
        trade['Price'] = df['匯率']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = notes
        trade['OrderNo'] = df['CommodityId']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def settle_format(settle, insert_type):
        type_dict = INTERNAL_DEAL_DICT_SETTLE[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        notes = type_dict['Notes']
        # bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (settle['採購單號'] + '-' + settle['採購單項次'] 
                            + '-' +settle['發票文件號碼'] + '-' + settle['發票文件項次']
                            + '-' + keyid)
        trade['TradeDate'] = settle['發票過帳日期']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = settle['CommodityId']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        if insert_type == 'P2':
            trade['BS'] = settle['發票金額'].apply(lambda x: 'S' if x>=0 else 'B')
        else:
            trade['BS'] = settle['發票金額'].apply(lambda x: 'B' if x>=0 else 'S')
        trade['Qty'] = abs(round(settle['發票金額'],6))
        trade['Price'] = settle['會計匯率']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = notes
        trade['OrderNo'] = settle['採購單號'] + '-' + settle['採購單項次']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def pre_order_settle_format(settle, insert_type):
        type_dict = INTERNAL_DEAL_DICT_SETTLE[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        notes_settle = type_dict['Notes']
        notes_update = notes_settle.replace('立帳結清','更新金額')
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (settle['採購單號'] + '-' + settle['採購單項次'] 
                            + '-' + settle['statement'] + '-' 
                            + settle['交易日期'].dt.strftime('%Y%m%d')
                            + '-' + keyid)
        trade['TradeDate'] = settle['交易日期']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = settle['採購單號'] + '-' + settle['採購單項次']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = settle['BS']
        trade['Qty'] = round(settle['差異金額'],6)
        trade['Price'] = settle['匯率offer']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = settle['statement'].apply(lambda x:notes_settle if x=='鋼捲點價結清' else notes_update)
        trade['OrderNo'] = settle['採購單號'] + '-' + settle['採購單項次']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    
    @staticmethod
    def adjustment_format(status, insert_type):
        type_dict = INTERNAL_DEAL_DICT_ADJ[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        notes = type_dict['Notes']
        # bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (status['CommodityId'] + '-adjust' + '-' +
                             status['date'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = status['date']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = status['CommodityId']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = status['Qty'].apply(lambda x: 'S' if x>=0 else 'B')
        trade['Qty'] = abs(round(status['Qty'],6))
        trade['Price'] = status['rate_adj']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = notes
        trade['OrderNo'] = status['CommodityId']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    
    @staticmethod
    def update_amount_format(update):
        type_dict = INTERNAL_DEAL_DICT_ORDER['P1']
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        # notes = type_dict['Notes']
        # bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (update['採購單號'] + '-' + update['採購單項次'] + '-update-'
                             + update['tradeDate'].dt.strftime('%Y%m%d') + '-' 
                             + keyid)
        trade['TradeDate'] = update['tradeDate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = update['採購單號'] + '-' + update['採購單項次']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = update['diff'].apply(lambda x: 'S' if x>=0 else 'B')
        trade['Qty'] = abs(round(update['diff'],6))
        trade['Price'] = update['匯率offer']
        trade['DataSource'] = 'SapOrder'
        trade['Notes'] = '訂單金額調整'
        trade['OrderNo'] = update['採購單號'] + '-' + update['採購單項次']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def commodity_fornmat(df):
        comdty = pd.DataFrame()
        comdty['CommodityId'] = df['採購單號'] + '-' + df['採購單項次']        
        comdty['CommodityNm'] = df['採購單號'] + '-' + df['採購單項次']
        comdty['QuoteCommodityId'] = df['幣別'] + '/NTD'
        comdty['CommodityKind'] = 'Business'
        comdty['UnderlyingId'] = 'FXPurchase-' + df['合金']
        comdty['PricingUnderlyingId'] = 'FXPurchase-' + df['合金']
        comdty['CurrencyId'] = 'NTD'
        comdty['BaseCurrencyId'] = df['幣別']
        comdty['ProductKind'] = df['幣別'] + '/NTD'
        comdty['IssueDate'] = df['發行日期']
        comdty['IssuePrice'] = df['匯率offer']
        comdty['Notes'] = '外幣採購單'
        comdty['DataSource'] = 'fx_purchase'
        comdty['MUser'] = 'UR08173'
        comdty['CUser'] = 'UR08173'
        
        return comdty
    
    @staticmethod
    def commodityGroupLink_fornmat(df):
        comdtylink = pd.DataFrame()
        comdtylink['CGId'] = df['CGId']    
        comdtylink['CGNm'] = df['CGId']
        comdtylink['CommodityId'] = df['採購單號'] + '-' + df['採購單項次']
        comdtylink['MUser'] = 'UR08173'
        
        return comdtylink
    
    @staticmethod
    def commodityGroup_fornmat(df):
        comdtyGroup = pd.DataFrame(set(df['採購單號']), columns=['CGId'])
        comdtyGroup['CGNm'] = comdtyGroup['CGId']
        comdtyGroup['Notes'] = '外幣採購單號'
        comdtyGroup['Muser'] = 'UR08173'
        
        return comdtyGroup
    
    @staticmethod
    def adjustment_reverse_format(df, iaccount):
        if iaccount == 'Y4':
            notes = '風管接BG之外匯部位-調整項-沖轉'
        elif iaccount == 'P2':
            notes = '內部交易拋轉至風管-調整項-沖轉'
        else:
            notes = '調整項-沖轉'
        df['KeyId'] = df['KeyId'] + '-' + df['TradeDate'].dt.strftime('%Y%m%d') + '-Reverse'
        df['BS'] = df['BS'].apply(lambda x:'B' if x=='S' else 'S')
        # df['Qty'] = df['Qty']
        df['Notes'] = notes
        
        return df
        

class rmd_table:
    @staticmethod
    def order_format(df):
        df = df[RMD_ORDER_DF_NAME].copy()
        df['幣別'] = df['幣別'] + 'TWD'
        df['bs'] = 'sell'
        df.columns = RMD_ORDER_TABLE_NAME
        return df

    @staticmethod
    def settle_format(df):
        df = df[RMD_SETTLE_DF_NAME].copy()
        df['bs'] = 'buy'
        df['comment'] = '立帳結清'
        df.columns = RMD_SETTLE_TABLE_NAME
        return df
    
    @staticmethod
    def pre_order_settle_format(df):
        df['差異金額'] = df.apply(lambda x:x['差異金額'] if x['BS']=='B' else -x['差異金額'], axis=1)
        df = df[['採購單號','採購單項次','交易日期','差異金額','匯率offer']].copy()
        df['bs'] = 'buy'
        df['comment'] = '鋼捲點價立帳結清'
        df.columns = RMD_SETTLE_TABLE_NAME
        return df 
    
    @staticmethod
    def adj_format(df):
        if not df.empty:
            df = df[RMD_ADJ_DF_NAME].copy()
            df['bs'] = 'buy'
            df['comment'] = '調整項'
            df.columns = RMD_ADJ_TABLE_NAME
        return df
    
    @staticmethod
    def adjReverse_format(adjReverse):
        df = pd.DataFrame(columns=RMD_ADJ_TABLE_NAME)
        if not adjReverse.empty:
            df[['order_no','order_item']] = adjReverse['CommodityId'].str.split('-',expand=True)            
            df['settle_date'] = adjReverse['TradeDate']
            df['amount'] = adjReverse['Qty']
            df['settle_rate'] = adjReverse['Price']
            df['bs'] = 'buy'
            df['comment'] = '調整項沖轉'
        return df

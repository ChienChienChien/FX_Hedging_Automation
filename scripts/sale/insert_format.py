from config import INTERNAL_DEAL_DICT_ORDER
from config import INTERNAL_DEAL_DICT_SETTLE
from config import INTERNAL_DEAL_DICT_ADJ
from config import DATASOURCE
import pandas as pd

class pas_tradehty:
    
    @staticmethod
    def contract_format(df, insert_type):
        type_dict = INTERNAL_DEAL_DICT_ORDER[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (df['合約號碼'] + '-' + df['basedate'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = df['basedate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = df['合約號碼']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = bs
        trade['Qty'] = round(df['合約總金額'],6)
        trade['Price'] = df['匯率']
        trade['DataSource'] = DATASOURCE
        trade['Notes'] = '合約成立'
        trade['OrderNo'] = df['合約號碼']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    
    @staticmethod
    def settle_format(settle, insert_type):
        type_dict = INTERNAL_DEAL_DICT_SETTLE[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (settle['合約號碼'] + '-' + settle['發票編號'] + '-' + settle['發票項次'] + '-' + keyid)
        trade['TradeDate'] = settle['發票日期']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = settle['合約號碼']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = bs
        trade['Qty'] = settle['結清金額']
        trade['Price'] = settle['會計匯率']
        trade['DataSource'] = DATASOURCE
        trade['Notes'] = '立帳結清'
        trade['OrderNo'] = settle['合約號碼']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    
    @staticmethod
    def adjustment_format(df, insert_type):
        type_dict = INTERNAL_DEAL_DICT_ADJ[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (df['contract_id'] + '-adjust' + '-' +
                             df['basedate'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = df['basedate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = df['contract_id']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = df['bs']
        trade['Qty'] = df['amount']
        trade['Price'] = df['rate'] 
        trade['DataSource'] = DATASOURCE
        trade['Notes'] = '調整項'
        trade['OrderNo'] =  df['contract_id']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    
    @staticmethod
    def update_format(check, insert_type):
        type_dict = INTERNAL_DEAL_DICT_ORDER[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (check['合約號碼'] + '-update' + '-' +
                             check['basedate'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = check['basedate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = check['合約號碼']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = check['bs']
        trade['Qty'] = check['diff']
        trade['Price'] = check['匯率'] 
        trade['DataSource'] = DATASOURCE
        trade['Notes'] = '合約金額調整'
        trade['OrderNo'] = check['合約號碼']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def cancel_format(df, insert_type):
        type_dict = INTERNAL_DEAL_DICT_SETTLE[insert_type]
        keyid = type_dict['KeyId']
        traderid = type_dict['TraderId']
        bs = type_dict['BS']
        iaccountid = type_dict['IAccountId']
        
        trade = pd.DataFrame(columns=['KeyId'])
        trade['KeyId'] = (df['合約號碼'] + '-cancel' + '-' +
                             df['basedate'].dt.strftime('%Y%m%d') + '-' + keyid)
        trade['TradeDate'] = df['basedate']
        trade['CounterPartyId'] = ''
        trade['TraderId'] = traderid
        trade['EAccountId'] = '0000000'
        trade['IAccountId'] = iaccountid
        trade['CombinationId'] = ''
        trade['CommodityId'] = df['合約號碼']
        trade['CommodityNm'] = ''
        trade['TradeType'] = 'Normal'
        trade['OrderType'] = 'New'
        trade['BS'] = bs
        trade['Qty'] = df['結清金額']
        trade['Price'] = df['匯率'] 
        trade['DataSource'] = DATASOURCE
        trade['Notes'] = '合約取消'
        trade['OrderNo'] =  df['合約號碼']
        trade['MUser'] = 'UR08173'
        trade['CUser'] = 'UR08173'
        return trade
    
    @staticmethod
    def commodity_fornmat(df):
        comdty = pd.DataFrame()
        comdty['CommodityId'] = df['合約號碼']     
        comdty['CommodityNm'] = df['合約號碼']
        comdty['QuoteCommodityId'] = df['幣別'] + '/NTD'
        comdty['CommodityKind'] = 'Business'
        comdty['UnderlyingId'] = 'FXSalesOrder-' + df['幣別'] + '/NTD'
        comdty['PricingUnderlyingId'] = 'FXSalesOrder-' + df['幣別'] + '/NTD'
        comdty['CurrencyId'] = 'NTD'
        comdty['BaseCurrencyId'] = df['幣別']
        comdty['ProductKind'] = df['幣別'] + '/NTD'
        comdty['IssueDate'] = df['建立日期']
        comdty['IssuePrice'] = df['匯率']
        comdty['Notes'] = '外幣銷售單'
        comdty['DataSource'] = DATASOURCE
        comdty['MUser'] = 'UR08173'
        comdty['CUser'] = 'UR08173'
        
        return comdty
    
    @staticmethod
    def commodityGroupLink_fornmat(df):
        comdtylink = pd.DataFrame()
        comdtylink['CGId'] = df['產品類別']    
        comdtylink['CGNm'] = df['產品類別']
        comdtylink['CommodityId'] = df['合約號碼']     
        comdtylink['MUser'] = 'UR08173'
        
        return comdtylink
    
    @staticmethod
    def commodityGroup_fornmat(df):
        comdtyGroup = pd.DataFrame(set(df['產品類別']), columns=['CGId'])
        comdtyGroup['CGNm'] = comdtyGroup['CGId']
        comdtyGroup['Notes'] = '外幣銷售產品分類'
        comdtyGroup['Muser'] = 'UR08173'
        
        return comdtyGroup
        
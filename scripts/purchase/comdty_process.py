import utils
from insert_format import pas_tradehty

def write_comdty(df, Group=True):
    
    # 寫入Commodity
    comdty = pas_tradehty.commodity_fornmat(df)
    store_order, errmsg_order = utils.insert_commodity(comdty)
    
    # 寫入CommodityGroupLink
    comdtylink = pas_tradehty.commodityGroupLink_fornmat(df)
    store_order, errmsg_order = utils.insert_commodityGtoupLink(comdtylink)
    
    if Group:        
        # 寫入CommodityGroup
        comdtyGroup = pas_tradehty.commodityGroup_fornmat(df)
        store_order, errmsg_order = utils.insert_commodityGtoup(comdtyGroup)
    
    
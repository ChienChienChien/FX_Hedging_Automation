import datetime
from dglib.message.TeamsMsg import TeamsMsg
from dglib.log.nlogE import Elog
from config import GlobalVar
from config import TEAMS_URL, MSG_HEADER
from contract import Contract
from settle import Settle
from adjust import Adj
import rmd_trans
import traceback
import pandas as pd

if __name__ == '__main__':
    
    pd.options.display.float_format = '{:,.2f}'.format
    today = datetime.datetime.today()
    basedate = today - datetime.timedelta(days=1)
    str_basedate = datetime.datetime.strftime(basedate, '%Y%m%d')
    GlobalVar.basedate = basedate.replace(hour=0, minute=0, second=0, microsecond=0)
    GlobalVar.str_basedate = str_basedate
    # 合約至立帳平均天期為60日(未來可能以精準交期做為拋轉天期的依據)
    GlobalVar.tenor = 60

    try:
        # 寫入合約
        Contract.Init()
        Contract.commodity_insert()
        Contract.contract_insert()
        Elog.info('合約寫入-ok')
        Contract.update_insert()
        Elog.info('合約金額更新-ok')
        Contract.cancel_insert()
        Elog.info('合約取消-ok')
        Contract.save_result()
        
        # 寫入立帳結清
        Settle.Init()
        Settle.settle_insert()
        Settle.save_result()
        Elog.info('結清寫入-ok')
        
        # 寫入合約立帳結清完成後的調整項
        Adj.Init()
        Adj.adj_insert()
        Adj.save_result()
        Elog.info('調整項寫入-ok')
        
        # 轉檔進RMD Table
        rmd_trans.trans_exec()
        Elog.info('轉檔進RMD-ok')
        
    except Exception as err:
        traceback_str = traceback.format_exc()
        err_str = str(err) + traceback_str
        msg = MSG_HEADER + '【fx_sale】\n轉檔失敗：' + err_str
        Elog.info(msg)
        TeamsMsg.send_by_request(err_str, TEAMS_URL)
    else:
        c_msg = Contract.push_msg()
        s_msg = Settle.push_msg()
        t_msg = MSG_HEADER + c_msg + s_msg
        t_msg = t_msg.replace('\n','<br>')
        t_msg = t_msg.replace('\t','&emsp;')
        TeamsMsg.send_by_request(t_msg, TEAMS_URL)
from coil_process import Coil
from alloy_process import Alloy
from settle_process  import Settle
from adjustment_process import Adj
from alloy_amount_update_process import Update
from dglib.message.TeamsMsg import TeamsMsg
from dglib.log.nlogE import Elog
from config import TEAMS_URL, MSG_HEADER
from config import GlobalVar
import rmd_trans 


if __name__ == '__main__':
    
    try:
        # 鋼捲
        Coil.Init()
        Coil.commodity_insert()
        Coil.coil_insert()
        Coil.pre_order_insert()
        Coil.coil_cancel_insert()
        Coil.save_result()
        Elog.info('鋼捲寫入-ok')
        
        # 合金
        Alloy.Init()
        Alloy.commodity_insert()
        Alloy.alloy_insert()
        Alloy.alloy_cancel_insert()
        Alloy.save_result()
        Elog.info('合金寫入-ok')
        
        # 結清
        Settle.Init()
        Settle.adj_reverse_insert()
        Settle.settle_insert()
        Settle.pre_order_settle()
        Settle.save_result()
        Elog.info('結清寫入-ok')
        
        # 調整項
        Adj.Init()
        Adj.adjust_insert()
        Adj.save_result()
        Elog.info('調整項寫入-ok')
        
        # 更新採購單金額
        Update.Init()
        Update.update_insert()
        Update.save_result()
        Elog.info('更新採購金額寫入-ok')
        
        # 更新RMD Table訂單狀態
        rmd_trans.trans_exec()
        Elog.info('RMD Table寫入-ok')
        
    except Exception as err:
        err_str = str(err)
        msg = MSG_HEADER + '【fx_purchase】轉檔失敗\n' + err_str
        Elog.info(msg)
        TeamsMsg.send_by_request(err_str, TEAMS_URL)
    else:
        c_msg = Coil.push_msg()
        a_msg = Alloy.push_msg()
        s_msg = Settle.push_msg()
        adj_msg = Adj.push_msg()
        t_msg = MSG_HEADER + c_msg + a_msg + s_msg + adj_msg
        t_msg = t_msg.replace('\n', '<br>')
        t_msg = t_msg.replace('\t', '&emsp;')
        TeamsMsg.send_by_request(t_msg, TEAMS_URL)
        
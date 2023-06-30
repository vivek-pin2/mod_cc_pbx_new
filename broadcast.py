import ESL
import requests as reqs
import json
import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling
import logging
from threading import Thread
import schedule
import time
import datetime
import uuid

with open('/var/www/html/fs_backend/config.json') as f:
    data = json.load(f)


# Connect to FreeSWITCH using ESL
def profile_info(query, qery_typ, arg):
    try:
        result = []
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            host=data['mysqlinfo']['host'],
            database=data['mysqlinfo']['database'],
            user=data['mysqlinfo']['user'],
            password=data['mysqlinfo']['password'],
            pool_name="pynative_pool",
            pool_size=5,
            pool_reset_session=True)
        mySql_Query = query
        connection_object = connection_pool.get_connection()
        if connection_object:
            cursor = connection_object.cursor()
            print(mySql_Query)
            cursor.execute(mySql_Query)
            if qery_typ == "insert":
                cursor.commit()
            elif qery_typ == "select":
                result = cursor.fetchall()
                print(result)
            elif qery_typ == "proc":
                print(qery_typ)
                cursor.callproc(query)
                for result in cursor.stored_results():
                    result = result.fetchall()
            # connection.commit()
            cursor.close()
    except mysql.connector.Error as error:
        print("Failed to   table in MySQL: {}".format(error))
    # logger.error(format(error))
    finally:
        if connection_object.is_connected():
            cursor.close()
            # connection_object.close()
            print("MySQL connection is closed")
    return result


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbosep=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
            return self._return

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def outbound_call(num, cust_id):
    if num[0] != '+':
        num = '+' + num
    lctyp_qry = "select c.lc_type from pbx_feature a,map_customer_package b,pbx_call_plan c,pbx_call_plan_rates d," \
                "gateway e,package f where b.customer_id=" + '"' + str(
        cust_id) + '"' + " and " + '"' + str(
        num) + '"' "like concat(d.dial_prefix,'%') and a.status='1' and b.status='1' and c.status='1' and " \
               "d.status='1' and e.status='1' and d.call_plan_id = a.call_plan_id and  f.id = b.package_id and a.id = " \
               "f.feature_id and f.product_id=1 and b.product_id=1 and e.id=d.gateway_id and c.id=a.call_plan_id and " \
               "b.start_date <= CURDATE() and b.end_date>= CURDATE() limit 1 "
    lc_typ = profile_info(lctyp_qry, "select", None)
    len(lc_typ) != 0
    if len(lc_typ) != 0:
        if lc_typ[0][0] == "1":
            gtwy_qry = "select e.id,d.call_plan_id,d.dial_prefix,d.buying_rate,d.selling_rate,d.selling_min_duration," \
                       "d.selling_billing_block ,e.codec ,e.callerID from pbx_feature a,map_customer_package b," \
                       "pbx_call_plan c,pbx_call_plan_rates d,gateway e,package f where b.customer_id=" + str(
                cust_id) + " and '" + str(
                num) + "' like concat(d.dial_prefix,'%') and a.status='1' and b.status='1' and c.status='1' and " \
                       "d.status='1' and e.status='1' and d.call_plan_id = a.call_plan_id and f.id = b.package_id and " \
                       "a.id = f.feature_id and f.product_id=1 and b.product_id=1 and e.id=d.gateway_id and " \
                       "c.id=a.call_plan_id and b.start_date <= CURDATE() and  b.end_date>= CURDATE()  group by (" \
                       "d.buying_rate) asc limit 1 "
        else:
            gtwy_qry = "select e.id,d.call_plan_id,d.dial_prefix,d.buying_rate,d.selling_rate,d.selling_min_duration," \
                       "d.selling_billing_block ,e.codec, e.callerID from pbx_feature a,map_customer_package b," \
                       "pbx_call_plan c,pbx_call_plan_rates d,gateway e,package f where b.customer_id=" + str(
                cust_id) + " and '" + str(
                num) + "' like concat(d.dial_prefix,'%') and a.status='1' and b.status='1' and c.status='1' and " \
                       "d.status='1' and e.status='1' and d.call_plan_id = a.call_plan_id and f.id = b.package_id and " \
                       "a.id = f.feature_id and f.product_id=1 and b.product_id=1 and e.id=d.gateway_id and " \
                       "c.id=a.call_plan_id and b.start_date <= CURDATE() and  b.end_date>= CURDATE()  group by (" \
                       "d.selling_rate) asc limit 1 "
        gtwy = profile_info(gtwy_qry, "select", None)
        print((gtwy[0][0]))
        return gtwy;
    else:
        return 0


def broadcast_query():
    bc_query = "SELECT bc.id,GROUP_CONCAT(cnt_map.phone_number1) as contact1,GROUP_CONCAT(cnt_map.phone_number2) as " \
               "contact2,GROUP_CONCAT(ext_map.ext_number)   as contact3,bc.scheduler,bc.schedular_start_date," \
               "bc.customer_id,bc.status,bc.is_extension,bc.is_pstn,pro.file_path, bc.caller_id," \
               "bc.caller_id_type FROM pbx_broadcast as bc LEFT JOIN " \
               "`pbx_prompts` as pro on (bc.welcome_prompt = pro.id) LEFT JOIN `pbx_broadcast_mapping` as bc_map    on " \
               "(bc.id =bc_map.bc_id) LEFT JOIN `pbx_contact_list` as cnt_map  on (bc_map.ref_id=cnt_map.id) LEFT JOIN " \
               "`extension_master` as  ext_map  on (bc_map.ref_id=ext_map.id) where ( bc_map.type='P' or " \
               "bc_map.type='E' )  and (MINUTE(bc.schedular_start_date)=MINUTE(CURRENT_TIMESTAMP)) and (HOUR(" \
               "bc.schedular_start_date )= HOUR(CURRENT_TIMESTAMP))and (DATE(bc.schedular_start_date )=DATE(" \
               "CURRENT_TIMESTAMP)) group by bc.id "
    bc_data = profile_info(bc_query, "select", None)
    print(len(bc_data))
    return bc_data;


def shedule_bc():
    fatch_data = broadcast_query()
    for i in range(len(fatch_data)):
        if fatch_data[i][3] is not None and fatch_data[i][4] == '2' and fatch_data[i][8] == '1':
            agent = fatch_data[i][3].split(",")
            print(len(agent))
            for j in range(len(agent)):
                print(agent[j])
                bc_sip = Thread(target=sip_orignate, args=("call_broadcast", fatch_data[i], agent[j]))
                bc_sip.start()
                # sip_orignate("call_broadcast", fatch_data[i], agent[j])
            # print(bc_sip.join())

        if fatch_data[i][1] is not None and fatch_data[i][4] == '2' and fatch_data[i][9] == '1':
            agent2 = fatch_data[i][1].split(",")
            for j in range(len(agent2)):
                gtwy = outbound_call(agent2[j], fatch_data[i][6])
                if gtwy == 0:
                    continue
                bc_outbound = Thread(target=outbound_orignate,
                                     args=("call_broadcast", fatch_data[i], agent2[j], gtwy[0]))
                bc_outbound.start()


'''def shedule_fedbck():
    query = "select fd.src,fd.customer_id,qu.feedback_ivr ,fd.status ,fd.id,ivr.is_selection_dtmf,GROUP_CONCAT(" \
            "DISTINCT(pro.file_path)) as welcme_pmt from pbx_feedback fd,pbx_queue qu ,pbx_ivr_master ivr left join  " \
            "pbx_prompts pro on (pro.id=ivr.welcome_prompt)   where fd.ref_id=qu.id and qu.feedback_ivr=ivr.id and " \
            "qu.feedback_call=1   and (MINUTE(fd.hangup_time)=MINUTE(CURRENT_TIMESTAMP)) and (HOUR(fd.hangup_time)= " \
            "HOUR(CURRENT_TIMESTAMP))and (DATE(fd.hangup_time)=DATE(CURRENT_TIMESTAMP)) "
    fedbck = profile_info(query, "select")
    print(fedbck)
    for i in range(len(fedbck)):
        if fedbck[i][0] is not None:
            print(fedbck[i][0], fedbck[i][1])
            gtwy = outbound_call(fedbck[i][0], fedbck[i][1])
            fedbck_strng = "originate {origination_caller_id_number=" + str(
                fedbck[i][0]) + ",sip_req_user=01171,call_type=call_feedback,application=outbound,fd_id=" + str(
                fedbck[i][2]) + ",ref_id=" + str(fedbck[i][2]) + ",cust_id=" + str(
                fedbck[i][1]) + ",gateway_group_id=" + str(gtwy[0][0]) + ",call_plan_id=" + str(
                gtwy[0][1]) + ",dial_prefix=" + str(gtwy[0][2]) + ",buy_rate=" + str(gtwy[0][3]) + ",sell_rate=" + str(
                gtwy[0][4]) + ",selling_min_duration=" + str(gtwy[0][5]) + ",selling_billing_block=" + str(
                gtwy[0][6]) + "}sofia/gateway/gw_" + str(gtwy[0][0]) + "/" + str(fedbck[i][0]) + " "
            if fedbck[i][5] == '1':
                con.bgapi(fedbck_strng + str(fedbck[i][0]) + " XML cc_pbx ")
                print(fedbck_strng + " XML cc_pbx")
            else:
                con.bgapi(fedbck_strng + " &playback(/var/www/html/pbx/app" + str(fedbck[i][6]))
                print(fedbck_strng + "&playback(/var/www/html/pbx/app" + str(fedbck[i][6]))
    # updte_fedbck="update pbx_feedback set status='1' where id="+str(fedbck[i][4])
    # profile_info(query,"insert")
'''


def sip_orignate(call_type, fatch_data, agent):
    for call in range(3):
        job_uuid = str(uuid.uuid1())
        global origination_caller_id_number
        global caller_id_number
        global query_caller_id
        print(fatch_data[11])
        if fatch_data[11] != 0:
           print("dwdwd")
           if fatch_data[12] == "SIP":
                    query_caller_id = "SELECT ext_number from extension_master WHERE id="+str(fatch_data[11])+""
                    print(query_caller_id)
           if fatch_data[12] == "DID":
                    query_caller_id = "SELECT did FROM `did` where id="+str(fatch_data[11])+""
                    print(query_caller_id)
           caller_id_number = profile_info(query_caller_id, "select", None)
           origination_caller_id_number = caller_id_number[0][0]
        else:
           origination_caller_id_number = "9005551212"
           print(origination_caller_id_number)
        print("originate {origination_caller_id_number="+str(origination_caller_id_number)+",cust_id=" + str(
            fatch_data[6]) + ",call_type=" + call_type + ",ref_id=" + str(fatch_data[0]) +
              ",application=intercom,absolute_codec_string='PCMU,PCMA,OPUS,GSM,iLBC,G729'}sofia/internal/" + str(
            agent) + "@" + data['server']['public_ip'] + ":5060  &playback(/var/www/html/pbx/app" + str(
            fatch_data[10]) + ")")
        e = exec_fs_cmd("originate {origination_caller_id_number="+str(origination_caller_id_number)+",cust_id=" + str(
            fatch_data[6]) + ",call_type=" + call_type + ",ref_id=" + str(fatch_data[0]) +
                        ",application=intercom,absolute_codec_string='PCMU,PCMA,OPUS,GSM,iLBC,G729',"
                        "Job_uuid=" + job_uuid + "}sofia/internal/" + str(
            agent) + "@" + data['server']['public_ip'] + ":5060  &playback(/var/www/html/pbx/app" + str(
            fatch_data[10]) + ")", job_uuid)
        if e == "NORMAL_CLEARING" or e == "USER_BUSY":
            print("ccccccccccccccccccccccccccccccccccccccc")
            break
            return
        else:
            print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
            time.sleep(60)

    # print("call  retry")
    # sip_orignate(call_type, fatch_data, agent)


def outbound_orignate(call_type, fatch_data, agent, gtwy):
    for call in range(3):
        job_uuid = str(uuid.uuid1())
        print(str(fatch_data[10]))
        global origination_caller_id_number
        print(gtwy[7])
        print(gtwy[7])
        if gtwy[8] != '':
            origination_caller_id_number = gtwy[8]
        else:
            if fatch_data[11] != 0:
                if fatch_data[12] == "SIP":
                    query_caller_id = "SELECT ext_number from extension_master WHERE id=" + str(fatch_data[11]) + ""
                    print(query_caller_id)
                    caller_id_number = profile_info(query_caller_id, "select", None)
                if fatch_data[12] == "DID":
                    query_caller_id = "SELECT did FROM `did` where id=" + str(fatch_data[11]) + ""
                    print(query_caller_id)
                    caller_id_number = profile_info(query_caller_id, "select", None)
                origination_caller_id_number = caller_id_number[0][0]
            else:
                origination_caller_id_number = "9005551212"
        print("originate {origination_caller_id_number="+str(origination_caller_id_number)+",cust_id=" + str(
            fatch_data[6]) + ",call_type=" + call_type + ",ignore_early_media=true,ref_id=" + str(
            fatch_data[0]) + ",application=outbound,gateway_group_id=" + str(gtwy[0]) + ",call_plan_id=" + str(
            gtwy[1]) + ",dial_prefix=" + str(gtwy[2]) + ",buying_rate=" + str(gtwy[3]) + ",selling_rate=" + str(
            gtwy[4]) + ",selling_min_duration=" + str(gtwy[5]) + ",selling_billing_block=" + str(
            gtwy[6]) + ",absolute_codec_string='PCMA,PCMU,G722,G729,iLBC,GSM,OPUS,VP8',Job_uuid=" + job_uuid +
              "}sofia/gateway/gw_" + str(gtwy[0]) + "/" + str(
            agent) + " &playback(/var/www/html/pbx/app" + str(fatch_data[10]) + ")")
        e = exec_fs_cmd("originate {origination_caller_id_number="+str(origination_caller_id_number)+ ",cust_id=" + str(
            fatch_data[6]) + ",call_type=" + call_type + ",ignore_early_media=true,ref_id=" + str(
            fatch_data[0]) + ",application=outbound,gateway_group_id=" + str(gtwy[0]) + ",call_plan_id=" + str(
            gtwy[1]) + ",dial_prefix=" + str(gtwy[2]) + ",buying_rate=" + str(gtwy[3]) + ",selling_rate=" + str(
            gtwy[4]) + ",selling_min_duration=" + str(gtwy[5]) + ",selling_billing_block=" + str(
            gtwy[6]) + ",absolute_codec_string='PCMA,PCMU,G722,G729,iLBC,GSM,OPUS,VP8',Job_uuid=" + job_uuid
                        + ",originate_retries=0}sofia/gateway/gw_" + str(gtwy[0]) + "/" + str(
            agent) + " &playback(/var/www/html/pbx/app" + str(fatch_data[10]) + ")", job_uuid)
        '''exec_fs_cmd("originate {origination_caller_id_number=9005551212,cust_id=" + str(
            fatch_data[6]) + ",call_type=" + call_type + ",ignore_early_media=true,ref_id=" + str(
            fatch_data[0]) + ",application=outbound,gateway_group_id=" + str(gtwy[0]) + ",call_plan_id=" + str(
            gtwy[1]) + ",dial_prefix=" + str(gtwy[2]) + ",buying_rate=" + str(gtwy[3]) + ",selling_rate=" + str(
            gtwy[4]) + ",selling_min_duration=" + str(gtwy[5]) + ",selling_billing_block=" + str(
            gtwy[6]) + ",absolute_codec_string='" + gtwy[7] + "',Job_uuid=" + job_uuid + " }sofia/gateway/gw_" + str(
            gtwy[0]) + "/" + str(
            agent) + " &playback(/var/www/html/pbx/app" + str(fatch_data[10]) + ")", job_uuid)'''
        if e == "NORMAL_CLEARING" or e == "USER_BUSY" or e == "NO_USER_RESPONSE" or e == "NORMAL_UNSPECIFIED":
            print("ccccccccccccccccccccccccccccccccccccccc")
            break
            return
        else:
            print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
            time.sleep(60)


def exec_fs_cmd(cmd, job_uuid):
    con = ESL.ESLconnection('127.0.0.1', '8002', 'ClueCon')
    if con.connected():
        print("Connected to freeswitch")
        e = con.bgapi(cmd)
        e = con.events(str('json'), str('CHANNEL_HANGUP'))
        print('Channel-Call-UUID', job_uuid)
        e = con.filter('variable_job_uuid', job_uuid)
        e = con.recvEvent()
        print(str(e.getHeader("Hangup-Cause")))
        con.disconnect()
        return str(e.getHeader("Hangup-Cause"))


# con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
# if con.connected():
# e = con.bgapi("create_uuid").getBody()


def thread_broadcast():
    x = Thread(target=shedule_bc)
    x.start()
    time.sleep(58)


def thread_fedbck():
    fd = Thread(target=shedule_fedbck)
    fd.start()
    time.sleep(55)


while True:
    thread_broadcast()
    # thread_fedbck()

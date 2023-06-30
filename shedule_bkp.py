from lib2to3.pytree import type_repr
from operator import le, truediv
from sqlite3 import adapt
import uuid
import ESL
import requests as reqs
import json
import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling
import logging
import threading
import schedule
import time
import numpy as np

with open('/var/www/html/fs_backend/config.json') as f:
    data = json.load(f)



def profile_info(query, qery_typ, arg):
    try:
        result = []
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            host=data["mysqlinfo"]["host"],
            database=data["mysqlinfo"]["database"],
            user=data["mysqlinfo"]["user"],
            password=data["mysqlinfo"]["password"],
            pool_name="pynative_pool",
            pool_size=15,
            pool_reset_session=True
        )
        mySql_Query = query
        connection_object = connection_pool.get_connection()
        if connection_object:
            cursor = connection_object.cursor()
            #print(mySql_Query)
            
            if qery_typ == "insert":
                cursor.execute(mySql_Query)
                connection_object.commit()
            elif qery_typ == "select":
                cursor.execute(mySql_Query)
                result = cursor.fetchall()
                #print(result)
            elif qery_typ == "proc":
                #print(qery_typ)
                cursor.callproc(query, arg)
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
            #print("MySQL connection is closed")
    return result





def caller_header_manipulation(cli_num,gtwy_id):
   
    query=f"select cli.gw_id, IF(cli.strip_clr_id !='',cli.strip_clr_id,'na') strip ,IF(cli.prepend_clr_id !='',cli.prepend_clr_id,'na') \
        prepend, cli.clr_id_manipulation from pbx_caller_header_manipulation cli where cli.gw_id={gtwy_id}"
    
    gtwy_cli_query = profile_info(query, "select",None)   
    gtwy_cli = np.array(gtwy_cli_query)

    for index in range(0,len(gtwy_cli)) :
     if  gtwy_cli[index][3]=="2" and cli_num.startswith(str(gtwy_cli[index][1])):
         cli_num = cli_num[len(str(gtwy_cli[index][1])):len(cli_num)]
         cli_num = str(gtwy_cli[index][2]) + cli_num  
         break
     elif gtwy_cli[index][3]=="3" and gtwy_cli[index][1]=='na' : 
         cli_num = str(gtwy_cli[index][2]) + cli_num     
    return cli_num             



def outbound_call(num, cust_id):
    #print(f"\t num {num} ****cust_id {str(cust_id)} ")
    if num[0] != "+":
        num = "+" + num

    gtwy = profile_info( "switch_python_outbound_1", "proc", [str(cust_id),str(num)])
    #print(f"\n\n switch_python_outbound_1:{len(gtwy)} \n\n") 

    if len(gtwy) == 0:
     return 0
    else :  
     is_mnt_plan = None
     talking_mnt = None
     call_plan_rate_mnt_id = None

     #print(f"is_mnt enabled {gtwy[0][10]}  ") 
     if gtwy[0][10] == 1:
      gtwy = gtwy[0]
      #print(f"MINUTE DETAILS  is_group  {gtwy[19]}\n")

      if gtwy[19]== '0':
         billing_type =1
         is_mnt_plan = 1
         talking_mnt = gtwy[18]
         call_plan_rate_mnt_id =gtwy[12]
         #print(f"is_mnt_plan{is_mnt_plan}  talking_mnt {talking_mnt} call_plan_rate_mnt_id {call_plan_rate_mnt_id}")
      elif gtwy[19] =='1':
         billing_type =2
         talking_mnt = gtwy[21]
         call_plan_rate_mnt_id = gtwy[20]
         #print(f" grp mnt plan details is_mnt_plan {is_mnt_plan}  {is_mnt_plan}  billing_type {billing_type}   talking_mnt {talking_mnt}\n")
     
     elif gtwy[0][10] == '0':
       #print(f"DIALOUT DETAILS--->{gtwy[0]}")
       gtwy = gtwy[0]
       billing_type = 3
    
    return  gtwy,billing_type,is_mnt_plan,talking_mnt,call_plan_rate_mnt_id
    
   

           




def broadcast_query():
    bc_query = "SELECT bc.id,GROUP_CONCAT(cnt_map.phone_number1) as contact1,GROUP_CONCAT(cnt_map.phone_number2) as contact2,GROUP_CONCAT(ext_map.ext_number)   as contact3,"\
               "bc.scheduler,bc.schedular_start_date,bc.customer_id,bc.status,bc.is_extension,bc.is_pstn,pro.file_path ,IF (bc.is_pstn = '1',(SELECT concat('+',country.phonecode,did.did) FROM did "\
               "LEFT JOIN country on country.id = did.country_id WHERE did.id=bc.DID_caller_id) ,0) AS DID, IF (bc.is_extension = '1',(SELECT ext_number "\
               "FROM extension_master WHERE id=bc.SIP_caller_id) ,0) AS SIP FROM pbx_broadcast as bc " \
               "LEFT JOIN `pbx_prompts` as pro on (bc.welcome_prompt = pro.id) LEFT JOIN `pbx_broadcast_mapping`" \
               "as bc_map    on (bc.id =bc_map.bc_id) LEFT JOIN `pbx_contact_list` as cnt_map  on" \
               "(bc_map.ref_id=cnt_map.id) LEFT JOIN `extension_master` as  ext_map  on (bc_map.ref_id=ext_map.id)" \
               "where ( bc_map.type='P' or bc_map.type='E' )  and  bc.scheduler = '2' AND  date(bc.schedular_start_date) = CURRENT_DATE"\
               " and (HOUR(bc.schedular_start_date)= HOUR(CURRENT_TIMESTAMP)) and  (MINUTE(bc.schedular_start_date)= MINUTE(CURRENT_TIMESTAMP))"\
               "group by bc.id"
    bc_data = profile_info(bc_query, "select",None)
    print("broadcast call ",len(bc_data))
    return bc_data


def exec_fs_pstn(cmd,job_uuid):
    conn = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
    if conn.connected():
        print("Connected to freeswitch pstn")
        e = conn.events(str("json"), str("CHANNEL_HANGUP_COMPLETE"))
        e = conn.bgapi(cmd)
        e = conn.filter("variable_job_uuid", job_uuid)
        e = conn.recvEvent()
        #print(e.serialize())
        pstn_response =str(e.getHeader(str("variable_sip_invite_failure_phrase")))
        if pstn_response == "None":
            pstn_response = str(e.getHeader(str("variable_endpoint_disposition")))
        print(pstn_response)
        conn.disconnect()
    return [pstn_response,e.getHeader(str("variable_sip_to_user"))]


def shedule_bc():
    fatch_data = broadcast_query()
    
    for i in range(len(fatch_data)):
        if fatch_data[i][3] is not None and fatch_data[i][4] == '2' and fatch_data[i][8] == '1':
            agent = fatch_data[i][3].split(",")

            for j in range(len(agent)):
                cli=fatch_data[i][12]
                cust_id=str(fatch_data[i][6])
                ref_id=str(fatch_data[i][0])
                ply_bck=(fatch_data[i][10])

                sip_cli = f"originate {{origination_caller_id_number={cli},origination_caller_id_name={cli},cust_id={cust_id},call_type=call_broadcast,ref_id={ref_id},direction=inbound,application=intercom}}sofia/internal/{agent[j]}@{str(data['server']['opensip_ip'])}:{str(data['server']['opensip_port'])} &playback(/var/www/html/pbx/app{ply_bck})"
                print(f"calling sip..........  {agent[j]}")
                con.bgapi(sip_cli)

        if fatch_data[i][1] is not None and fatch_data[i][4] == '2' and fatch_data[i][9] == '1':
            agent2 = fatch_data[i][1].split(",")
            for j in range(len(agent2)):
                gtwy = outbound_call(agent2[j], fatch_data[i][6])
                if  gtwy != '0':
                   gtwy_limit = profile_info("switch_api_concurrent_call", "proc",(str(fatch_data[i][6]),str(gtwy[0][0])) )
                   gtwy_limit = int(gtwy_limit[0][0]) 

                   cli_no = gtwy[0][8]
                   if len(cli_no) == 0:
                    cli_no= fatch_data[0][11]
                   if len(cli_no) == 0:
                    master_did =  profile_info(f"SELECT did FROM `did` WHERE customer_id = {str(fatch_data[i][6])} and  activated ='1'  and master_did = '1'  ORDER by did DESC LIMIT 1", "select",None)
                    cli_no= master_did[0][0]
                   
                   origination_caller_id_number = caller_header_manipulation(cli_no,gtwy[0][0])
     
                   total_balance=0
                   credit_blance = 0
                   is_group_mnt_plan= None
                   call_plan_rate_group_mnt_id = None
     
                   if  gtwy[2] is None and gtwy[3] is not None:
                       is_group_mnt_plan = 1
                       call_plan_rate_group_mnt_id = str(gtwy[4])
                   elif gtwy[0][10] =='0':
         
                    total_balance = gtwy[0][19]
                    credit_blance = gtwy[0][18]    
 
                   job_uuid = str(uuid.uuid1()) 
                   print("gtwy_limit %s total pstn...%s "%(gtwy_limit,len(agent2)))

                   if gtwy_limit >0:
                     cmd = (f"originate {{ignore_early_media=true,originate_timeout=10,origination_caller_id_number={origination_caller_id_number},origination_caller_id_name={origination_caller_id_number},originate_timeout=60,"
                     f"cust_id={str(fatch_data[i][6])},call_type=call_broadcast,ref_id={str(fatch_data[i][0])},application=outbound,gateway_group_id={str(gtwy[0][0])},call_plan_id={str(gtwy[0][1])},"
                     f"dial_prefix={str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},selling_min_duration={str(gtwy[0][5])},selling_billing_block={str(gtwy[0][6])}"
                     f",billing_type={str(gtwy[1])},is_mnt_plan={str(gtwy[2])},talking_mnt={str(gtwy[3])},call_plan_rate_mnt_id={str(gtwy[4])},is_group_mnt_plan={str(is_group_mnt_plan)},"
                     f"call_plan_rate_group_mnt_id={str(call_plan_rate_group_mnt_id)},total_balance={str(total_balance)},credit_blance={str(credit_blance)},Job_uuid={job_uuid}}}"
                     f"sofia/gateway/gw_{str(gtwy[0][0])}/{str(agent2[j])} &playback(/var/www/html/pbx/app{str(fatch_data[i][10])})")
                     con.bgapi(cmd) 
                     print(f"calling ..........  {str(agent2[j])}")
                     time.sleep(5)
                   else:
                             
                     query = ("insert into pbx_realtime_cdr(uuid,src,dst,current_status,direct_gateway,call_type,terminatecause,customer_id,sip_current_application"
                     ')values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(job_uuid,origination_caller_id_number,str(agent2[j]),"CHANNEL_HANGUP",str(gtwy[0][0]),"outbound","1007",str(fatch_data[i][6]),"call_broadcast"))
                     profile_info(query, "insert", None)
                     #print(query)
                     print("Failed agent due to gtwy limit !!! ",str(agent2[j])) 
                      
    

def shedule_fedbck():

    query = "select fd.src,fd.customer_id,qu.feedback_ivr ,fd.status ,fd.id,ivr.is_selection_dtmf," \
            "(pro.file_path) as welcme_pmt ,fd.dst from pbx_feedback fd,pbx_queue qu " \
            ",pbx_ivr_master ivr left join  pbx_prompts pro on (pro.id=ivr.welcome_prompt)   " \
            "where fd.ref_id=qu.id and qu.feedback_ivr=ivr.id and qu.feedback_call=1   " \
            "and (MINUTE(fd.hangup_time)=MINUTE(CURRENT_TIMESTAMP)) and (HOUR(fd.hangup_time)=" \
            "HOUR(CURRENT_TIMESTAMP))and (DATE(fd.hangup_time)=DATE(CURRENT_TIMESTAMP)) and  fd.status!='1' "


    fedbck = profile_info(query, "select",None)

    print("feeeback call", len(fedbck))
    if  len(fedbck):
     
     for i in range(len(fedbck)):
      if fedbck[i][0] is not None:
           cust_id = fedbck[i][1]
           gtwy = outbound_call(fedbck[i][0], fedbck[i][1])
           if gtwy:
             
            dial_no = str(fedbck[i][0]) 

            if len(dial_no) == 10:
              dial_no =  str(gtwy[0][2])+str(fedbck[i][0])
            cli_no = str(fedbck[i][7])

            if cli_no is None:
                 master_did =  profile_info(f"SELECT did FROM `did` WHERE customer_id = {cust_id} and  activated ='1'  and master_did = '1'  ORDER by did DESC LIMIT 1", "select",None)
                 if master_did:
                  cli_no= master_did[0][0]
                  #print(f"master cli_no -->{cli_no}")
                
            origination_caller_id_number = caller_header_manipulation(cli_no,gtwy[0][0])

            total_balance=0
            credit_blance = 0
            is_group_mnt_plan= None
            call_plan_rate_group_mnt_id = None
            
            if  gtwy[2] is None and gtwy[3] is not None:
                is_group_mnt_plan = 1
                call_plan_rate_group_mnt_id = str(gtwy[4])
            elif gtwy[0][10] =='0':
    
             total_balance = gtwy[0][19]
             credit_blance = gtwy[0][18]    

             

            fedbck_strng = "originate {origination_caller_id_number=" + origination_caller_id_number + "," \
                "ignore_early_media=true,call_type=call_feedback,sip_h_X-switch='cc-ecpl',application=outbound,fd_id=" + \
                str(fedbck[i][2]) + ",ref_id=" + str(fedbck[i][2]) + ",cust_id=" + str(fedbck[i][1]) \
                + ",gateway_group_id=" + str(gtwy[0][0]) + ",call_plan_id=" + str(gtwy[0][1]) + ",dial_prefix=" + str(gtwy[0][2]) + ",buy_rate=" + str(gtwy[0][3]) + ",sell_rate=" + str(
                gtwy[0][4]) + ",selling_min_duration=" + str(gtwy[0][5]) + ",absolute_codec_string="+str(gtwy[0][7])+",selling_billing_block=" + str(gtwy[0][6]) + ",billing_type=" +str(
                gtwy[1])+",is_mnt_plan="+str(gtwy[2])+",talking_mnt="+str(gtwy[3])+",call_plan_rate_mnt_id="+str(gtwy[4])+",is_group_mnt_plan="+str(is_group_mnt_plan)+",call_plan_rate_group_mnt_id="+str(
                call_plan_rate_group_mnt_id)+",total_balance="+str(total_balance)+",credit_blance="+str(credit_blance)+",outbound_caller_from_user="+origination_caller_id_number\
                +",origination_caller_id_name="+origination_caller_id_number+"}sofia/gateway/gw_" +str(gtwy[0][0])+ "/" + dial_no + " "

            if fedbck[i][5] == '1':
              con.bgapi(fedbck_strng + str(fedbck[i][0]) + " XML cc_pbx ")
              print(f"{fedbck_strng}  {str(fedbck[i][0])}  XML cc_pbx")
            else:
                con.bgapi(fedbck_strng + " &playback(/var/www/html/pbx/app" + str(fedbck[i][6]))
                print(fedbck_strng + "&playback(/var/www/html/pbx/app" + str(fedbck[i][6]))
            updte_fedbck="update pbx_feedback set status='1' where id="+str(fedbck[i][4])
            profile_info(updte_fedbck,"insert",None) 

           else:
            print(f"No dial-out-rate")

             


def call_alarm():
    query = "SELECT DISTINCT(src),cust_id,id,time_start,CURRENT_TIME FROM `pbx_call_alarm` WHERE date_slot = CURRENT_DATE \
        AND (MINUTE(time_start)=MINUTE(CURRENT_TIMESTAMP)) and (HOUR(time_start)= HOUR(CURRENT_TIMESTAMP)) and status ='0'"
    call_alarm = profile_info(query, "select",None)

    print(f"call_alarm {len(call_alarm)}")

    if  len(call_alarm) :
     
     for i in range(len(call_alarm)):
      callee =call_alarm[i][0]
      cust_id =call_alarm[i][1]
      id =str(call_alarm[i][2])
      wake_up_cmd =f"originate {{origination_caller_id_number=wakeup_alarm,cust_id={cust_id},ignore_early_media=true,application=intercom,call_type=call_alarm,DIALSTATUS=SUCCESS}}sofia/internal/{callee}@{data['server']['opensip_ip']}:{data['server']['opensip_port']} &playback(/var/www/html/fs_backend/upload/def_prompts/wake_up_alarm.wav"
      #print("wake_up_cmd",wake_up_cmd,"\n")  
      con.bgapi(wake_up_cmd)
      query="update pbx_call_alarm set status='1' where id="+id
      profile_info(query,"insert",None) 
     
     



def thread_fedbck():
    fd = threading.Thread(target=shedule_fedbck)
    fd.start()
    fd.join()
        
def call_alarm_thead():
    cl_arm = threading.Thread(target=call_alarm)
    cl_arm.start()
    cl_arm.join()
        
def thread_broadcast():
    bd_cast = threading.Thread(target=shedule_bc)
    bd_cast.start()
    bd_cast.join()
    time.sleep(58)


con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
if con.connected():
    con.events(str("json"), str("SERVER_DISCONNECTED"))
    while True:
     if con.events(str("json"), str("SERVER_DISCONNECTED")):
         con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
         call_alarm_thead()
         thread_fedbck()
         thread_broadcast()
     else:
        call_alarm_thead()
        thread_fedbck()
        thread_broadcast()
     

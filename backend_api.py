import os
import time
import flask
from flask import request, jsonify, Response
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling
import logging
import json
import ESL
import numpy as np

# from manual_broadcast import *
from threading import Thread,RLock
import uuid
from datetime import datetime

now = datetime.now()
app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app, support_credentials=True)

with open("/var/www/html/fs_backend/config.json") as f:
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


def profile(query, qery_typ, arg):
    try:
        result = []
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            host=data["mysqlinfo"]["host"],
            database=data["mysqlinfo"]["database_bcknd"],
            user=data["mysqlinfo"]["user"],
            password=data["mysqlinfo"]["password"],
            pool_name="pynative_pool",
            pool_size=15,
            pool_reset_session=True,
        )
        mySql_Query = query
        connection_object = connection_pool.get_connection()
        if connection_object:
            cursor = connection_object.cursor()
            print(mySql_Query)
            cursor.execute(mySql_Query)
            if qery_typ == "insert":
                connection_object.commit()
            elif qery_typ == "select":
                result = cursor.fetchall()
                print(result)
            elif qery_typ == "proc":
                print(qery_typ)
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
    return result

""" 
def check_token_id(extn):
 

    query = (
        "SELECT count(*) FROM `extension_master` WHERE ext_number ='{0}'".format(
            str(extn)
            ))
    token_id = profile_info(query, "select", None)
   
    if token_id[0]:
        print ("token_id",token_id )
        return 1
        
    else:
        return 0 
 """


def check_cust_token_id(cust_id, token):
    try:
        query = (
            "SELECT count(*) FROM `customer`  where BINARY token="
            '"' + token + '"'
            " and id=" + cust_id + ""
        )
        token_id = profile_info(query, "select", None)
    except:
        return 0
    if token_id[0][0]:
        return 1
    else:
        return 0


def outbound_call(num, cust_id):
    if num[0] != "+":
        num = '+'+num

    print(f"\t num {num} ****cust_id {str(cust_id)} ")
  
    gtwy_query = profile_info( "switch_python_outbound_1", "proc", [str(cust_id),str(num)])
    gtwy = np.array(gtwy_query)

    if len(gtwy) == 0:
     print ("NO Dial-out ")
     return 0
      
    else :  
     is_mnt_plan = None
     talking_mnt = None
     call_plan_rate_mnt_id = None

     if gtwy[0][10] == '1':
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
         
    print("caller_header_manipulation",cli_num)     
    return cli_num             



def orignate_bridge(dest, src, gtwy, cust_id,application,json_req):
   
    print(f"gateway_details gwty_id {gtwy[0][0]} dest {str(dest)} src: {str(src)} cust_id {str(cust_id)}  \
      internal server: {data['server']['opensip_ip']} opensip_port {data['server']['opensip_port']}") 
    if application == "click2call":
     query=f"SELECT caller_id_header_value FROM `extension_master` WHERE  extension_master.ext_number = {str(src)}"
     extn_cli = profile_info(query, "select",None)

     if extn_cli[0][0] !='0':
        cli_num = extn_cli[0][0]
     else:    
      cli_num = str(gtwy[0][8])
      
    else:
      cli_num = str(gtwy[0][8])
      print(f"gtwy_cli -->{cli_num}")

    if len(cli_num) == 0 :
      master_did =  profile_info(f"SELECT did FROM `did` WHERE customer_id = {str(cust_id)} and  activated ='1' AND master_did ='1' ORDER by did DESC LIMIT 1", "select", None)
      cli_num= master_did[0][0]
      print(f"master cli -->{cli_num}")
    cli = caller_header_manipulation(cli_num,gtwy[0][0])

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

    #print("application ---",application) 
    
    if application == "patch_api":
         if dest[0] != "+":
          dest = '+'+dest
          
         orignate = (
        f"originate {{outbound_caller_from_user='{str(src)}',origination_caller_id_name='{str(src)}',origination_caller_id_number={cli},call_type=click2call,"
        f"application=outbound,ignore_early_media=consume,call_timeout=60,call_type=click2call,"
        f"cust_id={str(cust_id)},gateway_group_id={str(gtwy[0][0])},"
        f"call_plan_id={str(gtwy[0][1])},dial_prefix={str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},selling_min_duration={str(gtwy[0][5])},"
        f"selling_billing_block={str(gtwy[0][6])}}}sofia/gateway/gw_{str(gtwy[0][0])}/{str(src)} "
        f"&bridge({{outbound_caller_from_user='{str(dest)}',origination_caller_id_name='{str(dest)}',origination_caller_id_number={cli},"
        f"application=outbound,bridge_early_media=true,ignore_early_media=ring_ready,call_timeout=60,call_type=click2call,set_recording=1,"
        f",cust_id={str(cust_id)},gateway_group_id={str(gtwy[0][0])},"
        f"call_plan_id={str(gtwy[0][1])},dial_prefix={str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},selling_min_duration={str(gtwy[0][5])},"
        f"selling_billing_block={str(gtwy[0][6])},billing_type={str(gtwy[1])},is_mnt_plan={str(gtwy[2])},talking_mnt={str(gtwy[3])},call_plan_rate_mnt_id={str(gtwy[4])},"
        f"is_group_mnt_plan={is_group_mnt_plan},call_plan_rate_group_mnt_id={call_plan_rate_group_mnt_id},total_balance={total_balance},credit_blance={credit_blance},execute_on_originate='record_session::/var/www/html/fs_backend/upload/{str(cust_id)}"
        f"/recording/c2c_clr{str(src)}_cle{str(dest)}_{now.strftime('%Y-%m-%d-%H:%M:%S')}.wav'}}sofia/gateway/gw_{str(gtwy[0][0])}/{str(dest)})")
        
         #print(orignate)
         
    elif application == "plugin": 
     plugin_data = f"{str(json_req['plugin_data'])}"
     print(plugin_data)      
        
     orignate = f"originate {{plugin_data={plugin_data},ignore_early_media=consume,origination_caller_id_number={cli},call_type=call_plugin,sip_h_X-switch='cc-ecpl',application=outbound,"\
             f"cust_id={str(json_req['cust_id'])},gateway_group_id={str(gtwy[0][0])},call_plan_id={str(gtwy[0][1])},dial_prefix={ str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},"\
             f"selling_min_duration={str(gtwy[0][5])},absolute_codec_string={str(gtwy[0][7])},selling_billing_block={str(gtwy[0][6])},billing_type={str(gtwy[1])},is_mnt_plan={gtwy[2]},talking_mnt={gtwy[3]},call_plan_rate_mnt_id={str(gtwy[4])},"\
             f"is_group_mnt_plan={is_group_mnt_plan},call_plan_rate_group_mnt_id={call_plan_rate_group_mnt_id},total_balance={total_balance},credit_blance={credit_blance},outbound_caller_from_user={cli},"\
             f"origination_caller_id_name={cli}}}sofia/gateway/gw_{gtwy[0][0]}/{str(json_req['destination_number'])} {str(json_req['destination_number'])} XML cc_pbx" 
     
    else: 
     orignate = (
        f"originate {{origination_caller_id_number={str(dest)},sip_req_user={str(dest)},call_type=click2call,set_recording=1,"
        f"application=intercom,absolute_codec_string='PCMA,PCMU',call_type=click2call,"
        f"cust_id={str(cust_id)},gateway_group_id={str(gtwy[0][0])},"
        f"call_plan_id={str(gtwy[0][1])},dial_prefix={str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},selling_min_duration={str(gtwy[0][5])},"
        f"selling_billing_block={str(gtwy[0][6])}}}sofia/internal/{str(src)}@{data['server']['opensip_ip']}:{ data['server']['opensip_port']} "
        f"&bridge({{absolute_codec_string='PCMA,PCMU',application=outbound,call_type=click2call,set_recording=1,"
        f"outbound_caller_from_user='{str(dest)}',origination_caller_id_name='{str(dest)}',origination_caller_id_number='{cli}'"
        f",cust_id={str(cust_id)},gateway_group_id={str(gtwy[0][0])},"
        f"call_plan_id={str(gtwy[0][1])},dial_prefix={str(gtwy[0][2])},buy_rate={str(gtwy[0][3])},sell_rate={str(gtwy[0][4])},selling_min_duration={str(gtwy[0][5])},"
        f"selling_billing_block={str(gtwy[0][6])},billing_type={str(gtwy[1])},is_mnt_plan={str(gtwy[2])},talking_mnt={str(gtwy[3])},call_plan_rate_mnt_id={str(gtwy[4])},"
        f"is_group_mnt_plan={is_group_mnt_plan},call_plan_rate_group_mnt_id={call_plan_rate_group_mnt_id},total_balance={total_balance},credit_blance={credit_blance},execute_on_originate='record_session::/var/www/html/fs_backend/upload/{str(cust_id)}" 
        f"/recording/c2c_clr{str(src)}_cle{str(dest)}_{now.strftime('%Y-%m-%d-%H:%M:%S')}.wav'}}sofia/gateway/gw_{str(gtwy[0][0])}/{str(dest)})")

    #print(orignate)
    body = exec_fs(orignate)
    print("execute cmd", body)
    return body



def manual_broadcast(json_req):
    fatch_data = manual_broadcast_query(json_req)
    total_balance=0
    credit_blance = 0
    is_group_mnt_plan= None
    call_plan_rate_group_mnt_id = None
       
    for i in range(len(fatch_data)):
        if (
            fatch_data[i][3] is not None
            and fatch_data[i][4] == "1"
            and fatch_data[i][8] == "1"
        ):
            agent = fatch_data[i][3].split(",")
            #print(" sip_set %s"%(agent))
            for j in range(len(agent)):
                bc_sip = Thread(
                    target=sip_orignate,
                    args=("call_broadcast", fatch_data[i], agent[j]),
                )
                bc_sip.start()
            bc_sip.join()      
              
        
        else:
            print("No sip user for manual broadcast")   

        

        if (
            fatch_data[i][1] is not None
            and fatch_data[i][4] == "1"
            and fatch_data[i][9] == "1"
        ):  
            
            agent2 = fatch_data[i][1].split(",")
            pstn_set=set(agent2)
            print("pstn_set",pstn_set)
            members={}
            for num in pstn_set:
              #print(num,json_req['cust_id'])
              gtwy = outbound_call(num, json_req['cust_id'])
              #print(f" outbound manual broadcasting  ****************  billing_type {gtwy[1]}  plan type {gtwy[2]}  talking_mnt / dialout rates {gtwy[3]}  talking_blance {gtwy[0][19]}  gtwy  {gtwy}")
              if gtwy:
               if  gtwy[2] is None and gtwy[3] is not None:
                  is_group_mnt_plan = 1
                  call_plan_rate_group_mnt_id = str(gtwy[4])
               elif gtwy[i][10] =='0':
                  
                  total_balance = gtwy[i][19]
                  credit_blance = gtwy[i][18]
 
               cli_num = fatch_data[i][11]
               broadcast_cli = caller_header_manipulation(cli_num,gtwy[i][0])
 
              
               members[num] ={"gw_id" :gtwy[i][0],
                             "call_plan_id" :gtwy[i][1],
                             "dial_prefix" :gtwy[i][2],
                             "buy_rate" :gtwy[i][3],
                             "sell_rate" :gtwy[i][4],
                             "selling_min_duration" :gtwy[i][5],
                             "selling_billing_block" :gtwy[i][6],
                             "billing_type":gtwy[1],
                             "is_mnt_plan":gtwy[2],
                             "talking_mnt":gtwy[3],
                             "call_plan_rate_mnt_id":gtwy[4],
                             "is_group_mnt_plan":is_group_mnt_plan,
                             "call_plan_rate_group_mnt_id":call_plan_rate_group_mnt_id,
                             "credit_blance":credit_blance,
                             "total_balance":total_balance,
                             "cli": broadcast_cli,
                             "ref_id":fatch_data[i][0],
                             "cust_id":fatch_data[i][6],
                             "playback_file":str(fatch_data[i][10]),
                             "agent":num
                             }
                        
              else:
                  
                print("No dial out ",num) 
                 
            bc_outbound = Thread(
                    target=outbound_orignate,
                    args=("call_broadcast",members),
                   )
            bc_outbound.start()   
            bc_outbound.join()   
          
          
        else:
            print("No pstn user for manual broadcast")  

    
     


def manual_broadcast_query(json_req):
    bc_query = (

        "SELECT bc.id,GROUP_CONCAT(cnt_map.phone_number1) as contact1,GROUP_CONCAT(cnt_map.phone_number2) as contact2,GROUP_CONCAT(ext_map.ext_number)   as contact3,"
        "bc.scheduler,bc.schedular_start_date,bc.customer_id,bc.status,bc.is_extension,bc.is_pstn,pro.file_path ,IF (bc.is_pstn = '1',(SELECT concat('+',country.phonecode,did.did) FROM did "
        "LEFT JOIN country on country.id = did.country_id WHERE did.id=bc.DID_caller_id) ,0) AS DID, IF (bc.is_extension = '1',(SELECT ext_number "
        "FROM extension_master WHERE id=bc.SIP_caller_id) ,0) AS SIP FROM pbx_broadcast as bc LEFT JOIN `pbx_prompts` as pro on (bc.welcome_prompt = pro.id)"
        "LEFT JOIN `pbx_broadcast_mapping` as bc_map on (bc.id =bc_map.bc_id) LEFT JOIN `pbx_contact_list` as cnt_map on (bc_map.ref_id=cnt_map.id)"
        "LEFT JOIN `extension_master` as ext_map on (bc_map.ref_id=ext_map.id) where bc.id={0} and bc.customer_id={1}".format(
         json_req["broadcast_id"], json_req["cust_id"]))
        
    bc_data = profile_info(bc_query, "select", None)
    #print("bc_query-----",bc_query)
    return bc_data



def sip_orignate(call_type, fatch_data, agent):
  
  originate_no = fatch_data[12]
                       
  for i in range(3):
         job_uuid = str(uuid.uuid1())

         cmd =f"originate {{origination_caller_id_number={originate_no},origination_caller_id_name={str(originate_no)},cust_id={str(fatch_data[6])},call_type={call_type},ref_id={str(fatch_data[0])},"\
              f"Job_uuid={job_uuid},direction=inbound,application=intercom}}sofia/internal/{str(agent)}@{data['server']['opensip_ip']}:{data['server']['opensip_port']} &playback(/var/www/html/pbx/app{str(fatch_data[10])})"
         #print("cmd sip ",cmd )  
         e = exec_fs_cmd(cmd, job_uuid) 
        
         if e in ("NORMAL_CLEARING","USER_BUSY","UNALLOCATED_NUMBER"):
            break
         else:
            time.sleep(60)

            
    

def outbound_orignate(call_type, members):

 con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
 if con.connected():
   con.events(str("json"), str("CHANNEL_HANGUP_COMPLETE"))
 
  
 for agent in members.copy() :
        cust_id = str(members[agent]["cust_id"])
        gw_id = str(members[agent]["gw_id"])
        gtwy_limit = profile_info("switch_api_concurrent_call", "proc",(cust_id,gw_id))

        gtwy_limit = int(gtwy_limit[0][0])

        print("%s %s  %s \n %s gtwy_limit %s  gw_id %s"%(call_type,cust_id,agent,len(members),gtwy_limit,gw_id))  

        if gtwy_limit > 0:
         job_uuid = str(uuid.uuid1())
         cmd=f"originate {{ignore_early_media=consume,origination_caller_id_number={members[agent]['cli']}"\
            f",outbound_caller_from_user={members[agent]['cli']},origination_caller_id_name={agent},cust_id={members[agent]['cust_id']},"\
            f"call_type={call_type},ref_id={members[agent]['ref_id']},application=outbound,gateway_group_id={members[agent]['gw_id']},"\
            f"call_plan_id={members[agent]['call_plan_id']},dial_prefix={ members[agent]['dial_prefix']},buy_rate={members[agent]['buy_rate']},sell_rate={members[agent]['sell_rate']},selling_min_duration="\
            f"{members[agent]['selling_min_duration']},selling_billing_block={members[agent]['selling_billing_block']},billing_type={members[agent]['billing_type']},is_mnt_plan={members[agent]['is_mnt_plan']},talking_mnt={members[agent]['talking_mnt']},call_plan_rate_mnt_id={members[agent]['call_plan_rate_mnt_id']},"\
            f"is_group_mnt_plan={members[agent]['is_group_mnt_plan']},call_plan_rate_group_mnt_id={members[agent]['call_plan_rate_group_mnt_id']},total_balance={members[agent]['total_balance']},credit_blance={members[agent]['credit_blance']}"\
            f",job_uuid={job_uuid},ply_bck={members[agent]['playback_file']}}}sofia/gateway/gw_{members[agent]['gw_id']}/{str(agent)} &playback(/var/www/html/pbx/app{members[agent]['playback_file']})"  
         
         con.bgapi(cmd) 
         print(cmd)
         print(f"calling ..........  {agent}")
         time.sleep(5)
                             
        else :
                  
             query = ("insert into pbx_realtime_cdr(uuid,src,dst,current_status,direct_gateway,call_type,terminatecause,customer_id,sip_current_application"
             ')values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(str(uuid.uuid1()),members[agent]['cli'],agent,"CHANNEL_HANGUP",members[agent]['gw_id'],"outbound","1007",members[agent]['cust_id'],call_type))
             profile_info(query, "insert", None)
             print("Failed agent due to gtwy limit !!! ",agent) 
                    


def click2call(json_req):
   
    if json_req["application"] == "patch_api":
        json_req['extension'] = json_req['contact']
        json_req['destination_number'] = json_req['user_contact']

    if json_req["application"] == "plugin":
     json_req['extension'] = None    
    
    
    try:
        gtwy_limit = profile_info("verify_concurrent_call", "proc", [str(json_req["cust_id"])])
        print(f" gtwy_limit  verify_concurrent_call {gtwy_limit[0][0]} status {gtwy_limit[0][1]}")
        
        if gtwy_limit[0][0] == '1' or gtwy_limit[0][1] =='0':
         
         if    gtwy_limit[0][0] == '1':
            api_status,failed_reason =1007,'Concurrent Call Limit Exhausted'
         else:
           api_status,failed_reason=403,'Customer is inactive'
                 
         c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`, `application`,`customer_id`,`api_status`,`failed_reason`) VALUES \
         ('1', {str(json_req['extension'])}, {str(json_req['destination_number'])}, '{json_req['application']}',{ str(json_req['cust_id'])},\
         {api_status},'{failed_reason}')")
       
         profile_info(c2c_log, "insert", None)
         data = {"status_code" : 500 ,"message " : failed_reason ,"terminatecause": api_status}
         return  data

        if json_req["application"] == "click2call":
         check_package = (
            "SELECT f.click_to_call FROM pbx_feature f,package p,map_customer_package mcp WHERE "
            "f.id=p.feature_id and p.id=mcp.package_id and mcp.customer_id={0}".format(
                json_req["cust_id"]
            )
        )

         package = profile_info(check_package, "select", None)
         if package[0][0] == 0:
            c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`,`application`,`customer_id`,`api_status`,`failed_reason`) VALUES \
            ('1', '{str(json_req['extension'])}', '{str(json_req['destination_number'])}', '{json_req['application']}','{str(json_req['cust_id'])}',\
            500,'Package Not Found')")
            profile_info(c2c_log, "insert", None)
            data = {"status_code": 500, "message": "Package Not Found"}
            return data

      
         query = ("select outbound from extension_master where ext_number="+ str(json_req["extension"])+ " and status ='1'")
         check_outbound = profile_info(query, "select", None)
         check_outbound = np.array(check_outbound)

         if check_outbound[0] == 0 :
            c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`,`application`,`customer_id`,`api_status`,`failed_reason`) VALUES \
            ('1', '{str(json_req['extension'])}', '{str(json_req['destination_number'])}', '{json_req['application']}','{str(json_req['cust_id'])}',\
            500,'Outbound disable')")
            profile_info(c2c_log, "insert", None)
            data = {"status_code": 500, "message": "Outbound disable","terminatecause": 1007}
            return data


        gtwy = outbound_call(str(json_req["destination_number"]), json_req["cust_id"])
        
        if gtwy == 0:
            c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`,`application`,`customer_id`,`api_status`,`failed_reason`) VALUES \
            ('1', '{str(json_req['extension'])}', '{str(json_req['destination_number'])}', '{json_req['application']}','{str(json_req['cust_id'])}',\
            500,'Gateway failure(No Dialout Rule available for given destination')")
            profile_info(c2c_log, "insert", None)
            data = {"status_code": 500, "message": "Gateway failure (No Dialout Rule available for given destination)","terminatecause": 1012}
            return data
         
        else:
           
            disposition = orignate_bridge(json_req["destination_number"],json_req["extension"],gtwy,json_req["cust_id"],json_req["application"],json_req)
            c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`,`application`,`customer_id`,`api_status`,`failed_reason`,`disposition`) VALUES \
            ('1', '{str(json_req['extension'])}', {str(json_req['destination_number'])},'{json_req['application']}','{str(json_req['cust_id'])}',200,'success','{str(disposition)}')")
            profile_info(c2c_log, "insert", None)
            data = {"status_code": 200,"message": "success","uuid": disposition}
            return data
       

      

    except Exception as ex:
     print("Exception-------  ",ex)
     c2c_log = (f"INSERT INTO `api_logs` ( `product_id`, `src`, `dest`, `application`,`customer_id`,`api_status`,`failed_reason`) VALUES \
     ('1', '{str(json_req['extension'])}','{str(json_req['destination_number'])}', '{json_req['application']}','{str(json_req['cust_id'])}',500,'{str(ex)})")
     profile_info(c2c_log, "insert", None)
    
     data = {"status_code": 404, "message": str(ex)}
     return data



def exec_fs_cmd(cmd, job_uuid):
    con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
    if con.connected():
        e = con.bgapi(cmd)
        e = con.events(str("json"), str("CHANNEL_HANGUP"))
        e = con.filter("variable_job_uuid", job_uuid)
        e = con.recvEvent()
        con.disconnect()
        return str(e.getHeader(str("Hangup-Cause")))


def exec_fs(cmd):
    conn = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
    if conn.connected():
        e = conn.events(str("json"), str("CHANNEL_CREATE"))
        e = conn.bgapi(cmd)
        e = conn.recvEvent()
        #print("exec_fs_get_body", e.getHeader("Channel-Call-UUID"))
        conn.disconnect()
    return e.getHeader("Channel-Call-UUID")

def exec_fs_backend_event(cmd):
    con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
    if con.connected():
        e = con.events(str("json"), str("BACKGROUND_JOB"))
        e = con.bgapi(cmd)
        e = con.recvEvent()
        #print("Connected to freeswitch 3",e.getHeader(str("Job-Command")))
        con.disconnect()
    return e.getBody()




@app.route("/esl_api", methods=["POST", "GET", "OPTIONS"])
@cross_origin(origin="*")
# @cross_origin(supports_credentials=True)


def handle_request():
    if request.method == "POST":
        json_req = request.get_json()

        if json_req["application"] == "manual_broadcast":
            manual_broadcast(json_req)
            return Response(status=200)

        if json_req["application"] in ("click2call","patch_api","plugin"):
            res = click2call(json_req)
            return jsonify(res),res['status_code']
        

        if json_req["application"] == "acl":
            print("acl request received.")
            exec_fs("reloadacl")
            return Response(status=200)

        if json_req["application"] == "callcenter":
            #print(json_req["action"])
            if json_req["action"] == "add" or json_req["action"] == "delete":
                exec_fs_backend_event("reload mod_callcenter")# specific queue reload
                return Response(status=200)
            if json_req["action"] == "update":
                if json_req["que_typ"] == "tc":
                    dlt_agnt = ("DELETE FROM `agents` where name like 'tc_"+ json_req["id"]+ "_%'")
                    profile(dlt_agnt, "insert", None)

                    dlt_ter = ("DELETE FROM `tiers` where queue='tc_"+ json_req["id"]+ "@default' ")
                    profile(dlt_ter, "insert", None)
                    
                    """  print("callcenter_config queue reload  tc_"+ str(json_req["id"])+ "@default")"""
                    
                    exec_fs_backend_event("callcenter_config queue reload  tc_"+ str(json_req["id"])+ "@default")
                    return Response(status="200 tc up date successfully")

                if json_req["que_typ"] == "queue":
                    dlt_agnt = ("DELETE FROM `agents` where name like '"+ str(json_req["id"])+ "_%'")
                    profile(dlt_agnt, "insert", None)

                    dlt_ter = ("DELETE FROM `tiers` where queue='"+ str(json_req["id"])+ "@default' ")
                   
                    profile(dlt_ter, "insert", None)
                    """  print("callcenter_config queue reload  "+ str(json_req["id"])+ "@default") """

                    exec_fs_backend_event("callcenter_config queue reload  "+ str(json_req["id"])+ "@default")
                    return Response(status=200)

        if json_req["application"] == "gateway":
            if json_req["action"] == "add":

                 sql= "select id  from gateway  ORDER BY `gateway`.`id` DESC limit 1"
                 gateway_add = profile_info(sql, "select", None)
                 gateway_id = list(gateway_add[0])
                 print("------------------gateway_id------------",gateway_id[0])
                 #gateway= exec_fs_backend_event("sofia profile external startgw gw_{0}".format(gateway_id[0]))
                 gateway=  exec_fs_backend_event("sofia profile external rescan")
                 
                 data = {"status": 200, "data": "Success"}
                 return jsonify(data)

            if json_req["action"] == "update":
                 
                 gateway= exec_fs_backend_event("sofia profile external killgw gw_{0}".format(json_req["id"]))
                 gateway= exec_fs_backend_event("sofia profile external rescan")
             
                 data = {"status": 200, "data": "Updated gateway uuid {0}".format(gateway)}
                 return jsonify(data) 

            if json_req["action"] == "delete":
                
                 print("Deleted id of gateway",json_req["id"])
                 gateway= exec_fs_backend_event("sofia profile external killgw gw_{0}".format(json_req["id"]))
                 data = {"status": 200, "data": "Successfully deleted"}
                 return jsonify(data) 
                 
                     

        if json_req["application"] == "conference":
            exec_fs("reload mod_conference")
            return Response(status=200)

        if json_req["application"] == "gateway_status":
            data = exec_fs_backend_event("sofia profile external gwlist up")
            gtwy = {"active_gateway": data}
            return gtwy
        
        else:
            return Response(status=404)
    

#app.run(data["server"]["local_ip"], 1111)
app.run('127.0.0.1', 1111)


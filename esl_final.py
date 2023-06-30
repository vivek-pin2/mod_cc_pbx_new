import datetime,requests
from email.mime import application
from termios import CINTR
from subprocess import call
import numpy
import json
import time
import logging
import logging.config
import logging.handlers
import ESL
import threading
import asyncio
import uuid
import multiprocessing
import mysql.connector
import requests as reqs
from mysql.connector import Error, pooling
from mysql.connector.connection import MySQLConnection
import geoip2.database
import re



formatter = logging.Formatter('%(asctime)s %(levelname)s:%(lineno)s\t%(message)s')
handler = logging.handlers.TimedRotatingFileHandler('/var/log/fs_event_destroy.log',when="midnight",  backupCount=10)
handler.setFormatter(formatter)
logger = logging.getLogger() 
logger.addHandler(handler)
logger.setLevel(logging.INFO)
with open("/var/www/html/fs_backend/config.json") as f:
    data = json.load(f)



logging.basicConfig(
    filename="/root/esl.log", format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



def get_loc(ip):
 with geoip2.database.Reader('/var/www/html/fs_backend/GeoLite2-City.mmdb') as reader:
  if (ip != "192.168.100.4"):
   response = reader.city(f"{ip}")
   #print(f"ip address is : {ip} iso_code : {response.country.iso_code} latitude :{response.location.latitude} Longitude :{response.location.longitude} postal code :{response.postal.code}")
  
   return  [response.location.latitude, response.location.longitude]


def get_roaming_ip(ip,src):
 with geoip2.database.Reader('/var/www/html/fs_backend/GeoLite2-City.mmdb') as reader:
  if ip:
   response = reader.city(f"{ip}")
   query = ('SELECT concat("+",phonecode) as country_code,  e.roaming FROM extension_master e , `country`  WHERE iso =\"{0}\" and e.ext_number=\"{1}\"'.format(response.country.iso_code,src))
   country_code = get_info(query, "select", None)
   if country_code: 
       return  country_code[0][0]
   else:
       return  0

 

# Connect to FreeSWITCH using ESL
def get_info(query, qery_typ, arg):
    try:
        #print(query, arg, qery_typ)
        result = []
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            host=data["mysqlinfo"]["host"],
            database=data["mysqlinfo"]["database"],
            user=data["mysqlinfo"]["user"],
            password=data["mysqlinfo"]["password"],
            pool_name="pynative_pool",
            pool_size=5,
            pool_reset_session=True,
        )
        query
        connection_object = connection_pool.get_connection()
        if connection_object:
            cursor = connection_object.cursor()
            if qery_typ == "insert":
                cursor.execute(query)
                connection_object.commit()
                #print(query)
            elif qery_typ == "select":
                cursor.execute(query)
                result = cursor.fetchall()
                #print(result)
            elif qery_typ == "proc":
                cursor.callproc(query, arg)
                for result in cursor.stored_results():
                    result = result.fetchall()
        
            cursor.close()
    except mysql.connector.Error as error:
        print("Failed to table in MySQL: {}".format(error))
    finally:
        if connection_object.is_connected():
            cursor.close()
        
    return result

def exec_fs(cmd):
    conn = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
    if conn.connected():
        e = conn.events(str("json"), str("CHANNEL_CREATE"))
        e = conn.bgapi(cmd)
        e = conn.recvEvent()
        conn.disconnect()
    return e.getHeader("Channel-Call-UUID")


def create_event(e):
    #print(e.serialize())
    call_type = e.getHeader(str("variable_call_type"))
    cust_id = str(e.getHeader(str("variable_cust_id")))
    event = str(e.getHeader(str("Event-Name")))
    core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
    ip = str(e.getHeader(str("FreeSWITCH-IPv4")))
    sip_call_id = str(e.getHeader(str("variable_sip_call_id")))
    src = str(e.getHeader(str("Caller-Caller-ID-Number")))
    dest = str(e.getHeader(str("Caller-Destination-Number"))) 
    esl_country_code = str(e.getHeader(str("variable_sip_h_X-userip")))
    call_back_plugin = (e.getHeader(str("variable_plugin_data")))
    dail_prefix = str(e.getHeader(str("variable_dial_prefix")))
    gtwy = str(e.getHeader(str("variable_gateway_group_id")))
    ref_id = str(e.getHeader("variable_ref_id"))

    if esl_country_code !="None":
       esl_country_code=get_roaming_ip(esl_country_code,src)
    
    #print (f"dest {dest}  call_back_plugin {call_back_plugin} cust id {cust_id}  type_call {type_call} call_type  {call_type}  esl_country_code  {esl_country_code}  dail_prefix {dail_prefix} gtwy {gtwy}")
    
    if call_back_plugin:
      plugin_data = call_back_plugin.split("_") 
    else: 
     plugin_data = dest.split("_") 

    if plugin_data[0] == "plugin" :
        if  "sip" in  plugin_data[1]:
         query = (f'SELECT ext_number from  extension_master WHERE id={plugin_data[2]}')
         plugin_name = get_info(query, "select", None)
         dest = f"Plugin Extension ({plugin_name[0][0]})"
        elif  "ivr" in  plugin_data[1]:
         query = (f'SELECT name from  pbx_ivr_master WHERE id={plugin_data[2]}')
         plugin_name = get_info(query, "select", None)
         dest = f"Plugin IVR ({plugin_name[0][0]})"
        elif  "cg" in  plugin_data[1]:
         query = (f'SELECT name from  pbx_callgroup WHERE id={plugin_data[2]}')
         plugin_name = get_info(query, "select", None)
         dest = f"Plugin Call Group ({plugin_name[0][0]})"
        elif  "queue" in  plugin_data[1]:
         query = (f'SELECT name from  pbx_queue WHERE id={plugin_data[2]}')
         plugin_name = get_info(query, "select", None)
         dest = f"Plugin Queue  ({plugin_name[0][0]})"
        elif  "contact" in  plugin_data[1]:
         dest = f"Plugin Contact  ({plugin_data[2]})"

    if (type_call == "inbound" or (call_type is not None and  type_call == "outbound")) : 
        query = (
            "insert into pbx_realtime_cdr(uuid,src,dst,ip,current_status,callerid,sip_call_id,esl_country_code,destination,direct_gateway,customer_id,call_type,ref_id,sip_current_application"
            ')values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}","{9}","{10}","{11}","{12}","{13}")'.format(core_uuid,src,dest,ip,event,src,sip_call_id,esl_country_code,dail_prefix,gtwy,cust_id,type_call,ref_id,call_type))
        #print(query)dest
        get_info(query,"insert",None)
 


def answer_event(e):
    #print(e.serialize())
    call_type = str(e.getHeader(str("variable_call_type")))
    caller_read_codec = str(e.getHeader(str("Channel-Read-Codec-Name")))
    caller_write_codec = str(e.getHeader(str("Channel-Write-Codec-Name")))
    cust_id = str(e.getHeader(str("variable_cust_id")))
    core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
    dest = str(e.getHeader(str("Caller-Destination-Number"))) 
    application = str(e.getHeader(str("variable_application")))
    minute_plan_id = str(e.getHeader(str("variable_minute_plan_id")))
   

    print(f"call_type {call_type}  dest {dest}  application {application}  minute_plan_id {minute_plan_id}")
    
    
    if (type_call == "inbound" or (call_type is not None and  type_call == "outbound")) :  
           
        codec = str(e.getHeader(str("Channel-Write-Codec-Name")))
        event = str(e.getHeader(str("Event-Name")))
        buy_cost = e.getHeader(str("variable_buy_rate"))
        sell_cost = e.getHeader(str("variable_sell_rate"))
        sell_billing_blk = e.getHeader(str("variable_selling_billing_block"))
        call_plan = str(e.getHeader(str("variable_call_plan_id")))
        getwy = str(e.getHeader(str("variable_provider_id")))
        ref_id = str(e.getHeader("variable_ref_id"))
        #print(f"ref_id   {ref_id} sell_billing_blk {sell_billing_blk}")


        if application == "inbound":
         did_no = get_info("switch_verify_did_number", "proc", [dest])
         #print(f"\n\n switch_verify_did_number    is {did_no[0][0]} \n\n") 
  
         if  did_no[0][0]:
          print("VMN did to check",did_no[0][0])
          dest = get_info( "switch_vmn_cli_manipulation", "proc", [did_no[0][0]])
          dest = dest[0][0]
        
         #print(f"\n\n  dest {dest} \n\n") 
      
         query = (
                f'update pbx_realtime_cdr set current_status="{event}",dst="{dest}",ip_internal="{str(e.getHeader(str("variable_local_media_ip")))}" ,buy_cost="{buy_cost}",sell_cost="{sell_cost}",'
                f' selling_billing_block="{sell_billing_blk}", id_callplan="{call_plan}" , codec="{codec}",direct_gateway ="{getwy}",'
                f'call_type ="{application}",sip_current_application="{call_type}",clr_read_codec="{caller_read_codec}",ref_id="{ref_id}"'
                f',clr_write_codec="{caller_write_codec}", minute_plan_id="{minute_plan_id}"'
                f' where uuid="{core_uuid}"' )
       
         get_info(query,"insert",None)

        else:
            print("answered outbound  ",cust_id)
            query = (
                f'update pbx_realtime_cdr set  current_status="{event}", codec="{codec}" '
                f',call_type="{application}",sip_current_application="{call_type}",customer_id ="{cust_id}"'
                f',clr_read_codec="{caller_read_codec}",sell_cost="{sell_cost}",ref_id="{ref_id}"'
                f',clr_write_codec="{caller_write_codec}", minute_plan_id="{minute_plan_id}"'
                f' where uuid="{core_uuid}"')
            get_info(query,"insert",None)
      
    

def bridge_event(e):
 
    cust_id = str(e.getHeader(str("variable_cust_id")))
    caller_read_codec = str(e.getHeader(str("Channel-Read-Codec-Name")))
    caller_write_codec = str(e.getHeader(str("Channel-Write-Codec-Name")))
    event = str(e.getHeader(str("Event-Name")))
    call_type = str(e.getHeader(str("variable_call_type")))
    getway = str(e.getHeader(str("variable_gateway_group_id")))
    cle_uuid = str(e.getHeader(str("Bridge-B-Unique-ID")))
    buy_cost = e.getHeader(str("variable_buy_rate"))
    sell_rate = e.getHeader(str("variable_sell_rate"))
    sell_billing_blk = e.getHeader(str("variable_selling_billing_block"))
    call_plan = str(e.getHeader(str("variable_call_plan_id")))
    country_code = str(e.getHeader(str("variable_dial_prefix")))
    forward = str(e.getHeader(str("Caller-Callee-ID-Number")))
    ip_internal = e.getHeader(str("variable_sip_from_host"))
    core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
    ref_id = str(e.getHeader("variable_ref_id"))
    application = str(e.getHeader(str("variable_application")))
    minute_plan_id = str(e.getHeader(str("variable_minute_plan_id")))
    caller_id_number	 = str(e.getHeader(str("Other-Leg-Caller-ID-Number")))
 
    print(f"call_type {call_type} frwd {forward} app {application} mnt_plan_id {minute_plan_id } call_plan {call_plan} cust_id {cust_id}")
     
    if minute_plan_id == "None":
         minute_plan_id = call_plan


    if (type_call == "inbound" or (call_type is not None and  type_call == "outbound")) :  
        
        dial = "answered"

        if call_type == "outbound"  or application=="outbound":
            query = (
                f'update pbx_realtime_cdr set direct_gateway ="{getway}",cle_uuid="{cle_uuid}" ,buy_cost="{buy_cost}",callerid="{caller_id_number}"'
                f',sell_cost="{sell_rate}" ,selling_billing_block="{sell_billing_blk}",id_callplan="{call_plan}",destination="{country_code}",current_status="{event}",forward="{forward}"'
                f',ip_internal="{ip_internal}",sip_current_application="{call_type}",customer_id ="{cust_id}",'
                f'clr_read_codec="{caller_read_codec}",cle_read_codec="{caller_read_codec}",cle_write_codec="{caller_write_codec}", minute_plan_id="{minute_plan_id}"'
                f',clr_write_codec="{caller_write_codec}", call_type ="{application}" '
                f'where uuid ="{core_uuid}"')
            
            get_info(query,"insert",None)
           
        elif application == "inbound" or  application == "intercom":
            query = (
                f'update pbx_realtime_cdr set cle_uuid="{cle_uuid}" ,current_status="{event}",forward="{forward}",sip_current_application="{call_type}"'
                f',buy_cost="{buy_cost}" ,sell_cost="{sell_rate}",selling_billing_block="{sell_billing_blk}",customer_id="{cust_id}",callerid="{caller_id_number}"'
                f',clr_read_codec="{caller_read_codec}",cle_read_codec="{caller_read_codec}",cle_write_codec="{caller_write_codec}",minute_plan_id="{minute_plan_id}"'
                f',clr_write_codec="{caller_write_codec}", call_type ="{application}" '
                f'where uuid="{core_uuid}"')

            get_info(query,"insert",None)

        if (
            call_type == "call_queue"
            or call_type == "call_sticky_agent"
            or call_type == "call_cg_sticky_agent"
            or call_type == "call_group"
        ):
            feedback = 'insert into pbx_feedback(uuid,src,dst,customer_id,forward,ref_id )values("{0}","{1}","{2}",\
          "{3}","{4}","{5}")'.format(
                core_uuid,
                str(e.getHeader(str("Caller-Caller-ID-Number"))),
                str(e.getHeader(str("Caller-Destination-Number"))),
                str(e.getHeader(str("variable_cust_id"))),
                forward,
                ref_id,
            )
            get_info(feedback,"insert",None)
        


def hangup_event(e):

    call_type = e.getHeader(str("variable_call_type"))
    bridge_time = "0"
    session_time = "0"
    event = str(e.getHeader(str("Event-Name")))
    tc_time = str(e.getHeader(str("Caller-Channel-Bridged-Time")))
    hangup_time = str(e.getHeader(str("Event-Date-Timestamp")))
    created_time = str(e.getHeader(str("Caller-Channel-Created-Time")))
    dialstatus = str(e.getHeader(str("variable_DIALSTATUS")))
    ans_time = str(e.getHeader(str("Caller-Channel-Answered-Time")))
    application = str(e.getHeader(str("variable_application")))
    cust_id = str(e.getHeader(str("variable_cust_id")))
  
       

    if (type_call == "inbound"  or (call_type is not None and  type_call == "outbound")):  
      
        print(f"ans_time {(ans_time)}  {tc_time} cust_id {cust_id}  call_type  {call_type}")


        if (type(hangup_time) == str) and ans_time.isdigit():
            #if tc_time != "0" and int(ans_time) > 0:
            if  int(ans_time) > 0:

                bridge_time = str((int(hangup_time) - int(ans_time)) / 1000000)
            else:
             pass
            
             
        if  hangup_time.isdigit() and created_time.isdigit():
         session_time = str((int(hangup_time) - int(created_time)) / 1000000)

 
        query = (
            f'update pbx_realtime_cdr set call_disposition = "{str(e.getHeader("Hangup-Cause"))}",  bridge_time ={bridge_time}, customer_id="{cust_id}"'
            f',session_time ={session_time}, sip_endpoint_disposition= "{dialstatus}", current_status= "{event}", end_time= "{str(datetime.datetime.now())}"'
            f' ,sip_current_application ="{call_type}",call_type ="{application}" where uuid= "{str(e.getHeader(str("Channel-Call-UUID")))}" ')
        
        get_info(query,"insert",None)


        if (
            call_type == "call_queue"
            or call_type == "call_sticky_agent"
            or call_type == "call_cg_sticky_agent"
            or call_type == "call_group"
        ):
        
            fedbck_time = datetime.datetime.fromtimestamp(
                (int(hangup_time) / 1000000) + 300
            )
            feedback = (
                "update pbx_feedback set hangup_time ="
                + '"'
                + fedbck_time.strftime("%Y-%m-%d %H:%M")
                + '"'
                + "  where uuid="
                + '"'
                + e.getHeader(str("Channel-Call-UUID"))
                + '"'
            )
            get_info(feedback,"insert",None)
            

            #print("feedback",feedback)

           
        if (
            call_type in("call_queue","call_sticky_agent","outbound")
        ):
            msg = None
            fedbck_time = datetime.datetime.fromtimestamp(
                (int(hangup_time) / 1000000) + 300
            )
      
            
      
            try:
               
                sms_typ = (
                    "select ft.is_sms_type_custom ,IF(ft.sms_id !='',ft.sms_id, 0 ) as sms_id   from pbx_feature ft, "
                    "package pk,map_customer_package mcp where pk.id =mcp.package_id and pk.feature_id =ft.id"
                    " and mcp.customer_id="
                    + str(e.getHeader(str("variable_cust_id")))
                    + ""
                )
                sms_info = get_info(sms_typ, "select", None)
                if sms_info[0][0]:
                    api_qry = (
                        "select api.url, GROUP_CONCAT(map.header) as header,GROUP_CONCAT(map.value),"
                        "GROUP_CONCAT(map.is_type) from pbx_sms_api api,pbx_sms_api_mapping map where "
                        "map.sms_api_id=api.id and api.customer_id="
                        + e.getHeader(str("variable_cust_id"))
                        + " group by api.url"
                    )
                else:
                    api_qry = (
                        "SELECT api.url, GROUP_CONCAT(map.header) as header,GROUP_CONCAT(map.value),"
                        "GROUP_CONCAT(map.is_type)FROM pbx_sms sms ,pbx_sms_api api,pbx_sms_api_mapping map "
                        " where api.id=sms.provider  and map.sms_api_id=sms.provider and sms.id="
                        + sms_info[0][1]
                        + " group by sms.id"
                    )
                    api_info = get_info(api_qry, "select", None)

                print("is_sms_type_custom .... ",sms_info[0][0])
                
                if sms_info[0][0] == 0:  
                    sms_chrg_qry = get_info("switch_getCustomerSMSInfo","proc",[e.getHeader(str("variable_cust_id"))])
                    print(f"sms_chrg_qry   sms_type: {sms_chrg_qry[0][0] }   charge: {sms_chrg_qry[0][1] } Remainng_sms: {(sms_chrg_qry[0][2]) }")
                sms_flag = False
                sms_charge =  sms_chrg_qry[0][1]

                if  (sms_chrg_qry[0][0] == '1' or  sms_chrg_qry[0][0] == '2') and int(sms_chrg_qry[0][2]) > 0:
                 #print("sms_type 1 2 :: :: :: charge  ")
                 sms_flag = True
                 sms_charge  = '0'

                elif sms_chrg_qry[0][0] == '3' :
                 sms_flag = True
                 #print("sms_type 3:: :: :: pay per charge")
                    
               
                if api_info[0][0] is not None and sms_flag:
                    sms_num = str(e.getHeader(str("Caller-Destination-Number")))
                    parms = api_info[0][1].split(",")
                    val = api_info[0][2].split(",")
                    status = api_info[0][3].split(",")
                    FV = api_info[0][0] + "?"
                    url =''
                    sms_num= str(e.getHeader(str("Caller-Caller-ID-Number")))  if  call_type == "call_queue" \
                    or call_type == "call_sticky_agent"  else sms_num
                    
                    print("api_number",sms_num)
                    for p in range(len(parms)):
                     if status[p] == "0":
                      url += parms[p]+"="+ val[p] +"&"
                     if status[p] == "2": 
                      url += parms[p]+"="+ sms_num +"&"    
                    url = FV +url
                    #print(f" url params ***********************************{ url}")      
                 
               

                    if ( 
                        e.getHeader(str("variable_application")) == "inbound"
                        or call_type == "sip_extn"
                        or e.getHeader(str("variable_application")) == "outbound"
                    ) and dial == "noanswer":
                        if e.getHeader(str("variable_sms")) == "1":
                         mised_dtls = (
                            "SELECT description  FROM `pbx_sms_template` where category_id=6 and customer_id="
                            + e.getHeader(str("variable_cust_id"))
                            + " and status='1' limit 1"
                        )
                         mised_call = get_info(mised_dtls, "select", None)
                         print("mised_dtls--------------",mised_dtls)

                         for st in range(len(status)):
                            if status[st] == "1":
                                try:
                                    if mised_call[0][0] is not None:
                                        url = (
                                            url
                                            + parms[st]
                                            + "="
                                            + str(mised_call[0][0])
                                            + "&"
                                        )
                                except:
                                    print("mised_dtls  no")
                            if status[st] == "2":
                                if e.getHeader(str("variable_mobile")) is not None:
                                    url = (
                                        url
                                        + parms[st]
                                        + "="
                                        + e.getHeader(str("variable_mobile"))
                                        + "&"
                                    )
                         try:
                            print("real" + url)
                            res = reqs.get(url)
                            
                         except reqs.exceptions.RequestException as error:
                            print("sms_api error".format(error))
                         sms_cdr = (
                            "insert into pbx_sms_log(dest,customer_id,msg,category_id,is_sms_type_custom"
                            ",sms_id,amount)values("
                            f' "{str(e.getHeader(str("variable_mobile")))}"'
                            + ","
                            + '"'
                            + str(e.getHeader(str("variable_cust_id")))
                            + '"'
                            + ","
                            + '"'
                            + str(mised_call[0][0])
                            + '"'
                            + ",6,"
                            + str(sms_info[0][0])
                            + ","
                            + str(sms_info[0][1])
                            + ","
                            + str(sms_charge)
                            + ")"
                        )
                         get_info(sms_cdr,"insert",None)
                        if sms_info[0][0] == 0 and sms_chrg_qry[0][0] == '3':
                            sms_chrg_cdr = (
                                "insert into charge(product_id,customer_id,amount,description,"
                                "charge_type,charge_status,invoice_status,ref_id) values(1,"
                                + str(e.getHeader(str("variable_cust_id")))
                                + ","
                                + str(sms_charge)
                                + ","
                                + '"Charge for SMS-'
                                + str(e.getHeader(str("variable_mobile")))
                                + '"'
                                + ",3,0,0,"
                                + sms_info[0][1]
                                + ")"
                            )
                            get_info(sms_chrg_cdr,"insert",None)


                #print(f"SMS Bridged_Time -------> {bridge_time}  call_type {call_type}  sms_flag {sms_flag} ans_time {ans_time}   extension_no  {str(e.getHeader(str('Caller-Caller-ID-Number')))}\n\n\n" )  

                if (
                    call_type == "call_queue"
                    or call_type == "call_sticky_agent"
                    or call_type == "outbound" 
                ) and sms_flag:
                    
                    msg= None
                    call_info=str(0),str(e.getHeader(str("Caller-Caller-ID-Number"))),str(e.getHeader(str("Caller-Destination-Number"))),str(e.getHeader(str("Caller-Callee-ID-Number")))

                    if (float(bridge_time) > 0): 

                       sms_ans = get_info("varify_sms","proc",[e.getHeader(str("variable_ref_id")),e.getHeader(str("variable_cust_id")),str(e.getHeader(str('Caller-Caller-ID-Number')))])
                       print("sms_ans",sms_ans[0][0])

                       if sms_ans[0][0] == 1 and  call_type == "call_queue" or call_type == "call_sticky_agent":
                          sms_dtls = (
                              "SELECT description  FROM `pbx_sms_template` where category_id=1 and customer_id="
                              + e.getHeader(str("variable_cust_id"))
                              + " and status='1' limit 1"
                          )
                          msg = get_info(sms_dtls, "select", None)
                          category_id = "1"

                       elif sms_ans[0][0] == 1 and  call_type == "outbound":
                          sms_dtls = (
                              "SELECT description  FROM `pbx_sms_template` where category_id=3 and customer_id="
                              + e.getHeader(str("variable_cust_id"))
                              + " and status='1' limit 1"
                          )
                          msg = get_info(sms_dtls, "select", None)
                          category_id = "3"

                    else:

                      sms_noans = get_info("varify_sms_no_ans","proc",[e.getHeader(str("variable_ref_id")),e.getHeader(str("variable_cust_id")),
                            str(e.getHeader(str('Caller-Caller-ID-Number')))])

                    
                      print(f" sms_noans {sms_noans}  {call_type} ")

                      if sms_noans[0][0] == 1 and  call_type == "call_queue" or call_type == "call_sticky_agent":
                        
                        category_id = "2"
                        sms_dtls = (
                            "SELECT description  FROM `pbx_sms_template` where category_id=2 and customer_id="
                            + e.getHeader(str("variable_cust_id"))
                            + " and status='1' limit 1"
                        )
                        msg = get_info(sms_dtls, "select", None)

                      elif sms_noans[0][0] == 1 and  call_type == "outbound":
                        category_id = "4"
                        sms_dtls = (
                            "SELECT description  FROM `pbx_sms_template` where category_id=4 and customer_id="
                            + e.getHeader(str("variable_cust_id"))
                            + " and status='1' limit 1"
                        )
                        msg = get_info(sms_dtls, "select", None)
                  
                    #print(f"call_info %s   msg %s   url %s category_id %s"%(call_info,msg,url,category_id))
                    
                    try:
                        if msg:

                            msg = str(msg[0][0])  
                            count= msg.count("$var")
                            for index in range(1,count+1):
                              dynamic_value= "$var"+ str(index)
                              msg = msg.replace(dynamic_value,str(call_info[index]))

                            print(f"pbx_sms_template   desciption *******************  {msg }")
                            
                            url = url + "message" + "=" +msg+ "&"

                            print("real url  ------->>>>" + url)
                            res = reqs.get(url)
                            print(f" \n response     {res} \n  ")

                            query =f"SELECT id FROM `country`  WHERE phonecode ={str(e.getHeader(str('variable_dial_prefix')))}"
                            country_id = get_info(query, "select", None)
                      
                            #print(f"Destination ---->  {(sms_num)}  cust_id-- {str(e.getHeader(str('variable_cust_id')))}    category_id {category_id}  ")   
                              
                            sms_cdr = (
                                  "insert into pbx_sms_log(dest,customer_id,msg,category_id,is_sms_type_custom,sms_id,"
                                  "amount,country_id)values("
                                  + sms_num
                                  + ","
                                  + '"'
                                  + str(e.getHeader(str("variable_cust_id")))
                                  + '"'
                                  + ","
                                  + '"'
                                  + str(msg)
                                  + '"'
                                  + ","+category_id+","
                                  + str(sms_info[0][0])
                                  + ","
                                  + str(sms_info[0][1])
                                  + ","
                                  + str(sms_charge)
                                  + ","
                                  + str(country_id[0][0])
                                  + ")"
                              )
                         
                            get_info(sms_cdr,"insert",None)
  
  
                            if sms_info[0][0] == 0 and sms_chrg_qry[0][0] == '3':
                                  sms_chrg_cdr = (
                                      "insert into charge(product_id,customer_id,amount,description,charge_type,"
                                      "charge_status,invoice_status,ref_id) values(1,"
                                      + str(e.getHeader(str("variable_cust_id")))
                                      + ","
                                      + str(sms_charge)
                                      + ","
                                      + '"Charge for SMS-'
                                      + sms_num
                                      + '"'
                                      + ",3,0,0,"
                                      + sms_info[0][1]
                                      + ")"
                                  )
                                  get_info(sms_chrg_cdr,"insert",None)
  
                    except reqs.exceptions.RequestException as error:
                                print("sms_api error".format(error))
                                        
            
            except Exception as exp_error:
                print("create channel {0}".format(exp_error))


def destroy_event(e, where=None):
 call_type = str(e.getHeader(str("variable_call_type")))
 clr_signallingip = str(e.getHeader(str("variable_sip_h_X-userip")))
 clr_media_ip= str(e.getHeader(str("variable_sip_h_X-userMediaIP"))) 
 geo_loc =  str(e.getHeader(str("variable_geo_location")))
 server_ip = str(e.getHeader(str("variable_sip_local_network_addr")))
 user_agent = str(e.getHeader(str("variable_sip_user_agent")))
 calleeSignalingIP = str(e.getHeader(str("variable_sip_rh_X-calleeSignalingIP")))
 calleeMediaIP = str(e.getHeader(str("variable_sip_rh_X-calleeMediaIP")))
 application = str(e.getHeader(str("variable_application")))
 cust_id = str(e.getHeader(str("variable_cust_id")))
 cle_lat_long = None ; clr_lat_long=None

  
 if (geo_loc == '1'):

  if clr_signallingip != "None":
   clr_lat_long = get_loc(clr_signallingip)
  else:
   clr_signallingip = str(e.getHeader(str("variable_sip_via_host")))  
   clr_media_ip = str(e.getHeader(str("variable_remote_media_ip")))  
        
  
 if (type_call == "inbound" or  type_call == "outbound"  and application != "None"):
  
     query = (
           f'update pbx_realtime_cdr set clr_mos ="{str(e.getHeader(str("variable_rtp_audio_in_mos")))}",clr_jitter_min_variance ="{str(e.getHeader(str("variable_rtp_audio_in_jitter_min_variance")))}",'
           f'clr_jitter_max_variance="{str(e.getHeader(str("variable_rtp_audio_in_jitter_max_variance")))}",'
           f'clr_jitter_loss_rate ="{str(e.getHeader(str("variable_rtp_audio_in_jitter_loss_rate")))}", clr_jitter_burst_rate="{str(e.getHeader(str("variable_rtp_audio_in_jitter_burst_rate")))}" ,clr_mean_interval="{str(e.getHeader(str("variable_rtp_audio_in_mean_interval")))}",'
           f'clr_quality_percentage ="{str(e.getHeader(str("variable_rtp_audio_in_quality_percentage")))}",clr_read_codec="{str(e.getHeader(str("variable_original_read_codec")))}" ,clr_write_codec="{ str(e.getHeader(str("variable_write_codec")))}",clr_dtmf_type ="{str(e.getHeader(str("variable_dtmf_type")))}"'
           f',clr_local_media_ip="{clr_media_ip}",clr_media_ip="{clr_media_ip}",clr_user_agent="{user_agent}", customer_id = "{cust_id}", sip_current_application  = "{call_type}", call_type  = "{application}"'
           f',clr_remote_media_ip="{clr_signallingip}",clr_signalling_ip ="{clr_signallingip}",clr_remote_media_port="{str(e.getHeader(str("variable_local_media_port")))}",current_status="{"CHANNEL_HANGUP"}",clr_lat_long="{clr_lat_long}"'
           f' where uuid="{str(e.getHeader(str("Channel-Call-UUID")))}"')
       
     get_info(query,"insert",None)
      
     
 elif (type_call == "inbound" or  type_call == "outbound"  and application == "None"): 

   if calleeSignalingIP != "None":
    cle_lat_long = get_loc(calleeSignalingIP)
   else:
     calleeSignalingIP = str(e.getHeader(str("variable_sip_reply_host")))          
     calleeMediaIP =str(e.getHeader(str("variable_remote_media_ip")))

 query = (
             f'update pbx_realtime_cdr set cle_lat_long="{cle_lat_long}"'
             f',cle_mos ="{str(e.getHeader(str("variable_rtp_audio_in_mos")))}",cle_jitter_min_variance ="{str(e.getHeader(str("variable_rtp_audio_in_jitter_min_variance")))}",'
             f'cle_jitter_max_variance="{str(e.getHeader(str("variable_rtp_audio_in_jitter_max_variance")))}",'
             f'cle_jitter_loss_rate ="{str(e.getHeader(str("variable_rtp_audio_in_jitter_loss_rate")))}", cle_jitter_burst_rate="{ str(e.getHeader(str("variable_rtp_audio_in_jitter_burst_rate")))}" ,cle_mean_interval="{str(e.getHeader(str("variable_rtp_audio_in_mean_interval")))}",'
             f'cle_quality_percentage ="{str(e.getHeader(str("variable_rtp_audio_in_quality_percentage")))}",cle_read_codec="{str(e.getHeader(str("variable_original_read_codec")))}" ,cle_write_codec="{str(e.getHeader(str("variable_write_codec")))}",cle_dtmf_type ="{str(e.getHeader(str("variable_dtmf_type")))}"'
             f',cle_local_media_ip="{calleeMediaIP}",cle_media_ip="{calleeMediaIP}",cle_user_agent="{user_agent}", customer_id = "{cust_id}",sip_current_application  = "{call_type}",call_type ="{application}"' 
             f',cle_remote_media_ip="{calleeSignalingIP}" ,cle_signalling_ip="{calleeSignalingIP}",cle_remote_media_port="{str(e.getHeader(str("variable_remote_media_port")))}",server_ip="{server_ip}"'
             f' where cle_uuid="{str(e.getHeader(str("Channel-Call-UUID")))}"')
         
 get_info(query,"insert",None)



def hangup_complete(e):

    call_type = str(e.getHeader(str("variable_call_type")))
    cc_switch=str(e.getHeader(str('variable_sip_h_X-switch')))
    sip_ip = e.getHeader("variable_sip_network_ip")
    hangup = e.getHeader("variable_hangup_cause")
    forward = str(e.getHeader(str("Caller-Callee-ID-Number")))
    
    query = "SELECT DISTINCT(ip) FROM `address`"
    whitelist_ip = get_info(query, "select", None)
    arr = numpy.array(whitelist_ip)
    loc = numpy.where(arr == sip_ip)

    
    if cc_switch!='cc-ecpl' and  not loc[0]:
        logging.info("Assuming attack from %s HCAUSE %s",sip_ip,hangup)
        print("Assuming attack from %s HCAUSE %s",sip_ip,hangup)
    

    if (type_call == "inbound" or (call_type is not None and  type_call == "outbound")) :  
        is_record = str(e.getHeader(str("variable_set_recording")))
        record_sec = str(e.getHeader("variable_record_seconds"))
        record_file = str(e.getHeader("variable_recording_file"))
        term_cause = str(e.getHeader("variable_custom_hangup"))
        dialstatus_check = str(e.getHeader("variable_hangup_cause"))
        dialstatus = str(e.getHeader("variable_originate_failed_cause"))
        is_frwd = str(e.getHeader("variable_set_frwd"))
        is_voicemail = str(e.getHeader("variable_voicemail_file_path"))
        rec_num = str(e.getHeader(str("variable_rec_num")))
        rec_callee = str(e.getHeader(str("variable_rec_callee")))
        sip_invite_failure_status = str(e.getHeader(str("variable_sip_invite_failure_status")))
        sip_term_status = str(e.getHeader(str("variable_sip_term_status")))
        proto_specific_hangup_cause = str(e.getHeader(str("variable_last_bridge_proto_specific_hangup_cause")))
        hangup_dis = str(e.getHeader(str("variable_sip_hangup_disposition")))
        core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
        num = str(e.getHeader(str("Caller-Username")))
        callee = str(e.getHeader(str("Caller-Destination-Number")))
        customer_id = str(e.getHeader(str("variable_cust_id")))
        date = str(e.getHeader(str("Event-Date-Local")))
        rec_type = str(e.getHeader(str("variable_rec_type")))
        #print(e.serialize())
        
        if term_cause == "None":
            term_cause = sip_term_status

        if term_cause == "None":
            term_cause = sip_invite_failure_status

        if term_cause == "None":
            term_cause = proto_specific_hangup_cause
            if term_cause.startswith("sip:"):
                term_cause = term_cause[4:]
                print("sip custom term_cause \n",term_cause)

        if term_cause == "None":
            if dialstatus == "NO_ANSWER":
                term_cause = 480
            elif  dialstatus_check =="NORMAL_CLEARING": 
                term_cause = 200
            elif  dialstatus_check =="ALLOTTED_TIMEOUT": 
                term_cause = 602
            elif  dialstatus_check =="USER_BUSY": 
                term_cause = 486

            elif  dialstatus_check =="UNKNOWN" and str(e.getHeader('variable_last_arg')) == "+0 1006":   
                term_cause= 1006
            else:
                term_cause = "608"
       
        
                  

        if str(e.getHeader(str("variable_sip_hangup_disposition"))) == "recv_cancel":
            hangup_dis = "recv_bye"  
        elif  str(e.getHeader(str("variable_sip_hangup_disposition"))) == "send_refuse" and str(e.getHeader("variable_DIALSTATUS")) == "SUCCESS":
            hangup_dis = "recv_cancel"
        elif  str(e.getHeader(str("variable_sip_hangup_disposition"))) == "send_refuse" and str(e.getHeader("variable_DIALSTATUS")) != "NOANSWER":
            hangup_dis = "recv_cancel" 

        query = f"update pbx_realtime_cdr set terminatecause='{term_cause}',hangup_disposition='{hangup_dis}',is_forward='{ is_frwd if is_frwd != 'None' else 0 }',forward ='{forward}' where uuid='{core_uuid}'"
        get_info(query,"insert",None)
        
      
        print(call_type, type_call, rec_type, is_record, record_sec, record_file, rec_num)

        if ( is_record == "1" and call_type != "call_voicemail" and record_sec != "None" and record_sec != "0"):

            if (call_type in ("call_queue","call_tc")):
               rec_callee= callee
               rec_num=num
               record_file=str(e.getHeader(str("variable_cc_record_filename"))).split("/")
               if call_type == "call_tc":
                   rec_type = "Tele Consultancy"
               else:
                   rec_type = "Call Queue"

            else:
               record_file = record_file.split("/")

            if  record_file[-1] !="None":  
              query = (f"INSERT INTO `pbx_recording` (`file_name`, `customer_id`, `src`, `type`, `dest`, `status`) VALUES\
                  ('{record_file[-1]}', '{customer_id}', '{rec_num}', '{rec_type}','{rec_callee}', '1')")
              get_info(query,"insert",None)
              print(query)


        if call_type == "click2call" and record_sec != "None":
            billing_sec = str(e.getHeader("variable_billsec"))
            if int(billing_sec) > 0:
                num = str(e.getHeader(str("Other-Leg-Destination-Number")))
                callee = str(e.getHeader(str("Caller-Callee-ID-Number")))
                rec = str(e.getHeader(str("variable_execute_on_originate")))
                record = rec.split("/")
                query = "INSERT INTO `pbx_recording` (`file_name`, `customer_id`, `src`,\
                           `type`, `dest`, `status`) VALUES\
                            ('{8}', '{4}', '{5}', '{6}', '{7}', '1')\
                            ".format(
                    call_type,
                    num,
                    callee,
                    date,
                    customer_id,
                    num,
                    call_type,
                    callee,
                    record[-1]
                )
                get_info(query,"insert",None)
                
        
      
        if call_type == "call_voicemail" and is_voicemail != "None":
            callee = str(e.getHeader(str("variable_voicemail_account")))
            query = ("select otherEmail, voicemailToEmail ,delVoicemailAfterEmail,deliverVoicemailTo from pbx_voicemail join\
                     extension_master on pbx_voicemail.extension_id = extension_master.id\
                     WHERE extension_master.ext_number ='{0}'".format(callee))

            vm_callback = get_info(query, "select", None)
         
            msg = is_voicemail.split("/")
            
            if len(vm_callback) == 0:
               
                query = "INSERT INTO `pbx_voicemail_recording` (`file_name`, `customer_id`, `src`,\
                                `dest`, `status`, `created_at`) VALUES\
                                ('{0}', '{1}', '{2}', '{3}', '1', '{4}')\
                                ".format(
                    msg[-1], customer_id, num, callee, date
                )
                get_info(query,"insert",None)
            elif len(vm_callback) == 1:
                if(vm_callback[0][2])==0:
                 query = "INSERT INTO `pbx_voicemail_recording` (`file_name`, `customer_id`, `src`,\
                                `dest`, `status`, `created_at`) VALUES\
                                ('{0}', '{1}', '{2}', '{3}', '1', '{4}')\
                                ".format(
                    msg[-1], customer_id, num, callee, date
                )
                get_info(query,"insert",None)

          
            
         
           
def broadcastthread(e,dest_no):
      con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
      if con.connected():
        
        print(f"Broadcasting thread executed for ......... {dest_no}")
        time.sleep(60)
       
        gw_id = str(e.getHeader(str("variable_gateway_group_id"))) 
        cust_id = str(e.getHeader(str("variable_cust_id"))) 
        callee = str(e.getHeader(str("Caller-Destination-Number")))
        cli = e.getHeader(str("variable_origination_caller_id_number")) 
        ref_id = str(e.getHeader(str("variable_ref_id"))) 
        dial_prefix = str(e.getHeader(str("variable_dial_prefix"))) 
        buy_rate = str(e.getHeader(str("variable_buy_rate"))) 
        sell_rate = str(e.getHeader(str("variable_sell_rate"))) 
        call_plan_id = str(e.getHeader(str("variable_call_plan_id"))) 
        sell_min = str(e.getHeader(str("variable_selling_min_duration"))) 
        sell_blk = str(e.getHeader(str("variable_selling_billing_block"))) 
        b_type = str(e.getHeader(str("variable_billing_type"))) 
        is_mnt = str(e.getHeader(str("variable_is_mnt_plan"))) 
        is_grp = str(e.getHeader(str("variable_is_group_mnt_plan"))) 
        t_mnt = str(e.getHeader(str("variable_talking_mnt"))) 
        cprt_mnt_id = str(e.getHeader(str("variable_call_plan_rate_mnt_id"))) 
        t_blc = str(e.getHeader(str("variable_total_balance"))) 
        c_blc = str(e.getHeader(str("variable_credit_blance"))) 
        ply_bck = str(e.getHeader(str("variable_ply_bck"))) 
        cprt_grmnt_id = str(e.getHeader(str("variable_call_plan_rate_group_mnt_id"))) 

        gtwy_limit = get_info("switch_api_concurrent_call", "proc",(cust_id,gw_id) )
        gtwy_limit = int(gtwy_limit[0][0])

        print("%s %s  gtwy_limit %s "%(call_type,cust_id,gtwy_limit))  

        if gtwy_limit > 0:
           
           cmd=f"originate {{ignore_early_media=true,origination_caller_id_number={cli}"\
            f",outbound_caller_from_user={cli},origination_caller_id_name={callee},cust_id={cust_id},"\
            f"call_type={call_type},ref_id={ref_id},application=outbound,gateway_group_id={gw_id},"\
            f"call_plan_id={call_plan_id},dial_prefix={dial_prefix},buy_rate={buy_rate},sell_rate={sell_rate},selling_min_duration="\
            f"{sell_min},selling_billing_block={sell_blk},billing_type={b_type},is_mnt_plan={is_mnt},talking_mnt={t_mnt},call_plan_rate_mnt_id={cprt_mnt_id},"\
            f"is_group_mnt_plan={is_grp},call_plan_rate_group_mnt_id={cprt_grmnt_id},total_balance={t_blc},credit_blance={c_blc}"\
            f"}}sofia/gateway/gw_{gw_id}/{str(callee)} &playback(/var/www/html/pbx/app{ply_bck})"  
           
           print(f"calling ..........  {dest_no}")
           con.api(cmd)

        else :
                    #failed_agent.append(agent)
                    query = ("insert into pbx_realtime_cdr(uuid,src,dst,current_status,direct_gateway,call_type,terminatecause,customer_id,sip_current_application"
                    ')values("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}")'.format(str(uuid.uuid1()),cli,callee,"CHANNEL_HANGUP",gw_id,"outbound","1007",cust_id,call_type))
                    get_info(query, "insert", None)
                    print("failed agent due to gtwy limit ",callee) 
                       
              
                


def callback_url(e):

 call_type = str(e.getHeader(str("variable_call_type")))
 core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
 event = str(e.getHeader(str("Event-Name")))
 Answer_State = str(e.getHeader(str("Answer-State")))
 src = str(e.getHeader(str("Caller-Caller-ID-Number")))
 dest = str(e.getHeader(str("Caller-Destination-Number")))


     
 if (call_type == "click2call" ):  
                
         query = "SELECT callback_url fROM `customer` where id='{0}' and is_callback_url=1".format(str(e.getHeader(str("variable_cust_id"))))
         call_back = get_info(query, "select", None)
 
         if len(call_back) != 0:
            if (event == "CHANNEL_HANGUP" or "CHANNEL_ANSWER" or "CHANNEL_CREATE"): 
                 """ and (Answer_State == "ringing" or "answered" or "hangup") """
                 call_data = {"UUID":core_uuid ,"Current_Status": event,"State":Answer_State ,"Source":src,"Destination":dest,"Direction":str(e.getHeader(str("Caller-Logical-Direction")))}
                 #webhook_url = "https://webhook.site/600cef8f-1570-4b86-8e6b-e836440e8974"
                 
                 if call_back[0][0]:
                  webhook_url = list(call_back[0])
                  r = requests.get(webhook_url[0], params= call_data)
                 
                  return r 


""" def backgroud_job_handle(e):
    bgapi_broadcast_cmd=e.getHeader(str("Job-Command-Arg"))
    print("job_uuid   ",e.serialize())  
    print("broadcast handle ---------------->",bgapi_broadcast_cmd) 
       """




con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
if con.connected():
    con.events(str("json"), str("CHANNEL_CREATE"))
    con.events(str("json"), str("CHANNEL_ANSWER"))
    con.events(str("json"), str("CHANNEL_BRIDGE"))
    con.events(str("json"), str("CHANNEL_HANGUP"))
    con.events(str("json"), str("CHANNEL_HANGUP_COMPLETE"))
    con.events(str("json"), str("CHANNEL_DESTROY"))
    con.events(str("json"), str("SERVER_DISCONNECTED"))
    con.events(str("json"), str("BACKGROUND_JOB"))
    
    while 1:
     time.sleep(0.000000005)
     
     e = con.recvEvent()
   
     if str(e.getHeader(str("Event-Name")))=='SERVER_DISCONNECTED':
         con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
         type_call = e.getHeader(str("variable_direction"))
     if e:
            #print(e.serialize())
            event_type = e.getType()
            con.events(str("json"), str("SERVER_DISCONNECTED"))
            con.events(str("json"), str("BACKGROUND_JOB"))
            con.events(str("json"), str("CHANNEL_CREATE"))
            con.events(str("json"), str("CHANNEL_ANSWER"))
            con.events(str("json"), str("CHANNEL_BRIDGE"))
            con.events(str("json"), str("CHANNEL_HANGUP"))
            con.events(str("json"), str("CHANNEL_HANGUP_COMPLETE"))
            con.events(str("json"), str("CHANNEL_DESTROY"))
            
            
            dial = "noanswer"
            click2call_cdr = str(e.getHeader(str("Caller-Logical-Direction")))
            type_call = str(e.getHeader(str("variable_direction")))
            call_type = str(e.getHeader(str("variable_call_type")))
            cust_id = str(e.getHeader(str("variable_cust_id")))
            core_uuid = str(e.getHeader(str("Channel-Call-UUID")))
            codec = str(e.getHeader(str("Channel-Write-Codec-Name")))
            event = str(e.getHeader(str("Event-Name")))
            ip = str(e.getHeader(str("variable_sip_h_X-userip")))

            callback_url(e)              
          

            if event_type == "CHANNEL_CREATE":
                try:
                    
                    create_event(e)
                   
                    
                except Exception as error:
                    print("create channel {0}".format(error))

            if event_type == "CHANNEL_ANSWER":
                try:
                    answer_event(e)
                    
                except Exception as error:
                    print("create channel {0}".format(error))


            if event_type == 'CHANNEL_BRIDGE':
                try:
                    bridge_event(e)
                    
                except Exception as error:
                    print("create channel {0}".format(error))

            if event_type == "CHANNEL_HANGUP" :
                hangup_event(e)
                
            if event_type == "CHANNEL_DESTROY":
                try:
                    destroy_event(e)
                    
                except Exception as error:
                    print("create channel {0}".format(error))

            if event_type == "CHANNEL_HANGUP_COMPLETE":
                 dest_no = str(e.getHeader(str("Caller-Destination-Number")))
                 
                 hangup_thread = threading.Thread(target=hangup_complete,args=(e,))
                 bc_thread = threading.Thread(target=broadcastthread,args=(e,dest_no))
                 hangup_thread.start()
                 job_uuid = str(e.getHeader(str("variable_job_uuid")))
                 term_cause =str(e.getHeader(str("variable_sip_invite_failure_phrase")))
                 application =str(e.getHeader(str("variable_application")))
                 if term_cause == "None":
                       term_cause = str(e.getHeader(str("variable_endpoint_disposition")))

                 #print(f" {job_uuid}  {application } {call_type }  {term_cause} ")    
                 if  job_uuid  != "None" and application =="outbound" and call_type =="call_broadcast" and term_cause not in ('ANSWER','CANCEL'):    
                  bc_thread.start()
                  continue
                   
                 
                

            if event_type == "BACKGROUND_JOB":
                #backgroud_job_handle(e)  
                pass   
   

   

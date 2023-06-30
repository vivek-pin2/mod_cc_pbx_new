from email.mime import application
from itertools import count
import math
import logging.config
import logging.handlers
import string
import ESL
import sys
import requests as reqs
import json
import mysql.connector
from mysql.connector import Error
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling
import threading
import schedule
import time
import datetime
import os
# import  billing
# import _ESL
from ESL import *
import queue
import threading
import time

# current time
now=datetime.datetime.now()
current_time = now.strftime("%d/%m/%Y %H:%M:%S,%f")
seconds_in_day = 24 * 60 * 60

formatter = logging.Formatter('%(asctime)s %(levelname)s:%(lineno)s\t%(message)s')  # logger module
handler = logging.handlers.TimedRotatingFileHandler('/var/log/fs_billing_cdr.log', when="midnight", backupCount=10)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

with open('config.json') as config:
    data = json.load(config)
#119.18.55.154
# import queue
def profile_info(query, qery_typ, arg):
    try:
        result = []
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(
            host=data['mysqlinfo']['host'],
            database=data['mysqlinfo']['database'],
            user=data['mysqlinfo']['user'],
            password=data['mysqlinfo']['password'],
            pool_name="pynative_pool",
            pool_size=15,
            autocommit=True,
            pool_reset_session=True)
        mysql_query = query
        connection_object = connection_pool.get_connection()
        if connection_object:
            cursor = connection_object.cursor(dictionary=True)
            logging.info(mysql_query)
            #print(mysql_query)
            cursor.execute(mysql_query)
            if qery_typ == "insert":
                cursor.insert_id()
                cursor.commit()
            elif qery_typ == "select":
                result = cursor.fetchall()
                num_of_row = cursor.rowcount
                logging.info("row count is %s", num_of_row)
                #print(result)
            elif qery_typ == "proc":
                logging.info(qery_typ)
                cursor.callproc(query)
                for result in cursor.stored_results():
                    result = result.fetchall()
            # connection.commit()
            cursor.close()
    except mysql.connector.Error as error:
        logging.error("Failed to   table in MySQL: {}".format(error))
    finally:
        if connection_object.is_connected():
            cursor.close()
           # connection_object.close()
            logging.info("MySQL connection is closed")
        return result


class MyThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        process_queue()


def process_queue():
    while True:
        try:
            x = my_queue.get(block=False)
        except queue.Empty:
            return
        else:
            event = e.getType()
            if event_type == "CHANNEL_CREATE":
                create_event(e)
            elif event == 'CHANNEL_ANSWER':
                event_answer(e)
            elif event == 'CHANNEL_BRIDGE':
                event_bridge(e)
            elif event == 'CHANNEL_HANGUP':
                event_hangup(e)
            elif event == 'CHANNEL_DESTROY':
                event_destroy(e)


my_queue = queue.Queue()


def get_server_details():
    query = "select distinct(ip) from server_details where service_id='2'"
    profile_info(query, 'select', None)
    #print(query)


def create_event(e):
     pass
  
def event_bridge(e):
    #print(f"total_balance {str(e.getHeader(str('variable_total_balance')))}")

    pass

    


def event_answer(e):
    did_sell_rate = {str(e.getHeader(str('variable_did_sell_rate')))}
    application= str(e.getHeader(str("variable_application")))
    call_type=str(e.getHeader(str('variable_call_type')))

    #print(f"answer function called time {current_time} call_type {call_type}   did_sell_rate {did_sell_rate} type_call {type_call} application {application} \n ")
   
    call_data = {'server_details': str(e.getHeader(str("FreeSWITCH-IPv4")))}
    call_data['customer_id'] = str(e.getHeader(str("variable_cust_id")))
    call_data['core_uuid'] = str(e.getHeader(str("Channel-Call-UUID")))
    call_data['server_details'] = str(e.getHeader(str("FreeSWITCH-IPv4")))
    call_data['talking_mnt'] = str(e.getHeader(str("variable_talking_mnt")))
    call_data['talking_grp_mnt'] = str(e.getHeader(str("variable_talking_group_mnt")))
    call_data['is_grp_mnt_plan'] = str(e.getHeader(str("variable_is_group_mnt_plan")))
    call_data['is_mnt_plan'] = str(e.getHeader(str("variable_is_mnt_plan")))
    call_data['call_type'] = str(e.getHeader(str("variable_call_type")))
    call_data['application'] = str(e.getHeader(str("variable_application")))
    call_data['dial_prefix'] = str(e.getHeader(str('variable_dial_prefix')))
    call_data['billing_type'] = str(e.getHeader(str('variable_billing_type')))
    call_data['sell_rate'] = str(e.getHeader(str('variable_sell_rate')))
    call_data['selling_min_duration'] = str(e.getHeader(str('variable_selling_min_duration')))
    call_data['selling_billing_block'] = str(e.getHeader(str('variable_selling_billing_block')))
    call_data['call_plan_id'] = str(e.getHeader(str('variable_call_plan_id')))
    call_data['buy_rate'] = str(e.getHeader(str('variable_buy_rate')))
    call_data['talking_blance'] = str(e.getHeader(str('variable_talking_blance')))
    call_data['credit_balance'] = str(e.getHeader(str("variable_credit_blance")))
    call_data['total_balance'] = str(e.getHeader(str('variable_total_balance')))
    call_data['did_connect_charge'] = str(e.getHeader(str('variable_did_connect_charge')))
    call_data['did_billing_type'] = str(e.getHeader(str("variable_did_billing_type")))
    call_data['caller']=str(e.getHeader(str('Caller-Caller-ID-Number')))
    call_data['server_details'] = str(e.getHeader(str("FreeSWITCH-IPv4")))
    call_data['custom_hangup'] = str(e.getHeader(str('variable_custom_hangup')))

    

    #print("cust id ",call_data['customer_id'],  call_data['custom_hangup'] )
    #e.addHeader("sell_rate",call_data['sell_rate'] )

    if type_call == "inbound" and call_type != "None" and application =="outbound" and  call_data['billing_type'] !="None":
        
        call_data['core_uuid'] = str(e.getHeader(str("Channel-Call-UUID")))
        
        call_data['caller']=str(e.getHeader(str('Caller-Caller-ID-Number')))
        
        if call_data['is_mnt_plan'] == 'None':
            call_data['is_mnt_plan'] = call_data['is_grp_mnt_plan']
            call_data['talking_mnt'] = call_data['talking_grp_mnt']
            #print(f"swap grp mnt{call_data['is_mnt_plan']} talking_group_mnt----->{call_data['talking_mnt']}")
        
        #print(f"is_mnt_plan --->{call_data['is_mnt_plan']}  billng_type --{call_data['billing_type']}   did_billng_type-->{call_data['did_billing_type']} did_connect_charge --{call_data['did_connect_charge']}")
        #print(e.serialize())
  
        real_time_data = "insert into  pbx_real_time_billing (uuid,customer_id,billing_type,server_details," \
                         "call_type,call_application,destination,sell_rate,buy_rate,selling_min_duration," \
                         "selling_billing_block,caller,did_connect_charge,did_billing_type) values (\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\"" \
                         ",\"{7}\",\"{8}\",\"{9}\",\"{10}\",\"{11}\",\"{12}\",\"{13}\")" \
            .format(call_data['core_uuid'], call_data['customer_id'], call_data['billing_type'],
                    call_data['server_details'], call_data['call_type'], call_data['application'],
                    call_data['dial_prefix'], call_data['sell_rate'], call_data['buy_rate'],
                    call_data['selling_min_duration'], call_data['selling_billing_block'],call_data['caller'],call_data['did_connect_charge'],call_data['did_billing_type'])
        profile_info(real_time_data, 'insert', None)
            # if int(call_data['talking_mnt']) >= 1 and call_data['is_mnt_plan'] == '1':
        if call_data['is_mnt_plan'] == '1':
         if call_data['call_type'] == 'outbound' or call_data['application'] == 'outbound':
                get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type," \
                           "call_application,server_details ,start_time from pbx_real_time_billing where" \
                           " customer_id=\"{0}\" and  billing_type=\"{1}\" " \
                    .format(call_data['customer_id'], call_data['billing_type'])
                live_call = profile_info(get_call, 'select', None)
                print("live call  time ", datetime.datetime.now())
                call_deduct_mnt_outbound(call_data, live_call, 1)
              
        elif call_data['billing_type'] == "3":
            deduct_balance(e, call_data, 0)

    elif (call_type == "click2call" or call_type == "call_broadcast" or call_type == "call_feedback" or  call_type == "call_plugin" ) and  type_call =="outbound"and application =="outbound" and  call_data['billing_type'] !="None" :
        
        if call_data['is_mnt_plan'] == 'None':
            call_data['is_mnt_plan'] = call_data['is_grp_mnt_plan']
            
        #print(f"swap grp mnt{call_data['is_mnt_plan']} talking_group_mnt----->{call_data['talking_mnt']} is_mnt_plan --->{call_data['is_mnt_plan']}  billng_type --{call_data['billing_type']}")
        
        real_time_data = "insert into  pbx_real_time_billing (uuid,customer_id,billing_type,server_details," \
                         "call_type,call_application,destination,sell_rate,buy_rate,selling_min_duration," \
                         "selling_billing_block,caller ) values (\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\"" \
                         ",\"{7}\",\"{8}\",\"{9}\",\"{10}\",\"{11}\")" \
            .format(call_data['core_uuid'], call_data['customer_id'], call_data['billing_type'],
                    call_data['server_details'], type_call,call_data['call_type'],
                    call_data['dial_prefix'], call_data['sell_rate'], call_data['buy_rate'],
                    call_data['selling_min_duration'], call_data['selling_billing_block'],call_data['caller'])
        profile_info(real_time_data, 'insert', None)
           
        if call_data['is_mnt_plan'] == '1':
         
          get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type," \
                     "call_application,server_details ,start_time from pbx_real_time_billing where" \
                     " customer_id=\"{0}\" and  billing_type=\"{1}\" " \
              .format(call_data['customer_id'], call_data['billing_type'])
          live_call = profile_info(get_call, 'select', None)
          print("live call  time ", datetime.datetime.now())
          call_deduct_mnt_outbound(call_data, live_call, 1)
              
        elif call_data['billing_type'] == "3":
            deduct_balance(e, call_data, 0)


    elif   did_sell_rate != "None"  and  application =="inbound"  :

        real_time_data = "insert into  pbx_real_time_billing (uuid,customer_id,billing_type,server_details," \
                         "call_type,call_application,destination,sell_rate,buy_rate,selling_min_duration," \
                         "selling_billing_block,caller,did_connect_charge,did_billing_type) values (\"{0}\",\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\"" \
                         ",\"{7}\",\"{8}\",\"{9}\",\"{10}\",\"{11}\",\"{12}\",\"{13}\")" \
            .format(call_data['core_uuid'], call_data['customer_id'], call_data['billing_type'],
                    call_data['server_details'], call_data['call_type'], call_data['application'],
                    call_data['dial_prefix'], call_data['sell_rate'], call_data['buy_rate'],
                    call_data['selling_min_duration'], call_data['selling_billing_block'],call_data['caller'],call_data['did_connect_charge'],call_data['did_billing_type'])
        profile_info(real_time_data, 'insert', None)

          
        deduct_balance(e, call_data, 0)
     


def event_hangup(e):
    #print(e.serialize())

    call_hangup_dtl = {'core_uuid': str(e.getHeader(str("Channel-Call-UUID"))),
                           'bridge_time': str(e.getHeader(str("Caller-Channel-Answered-Time"))),
                           'hangup_time': str(e.getHeader(str("Event-Date-Timestamp"))),
                           'call_plan_rate_mnt_id': str(e.getHeader(str('variable_call_plan_rate_mnt_id'))),
                           'talking_mnt': str(e.getHeader(str("variable_talking_mnt"))),
                           'is_mnt_plan': str(e.getHeader(str('variable_is_mnt_plan'))),
                           'is_grp_mnt_plan': str(e.getHeader('variable_is_group_mnt_plan')),
                           'talking_grp_mnt': str(e.getHeader('variable_talking_group_mnt')),
                           'group_id': str(e.getHeader('variable_call_plan_rate_group_mnt_id')),
                           'server_details': str(e.getHeader(str("FreeSWITCH-IPv4"))),
                           'customer_id': str(e.getHeader(str("variable_cust_id"))),
                           'call_type': str(e.getHeader(str("variable_call_type"))),
                           'application': str(e.getHeader(str("variable_application"))),
                           'dial_prefix': str(e.getHeader(str('variable_dial_prefix'))),
                           'billing_type': str(e.getHeader(str('variable_billing_type'))),
                           'sell_rate': str(e.getHeader(str('variable_sell_rate'))),
                           'selling_min_duration': str(e.getHeader(str('variable_selling_min_duration'))),
                           'selling_billing_block': str(e.getHeader(str('variable_selling_billing_block'))),
                           'call_plan_id': str(e.getHeader(str('variable_call_plan_id'))),
                           'buy_rate': str(e.getHeader(str('variable_buy_rate'))),
                           'talking_blance': str(e.getHeader(str('variable_talking_blance'))),
                           'credit_balance': str(e.getHeader(str("variable_credit_blance"))),
                           'total_balance': str(e.getHeader(str('variable_total_balance'))),
                           'did_billing_type': str(e.getHeader(str('variable_did_billing_type'))),
                           'did_sell_rate': str(e.getHeader(str('variable_did_sell_rate'))),
                           'did_connect_charge': str(e.getHeader(str('variable_did_connect_charge'))),
                           'caller': str(e.getHeader(str('Caller-Caller-ID-Number'))),
                           'cust_id': str(e.getHeader(str('variable_cust_id'))),
                           'custom_hangup': str(e.getHeader(str('variable_custom_hangup'))),
    }  
    
    dlt_call = "delete from pbx_real_time_billing where uuid=\"{0}\"".format(call_hangup_dtl['core_uuid'])
    profile_info(dlt_call, 'insert', None)

    #print(f"application   {call_hangup_dtl['application']}  call_type- {call_hangup_dtl['call_type'] }   type_call {type_call}  custom_hangup {call_hangup_dtl['custom_hangup']}  ")
    if (type_call == "inbound" or type_call == "outbound") and call_hangup_dtl['application'] =="outbound":
     
    
        '''print(f" is_mnt_plan --->{call_hangup_dtl['is_mnt_plan']}  is_grp_mnt_plan -->{call_hangup_dtl['is_grp_mnt_plan']} caller -->{call_hangup_dtl['caller']}\
              \n  did_billing_type {call_hangup_dtl['did_billing_type']} did_connect_charge {call_hangup_dtl['did_connect_charge']}") '''


        if int(call_hangup_dtl['bridge_time']) != 0 and call_hangup_dtl['talking_mnt'] != '0':


            if call_hangup_dtl['is_mnt_plan'] == '1':
               # print(f"update minute plan  bridge_time {int(call_hangup_dtl['bridge_time']) }")
                billing_time=did_deduct_mnt(call_hangup_dtl['hangup_time'] ,call_hangup_dtl['bridge_time'],call_hangup_dtl['did_connect_charge'],call_hangup_dtl['did_billing_type'])
                
                if call_hangup_dtl['call_type'] == "click2call":
                 update_mnt_cdr="UPDATE pbx_realtime_cdr SET used_minutes = '{0}' WHERE uuid = '{1}' and src =\"{2}\" ".format(billing_time,call_hangup_dtl['core_uuid'] ,call_hangup_dtl['caller'] )
                else:
                 update_mnt_cdr = "UPDATE pbx_realtime_cdr SET used_minutes = '{0}' WHERE uuid = '{1}'" .format(billing_time,call_hangup_dtl['core_uuid'])
               
                profile_info(update_mnt_cdr, 'insert', None)

                update_mnt = "UPDATE pbx_call_plan_rates SET used_minutes = used_minutes+\"{0}\" WHERE id = \"{1}\"" \
                    .format(billing_time, call_hangup_dtl['call_plan_rate_mnt_id'])
                profile_info(update_mnt, 'insert', None)
         


            if call_hangup_dtl['is_mnt_plan'] == 'None':
                call_hangup_dtl['is_mnt_plan'] = call_hangup_dtl['is_grp_mnt_plan']
                


            if call_hangup_dtl['is_grp_mnt_plan'] == '1':

                #print(f'update group plan ***{call_hangup_dtl["core_uuid"]} \n')
                billing_time=did_deduct_mnt(call_hangup_dtl['hangup_time'] ,call_hangup_dtl['bridge_time'],call_hangup_dtl['did_connect_charge'],call_hangup_dtl['did_billing_type'])
                
                if call_hangup_dtl['call_type'] == "click2call":
                    update_mnt_cdr="UPDATE pbx_realtime_cdr SET used_minutes = '{0}' WHERE uuid = '{1}' and src =\"{2}\" ".format(billing_time,call_hangup_dtl['core_uuid'] ,call_hangup_dtl['caller'] )
                else:
                 update_mnt_cdr = "UPDATE pbx_realtime_cdr SET used_minutes = '{0}' WHERE uuid = '{1}'" .format(billing_time,call_hangup_dtl['core_uuid'])
                
                profile_info(update_mnt_cdr, 'insert', None)

                update_mnt = "UPDATE pbx_call_rate_group SET used_minutes = used_minutes+\"{0}\" WHERE id = \"{1}\"" \
                    .format(billing_time, call_hangup_dtl['group_id'])
                profile_info(update_mnt, 'insert', None)


            get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type,call_application," \
                       " server_details ,start_time from pbx_real_time_billing where" \
                       " customer_id=\"{0}\"  and billing_type=\"{1}\" " \
                       "desc ".format(call_hangup_dtl['customer_id'], call_hangup_dtl['billing_type'])
            live_call = profile_info(get_call, 'select', None)
            if len(live_call) > 0:
                if int(call_hangup_dtl['talking_mnt']) >= 1 and call_hangup_dtl['is_mnt_plan'] == '1':
                    if call_hangup_dtl['call_type'] == 'outbound' or call_hangup_dtl['application'] == 'outbound':
                        call_hangup_dtl['talking_mnt'] = int(call_hangup_dtl['talking_mnt']) - billing_time
                        call_deduct_mnt_outbound(call_hangup_dtl, live_call, 0)


        if int(call_hangup_dtl['bridge_time']) != 0 and call_hangup_dtl['billing_type'] == "3" :
            #print(f"outbound dial out billing " )

            billing_time = ((int(call_hangup_dtl['hangup_time']) - int(call_hangup_dtl['bridge_time'])) / 1000000)
            call_blnce = calc_dial_out_sec_to_charge(call_hangup_dtl['sell_rate'],
                                            call_hangup_dtl['selling_billing_block'], billing_time,call_hangup_dtl['billing_type'],call_hangup_dtl['did_connect_charge'])
            
         


            if call_hangup_dtl['call_type'] == "click2call":
              print(f"sessionbill click2call \n src -->{call_hangup_dtl['caller']}  call_type -{call_hangup_dtl['call_type'] }" )

              update_session_bill="update pbx_realtime_cdr set sessionbill= \"{0}\" where uuid=\"{1}\" and src =\"{2}\" ".format(str(call_blnce),call_hangup_dtl['core_uuid'] ,call_hangup_dtl['caller'] )
              
            else:
             update_session_bill="update pbx_realtime_cdr set sessionbill= \"{0}\" ,bridge_time= \"{2}\"  where uuid=\"{1}\"".format(str(call_blnce),call_hangup_dtl['core_uuid'],billing_time)
            
            query="update customer set balance=balance-\"{0}\" where id=\"{1}\"".format(str(call_blnce),call_hangup_dtl['customer_id'])
            profile_info(query, 'insert', None)
            profile_info(update_session_bill, 'insert', None)

            
            #print(f"call blance -->{call_blnce} total_balance -->{call_hangup_dtl['total_balance']}")
            deduct_balance(e, call_hangup_dtl, 1)
            print("hangup_event function")
 

    if  str(e.getHeader(str('variable_did_connect_charge'))) != "None" and  type_call =="inbound"  and call_hangup_dtl['application'] =="inbound":  
           
            #print(f"hangup_time {int(call_hangup_dtl['hangup_time'])}  bridge_time  {int(call_hangup_dtl['bridge_time'])}")  
            if int(call_hangup_dtl['bridge_time']) != 0 :
             billing_time = ((int(call_hangup_dtl['hangup_time']) - int(call_hangup_dtl['bridge_time'])) / 1000000)
             #print(f"INBOUND DID deduction  { str(e.getHeader(str('variable_did_connect_charge')))} billing_time  {billing_time} call_type {str(e.getHeader(str('variable_call_type')))}")  

             call_blnce = did_deduct_outbound(call_hangup_dtl['sell_rate'], call_hangup_dtl['did_connect_charge'] ,billing_time,call_hangup_dtl['did_billing_type'])
             print(f"call_blnce  --------->>>>>{call_blnce}  billing_time--> {billing_time } total bal {call_hangup_dtl['total_balance'] }")

             if float(call_hangup_dtl['total_balance']) < (call_blnce) and billing_time <0.5:
               call_blnce = 0

             
             update_session_bill="update pbx_realtime_cdr set sessionbill= \"{0}\" ,bridge_time= \"{2}\"  where uuid=\"{1}\"".format(str(call_blnce),call_hangup_dtl['core_uuid'],billing_time)
             profile_info(update_session_bill, 'insert', None)
             query="update customer set balance=balance-\"{0}\" where id=\"{1}\"".format(str(call_blnce),call_hangup_dtl['customer_id'])
             profile_info(query, 'insert', None)
             #print(f"call blance -->{call_blnce} total_balance -->{call_hangup_dtl['total_balance']}")


            """   deduct_balance_inbound(e, call_hangup_dtl, 1)
            print("hangup_event function") """
            


            
 

def event_destroy(e):
    pass
   


def shed_hangup(uuid, minute, ip_details):
    conn = ESLconnection(ip_details, '8002', 'ClueCon')
    if conn.connected():
        if minute < 0:
         print("uuid_kill %s allotted_timeout"%(uuid))   
         conn.execute("uuid_kill %s allotted_timeout"%(uuid)) 
        else:
         conn.execute("sched_hangup", "+" + str(minute) + "allotted_timeout", uuid)
        conn.disconnect() 

    

def call_deduct_mnt_outbound(call_data, live_call, i):
    if len(live_call) == 1 and i == 1:
        print("talk time  final minute ", call_data['talking_mnt'])
        talking_mnt = int(call_data['talking_mnt']) * 60
        print("caller",live_call)
        shed_hangup(call_data['core_uuid'], talking_mnt, call_data['server_details'])
    elif len(live_call) > 1 or i == 0:
        total_used_mnt = 0
        # rest_sec = [0]
        print("total mnt ", call_data['talking_mnt'])
        if i == 0:
            rest_sec = []
            start = 0
        else:
            rest_sec = [0]
            start = 1
        for index in range(start, live_call[0]['calls']):
            print(f" {datetime.datetime.now()} - {live_call[index-1]['start_time']} ")
            used_mnt = datetime.datetime.now() - live_call[index-1]['start_time']
            print(f" {used_mnt.days } * {seconds_in_day} + {used_mnt.seconds} ")
            total_sec = used_mnt.days * seconds_in_day + used_mnt.seconds
            total_mnt = math.ceil(total_sec / 60)
            rest_sec.append(60 - (divmod(total_sec, 60)[1]))
            total_used_mnt = total_used_mnt + total_mnt
            print(f" total_sec {total_sec}  total_mnt {total_mnt }  reset_sec {rest_sec} total_used_mnt {total_used_mnt}  taking mnt {call_data['talking_mnt']}")
       
        rest_mnt = int(call_data['talking_mnt'])-total_used_mnt 
        rest_mnt_test = (divmod(rest_mnt, live_call[0]['calls'])[1])
        rest_mnt = math.floor(rest_mnt / live_call[0]['calls'])
        print("rest mnt test", rest_mnt_test)
        print("rest_mnt", rest_mnt)
        if rest_mnt > 0:
            for row in range(0, live_call[0]['calls']):
                print("row index sheduling time", row)
                if rest_mnt_test > 0:
                    print("rest mnt test", rest_mnt_test)
                    rest_mnt_test -= 1
                    test = 1
                else:
                    test = 0
                mnt = int(rest_mnt) * 60 + int(rest_sec[row]) + test * 60
                print("restsec for single call", mnt)
                print(live_call[row]['uuid'], mnt, live_call[row]['server_details'])
                print('\n', "next", '\n')
                shed_hangup(live_call[row]['uuid'], mnt, live_call[row]['server_details'])
                #print(type(live_call[row]['uuid']), type(rest_mnt), type(live_call[row]['server_details']))
                # rest_mnt_test-=1
        elif rest_mnt <= 0:  

            conn = ESLconnection(call_data['server_details'], '8002', 'ClueCon')  
            if conn.connected():
               print("Connected to freeswitch 2 ")

               """  cmd =f"uuid_broadcast {call_data['core_uuid']}  /var/www/html/fs_backend/upload/def_prompts/ip_blocked.wav aleg" """
               print(f"No available minute rest_mnt {rest_mnt}  uuid {call_data['core_uuid']}  custom_hangup { str(e.getHeader('variable_custom_hangup'))}")
               conn.execute("sched_hangup", "+0 1006",call_data['core_uuid'])

               #con.execute("answer", "", call_data['core_uuid'])
               #con.execute("playback", "", call_data['core_uuid'])
               #con.bgapi(fedbck_strng + " &playback(/var/www/html/fs_backend/upload/def_prompts/ip_blocked.wav" + str(fedbck[i][6]))

               
               conn.disconnect()


def did_deduct_outbound(sell_rate,did_connect_chrg,bridge_time,did_bill_type):
    #print(f"DID  bill_type-->{did_bill_type}   sell_rate {sell_rate} bridge_time-->{bridge_time}  did_connect_chrg {did_connect_chrg}")

    if did_bill_type =='2' or did_bill_type =="4":
        total_rate =  float(did_connect_chrg)
    else:
        total_rate = math.ceil(float(bridge_time)/60)  * float(sell_rate)  +  float(did_connect_chrg)
    
    return total_rate



def deduct_balance(e, call_data, hangup_shed):


    if str(e.getHeader(str('variable_did_sell_rate'))) and  type_call =="inbound" and call_data['application'] == "inbound":
      get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type,caller," \
               "call_application,server_details ,start_time ,sell_rate,buy_rate,selling_min_duration," \
               "selling_billing_block from pbx_real_time_billing where " \
               "customer_id=\"{0}\" and  did_billing_type=\"{1}\"  " \
        .format(call_data['customer_id'], call_data['did_billing_type'])
    
    
    else:
        
       get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type,caller," \
               "call_application,server_details ,start_time ,sell_rate,buy_rate,selling_min_duration," \
               "selling_billing_block ,billing_type,did_connect_charge from pbx_real_time_billing where " \
               "customer_id=\"{0}\" and  billing_type=\"{1}\"  ORDER BY start_time DESC" \
        .format(call_data['customer_id'], call_data['billing_type'])
    
    
    live_call = profile_info(get_call, 'select', None)

    print(f"live calls {len(live_call)}  application  {call_data['application']}")

    if len(live_call) > 0:
        if hangup_shed==1:
          start=0
          reset_sec=[]
        else:
          start = 1
          reset_sec=[0]
          
        total_sec = 0
        consume_balance = 0
        #print(f"start  {start}    reset_sec  {reset_sec}")
        for index in range(start, len(live_call)):
         
            if hangup_shed ==1:
             #print("call disconnected uuid ",call_data['core_uuid'])   
             used_mnt_2 = datetime.datetime.now().replace(microsecond=0) - live_call[index]['start_time']
             sec = used_mnt_2.days * seconds_in_day + used_mnt_2.seconds
            else:
             used_mnt_2 =live_call[index-1]['start_time']  - live_call[index]['start_time']  
             sec = used_mnt_2.days * seconds_in_day + used_mnt_2.seconds
            reset_sec.append((sec%live_call[index]['selling_billing_block']))
            per_call_deduction = calc_dial_out_sec_to_charge(live_call[index]['sell_rate'],live_call[index]['selling_billing_block'], sec,live_call[index]['billing_type'],live_call[index]['did_connect_charge'])
            consume_balance = consume_balance + per_call_deduction
            total_sec = total_sec + sec
            print(f"per_call_deduction {per_call_deduction}, reset_sec {reset_sec}")
             
        reset_blance = float(call_data['total_balance']) - consume_balance
        per_call_blance = math.floor(reset_blance / live_call[0]['calls'])
        print(f" total bal {(call_data['total_balance'])}  reset bal {int(reset_blance)} per_call_blance {per_call_blance}")
                
        for row in range(len(live_call)):
             i = calc_dial_out_sec(live_call[row]['sell_rate'], live_call[row]['selling_billing_block'],
                                   per_call_blance)
             i=i+reset_sec[row] 
             print("reset_sec",i)
             if int(per_call_blance) < 0:
                print(f"should hangup now  uuid {live_call[row]['uuid']} ")
                shed_hangup(live_call[row]['uuid'],0, live_call[row]['server_details'])
             else:  
                shed_hangup(live_call[row]['uuid'], i, live_call[row]['server_details'])

          
""" 
def deduct_balance_inbound(e, call_data, hangup_shed):
    get_call = "select (select count(1) from pbx_real_time_billing) as calls,uuid,call_type,caller," \
               "call_application,server_details ,start_time ,sell_rate,buy_rate,selling_min_duration," \
               "selling_billing_block from pbx_real_time_billing where " \
               "customer_id=\"{0}\" and  did_billing_type=\"{1}\"  " \
        .format(call_data['customer_id'], call_data['did_billing_type'])

    live_call = profile_info(get_call, 'select', None)
    if len(live_call) == 1 and hangup_shed == 0:
        i = calc_dial_out_sec(call_data['sell_rate'], call_data['selling_billing_block'], call_data['total_balance'])
        print("caller who's on live_call ------->",live_call)
        shed_hangup(call_data['core_uuid'], i, call_data['server_details'])

    elif len(live_call) > 1 or (hangup_shed == 1 and len(live_call) > 0):
        if hangup_shed==1:
          start=0
          reset_sec=[]
        else:
          start = 1
          reset_sec=[0]
        total_sec = 0
        total_blance = 0
        print(f"live_call --------------->{len(live_call)}  did_billing_type {call_data['did_billing_type']}")
        #for index in range(start,len(live_call) - 1):
        for index in range(start, live_call[0]['calls']):
            used_mnt = datetime.datetime.now() - live_call[index]['start_time']
            sec = used_mnt.days * seconds_in_day + used_mnt.seconds
            reset_sec.append(int(live_call[index]['selling_billing_block'])-(sec%live_call[index]['selling_billing_block']))


            blance = calc_dial_out_sec_to_charge(live_call[index]['sell_rate'],live_call[index]['selling_billing_block'], sec,live_call[index]['did_billing_type'],live_call[index]['did_connect_charge'])
            print("reset sec",reset_sec)
            total_blance = total_blance + blance
            total_sec = total_sec + sec
            print(f"total balance -->{total_blance} second-->{total_sec}")
        reset_blance = float(call_data['total_balance']) - total_blance
        per_call_blance = math.floor(reset_blance / live_call[0]['calls'])


        for row in range(len(live_call)):
             i = calc_dial_out_sec(live_call[row]['sell_rate'], live_call[row]['selling_billing_block'],
                                   per_call_blance)
             i=i+reset_sec[row] 
             if int(per_call_blance) < 0:
                print(f"should hangup now  uuid {live_call[row]['uuid']} ")
                shed_hangup(live_call[row]['uuid'],0, live_call[row]['server_details'])
             else:  
                shed_hangup(live_call[row]['uuid'], i, live_call[row]['server_details'])
  """      

       


def calc_dial_out_sec(sell_rate, billing_block, balance):
    #print(f"{float(balance)} / {float(sell_rate)}")
    total_sec =math.floor(float(balance) / float(sell_rate))
    total_sec=total_sec*int(billing_block)-1
    return total_sec




def calc_dial_out_sec_to_charge(sell_rate, selling_billing_block, bridge_time,did_bill_type,did_connect_chrg):
    if did_bill_type =='2' or did_bill_type =="4":
     per_call_deduction =  float(did_connect_chrg)
    else:    
      count = math.ceil(float(bridge_time) / int(selling_billing_block))
      if did_connect_chrg != "None":
       per_call_deduction = count * float(sell_rate) +  float(did_connect_chrg)
      else:
       per_call_deduction = count * float(sell_rate)

    return per_call_deduction




def did_deduct_mnt(hangup_time,bridge_time,did_connect_chrg,did_billing_type):

    print(f" did_connect_chrg-->{did_connect_chrg}")
    if did_billing_type =='2' or did_billing_type =="4":
        billing_time =  float(did_connect_chrg)
    else:
        billing_time = ((int(hangup_time) - int(bridge_time)) / 1000000)
        if did_connect_chrg != "None":
         billing_time = math.ceil(billing_time / 60) + float(did_connect_chrg)
        else:
         print(billing_time)  
         if billing_time <= 0 :
            billing_time =0
         else:
          billing_time  = math.ceil(billing_time / 60)  
           

    #print(f" Minute billing_time-->{billing_time}")
    return billing_time 


# Esl Connection

con = ESL.ESLconnection(data['eslinfo']['ip'], data['eslinfo']['port'], data['eslinfo']['password'])
get_server_details()


if con.connected():
    con.events(str("json"), str("CHANNEL_CREATE"))
    con.events(str("json"), str("CHANNEL_ANSWER"))
    con.events(str("json"), str("CHANNEL_BRIDGE"))
    con.events(str("json"), str("CHANNEL_HANGUP"))
    con.events(str("json"), str("CHANNEL_HANGUP_COMPLETE"))
    con.events(str("json"), str("CHANNEL_DESTROY"))
    con.events(str("json"), str("SERVER_DISCONNECTED"))

    while 1:
        time.sleep(0.000000005)
        e = con.recvEvent()
        #print(e.serialize())
        if str(e.getHeader(str("Event-Name")))=='SERVER_DISCONNECTED':
         con = ESL.ESLconnection("127.0.0.1","8002","ClueCon")
         print("FREESWITCH_DISCONNECTED")
         
         type_call = e.getHeader(str("Caller-Direction"))
        if e:
           
            
           # Getting event type
           event_type = e.getType()
           con.events(str("json"), str("CHANNEL_CREATE"))
           con.events(str("json"), str("CHANNEL_ANSWER"))
           con.events(str("json"), str("CHANNEL_BRIDGE"))
           con.events(str("json"), str("CHANNEL_HANGUP"))
           con.events(str("json"), str("CHANNEL_DESTROY"))
           con.events(str("json"), str("SERVER_DISCONNECTED"))
           dial = "noanswer"
           type_call = e.getHeader(str("Caller-Direction"))
           if event_type == 'CHANNEL_CREATE':
               my_queue.put(e)
               thread1 = MyThread('first event thread')
               thread1.start()
           if event_type == 'CHANNEL_ANSWER':
               my_queue.put(e)
               thread2 = MyThread('sec event thread')
               thread2.start()
           if event_type == 'CHANNEL_BRIDGE':
               my_queue.put(e)
               thread3 = MyThread('third event thread')
               thread3.start()
           if event_type == 'CHANNEL_HANGUP':
               my_queue.put(e)
               thread4 = MyThread('fourth event thread')
               thread4.start()
           if event_type == 'CHANNEL_DESTROY':
               my_queue.put(e)
               thread5 = MyThread('fifth event thread')
               thread5.start()

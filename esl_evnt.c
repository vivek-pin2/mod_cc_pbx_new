#include "cc_pbx.h"
#include <switch_apr.h>






char  *c_time() {

char * res_tm;
char create_tm[50]={'\0'};
switch_time_exp_t tm;
switch_size_t retsize;
switch_time_t ts;
ts = switch_time_now();
switch_time_exp_lt(&tm, ts);
switch_strftime(create_tm, &retsize, sizeof(create_tm), "%Y-%m-%d %X", &tm);
res_tm = malloc(sizeof(char)*100);
strcpy(res_tm,create_tm);
//res_tm = create_tm;
//switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "c_time :%s", res_tm);
    return res_tm;
    free(res_tm);
}



void create_event(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex){
char* create_sql= NULL;
const char *uuid;
//switch_core_session_t *session = switch_channel_get_session(channel);
char result[50]={'\0'};

const char*  conf_id = switch_channel_get_variable(channel,"conf_id");
const char*  conf_name = switch_channel_get_variable(channel,"conf_name");
const char* clr = switch_channel_get_variable(channel,"sip_from_user");
const char* cle = switch_channel_get_variable(channel,"sip_req_user");
const char* clr_id = switch_channel_get_variable(channel,"sip_req_uri");
const char* event = switch_channel_get_variable(channel,"endpoint_disposition");
const char* admin = switch_channel_get_variable(channel,"participants_status");

uuid = switch_channel_get_uuid(channel);

                
        //switch_core_session_execute_application(session,"info","notice");
        switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE," conf_name %s & admin:%s  \t conf_time:%s \n",conf_name,admin,c_time());
       

if (!strcmp(event,"ANSWER"))
{ 

         create_sql = switch_mprintf("insert into pbx_conference_cdr (conf_id,participant_id,conf_name,caller,callee,participants_status,caller_id,uuid,session_start)\
         VALUES('%s', '%s','%s','%s','%s','%s','%s','%s',CURRENT_TIMESTAMP())",conf_id,call->conf.participant_id,conf_name,clr,cle,admin,clr_id,uuid);   
         execute_sql2str(dsn, mutex, create_sql, result, NELEMS(result));
         switch_safe_free(create_sql); 

}

}



void members_status(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex,const char *uuid){
char* sql= NULL;
//switch_core_session_t *session = switch_channel_get_session(channel);

char result[50]={'\0'};
//char count_live[50]={'\0'};
char participant_id[10]={'\0'};
const char* insta_id = switch_channel_get_variable(channel,"instance_id");
const char* member_status = switch_channel_get_variable(channel,"participants_status");
   
            switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, " member_status :%s  & Instance_id :%s ", member_status,insta_id);
          
            sql = switch_mprintf("SELECT (pcc.instance_id ) FROM `pbx_conference` as pc LEFT JOIN pbx_conference_participant as pcp \
            on pcp.conference_id = pc.id JOIN pbx_conference_cdr pcc on pcc.conf_id = pc.id WHERE pc.customer_id = %s  and pcc.participant_id = %s \
            AND pcc.participants_status like 'active_%%' ORDER by pcc.instance_id asc limit 1",call->conf.cust_id, call->conf.participant_id);   
            execute_sql2str(dsn, mutex, sql, participant_id, NELEMS(participant_id));
            //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " sql :%s \n  participant_id:%s ", sql,participant_id);

    
            if (atoi(participant_id )!= 0)
            {
            insta_id = participant_id;
            switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "  conference:%s  ", participant_id);
            }
            else
            {
            sql = switch_mprintf("UPDATE  `pbx_conference` SET status ='1',instance_id ='%s' where id ='%s' ",insta_id,call->conf.id);   
            execute_sql2str(dsn, mutex, sql, participant_id, NELEMS(participant_id));
            switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "confererce id  %s  sql %s",call->conf.id,sql);

            }
               
            sql = switch_mprintf("UPDATE `pbx_conference_cdr` SET participants_status = '%s',instance_id = '%s' \
            WHERE uuid = '%s'",member_status,insta_id,uuid);   
            execute_sql2str(dsn, mutex, sql, result, NELEMS(result));
            switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "sql:%s participant_id :%s    ",sql, participant_id);
            switch_safe_free(sql); 
         
}



void bridge_event(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex,const char *uuid){
char* sql= NULL;
char result[50]={'\0'};
char create_tm[50]={'\0'};
int diff_secs ,diff_mnts, diff_hrs ;
int crt_hr,crt_mnt, crt_sec,year,month,day;
int end_hr,end_mnt, end_sec,end_year,end_month,end_day;
const char*  member_status;


        sscanf(c_time(),"%d-%d-%d %d:%d:%d",&end_year,&end_month,&end_day,&end_hr, &end_mnt, &end_sec); 
        sql = switch_mprintf("SELECT session_start FROM `pbx_conference_cdr`  WHERE uuid ='%s' ",uuid);
        execute_sql2str(dsn, mutex, sql, create_tm, NELEMS(create_tm));
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "created_time :%s", create_tm); 
        sscanf(create_tm,"%d-%d-%d %d:%d:%d",&year,&month,&day,&crt_hr, &crt_mnt, &crt_sec); 

             
          if(crt_sec > end_sec)
         {
              end_sec +=60;
             --end_mnt;
         }
     
         if(crt_mnt > end_mnt)
         {
             crt_mnt +=60;
             --end_hr;
         }
     
     
         diff_secs = end_sec - crt_sec;
         diff_mnts = end_mnt - crt_mnt;
         diff_hrs = end_hr - crt_hr;

        
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " diff_secs :%d diff_mnts:%d  diff_hrs:%d and member_status: %s \n ", diff_secs,diff_mnts,diff_hrs, switch_channel_get_variable(channel,"participants_status"));
        if (strcmp(switch_channel_get_variable(channel,"participants_status"),"active_admin") == 0){
        switch_channel_set_variable(channel,"participants_status","admin");
        }
        else if (strcmp(switch_channel_get_variable(channel,"participants_status"),"active_member") == 0){
        switch_channel_set_variable(channel,"participants_status","member");
        }
         member_status =  switch_channel_get_variable(channel,"participants_status");

         sql = switch_mprintf("UPDATE `pbx_conference_cdr` SET bridge_time = '%d:%d:%d',session_end = '%s', participants_status = '%s'\
         WHERE uuid = '%s'", diff_hrs,diff_mnts,diff_secs, c_time(),member_status,uuid);   
         execute_sql2str(dsn, mutex, sql, result, NELEMS(result));
         switch_safe_free(sql); 
         

}


void destroy_event(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex){
char* sql= NULL;
const char* conf_id= switch_channel_get_variable(channel,"conf_id");
char dtry_sql[20] = {'\0'};
char count_live[20] = {'\0'};

       /* sql = switch_mprintf("call switch_live_pbx_conference_destroy('%s') ",conf_id); 
       execute_sql2str(dsn, mutex, sql, dtry_sql, NELEMS(dtry_sql));
       switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "destroy conf_id  %s ",conf_id); */


       sql = switch_mprintf("DELETE FROM pbx_conference_cdr WHERE instance_id = '0' or participants_status = '0' ");
       execute_sql2str(dsn, mutex, sql, dtry_sql, NELEMS(dtry_sql));
      
       sql = switch_mprintf("SELECT count(1)  FROM `pbx_conference_cdr` WHERE conf_id ='%s'  and participants_status LIKE 'active%%'",conf_id);
       execute_sql2str(dsn, mutex, sql, count_live, NELEMS(count_live));
       switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "destroy conf_id %s count_live %s ",conf_id,count_live);
       
       if (!atoi(count_live)){
       sql = switch_mprintf("UPDATE  `pbx_conference` SET status ='0' WHERE id = '%s'",conf_id);
       execute_sql2str(dsn, mutex, sql, count_live, NELEMS(count_live));
          

       }
       switch_safe_free(sql); 




}   

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
switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "c_time :%s", res_tm);
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

                
       // switch_core_session_execute_application(session,"info","notice");
        switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"strcmp Event:%d \n conf_name %s & admin:%s \t \n tims_sql:%s \n",strcmp(event,"ANSWER"),conf_name,admin,c_time());
       

if (strcmp(event,"ANSWER") == 0)
{

         create_sql = switch_mprintf("insert into pbx_conference_cdr (conf_id,participant_id,conf_name,caller,callee,participants_status,caller_id,uuid,session_start)\
         VALUES('%s', '%s','%s','%s','%s','%s','%s','%s',CURRENT_TIMESTAMP())",conf_id,switch_channel_get_variable(channel,"participant_id_conf"),conf_name,clr,cle,admin,clr_id,uuid);   

          execute_sql2str(dsn, mutex, create_sql, result, NELEMS(result));
          switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " create_sql :%s \n conf_id:%s & event_name:%s   ", create_sql,conf_id,event);
          switch_safe_free(create_sql); 

}

}



void members_status(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex,const char *uuid){
char* create_sql= NULL;

char result[50]={'\0'};
const char* member_status = switch_channel_get_variable(channel,"participants_status");
   
         switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " member_status :%s  & Instance_id :%s ", member_status,switch_channel_get_variable(channel,"instance_id"));
     
         create_sql = switch_mprintf("UPDATE `pbx_conference_cdr` SET participants_status = '%s',\
         instance_id = '%s' WHERE uuid = '%s'",member_status,switch_channel_get_variable(channel,"instance_id"),uuid);   

          execute_sql2str(dsn, mutex, create_sql, result, NELEMS(result));
          switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " create_sql :%s  ", create_sql);
          switch_safe_free(create_sql); 
         
}



void bridge_event(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex,const char *uuid){
char* create_sql= NULL;
char* sql= NULL;
char result[50]={'\0'};
char create_tm[50]={'\0'};
int diff_secs ,diff_mnts, diff_hrs ;
int crt_hr,crt_mnt, crt_sec,year,month,day;
int end_hr,end_mnt, end_sec,end_year,end_month,end_day;
const char*  member_status;



// session_end
      sscanf(c_time(),"%d-%d-%d %d:%d:%d",&end_year,&end_month,&end_day,&end_hr, &end_mnt, &end_sec); 
      switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " end_hr:%d   end_mnt:%d  end_sec:%d \n", end_hr,end_mnt,end_sec); 

        sql = switch_mprintf("SELECT session_start FROM `pbx_conference_cdr`  WHERE uuid ='%s' ",uuid);
        execute_sql2str(dsn, mutex, sql, create_tm, NELEMS(create_tm));
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " sql :%s  ", create_tm);
        switch_safe_free(sql); 
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "created_time :%s", create_tm); 

//session_create
     sscanf(create_tm,"%d-%d-%d %d:%d:%d",&year,&month,&day,&crt_hr, &crt_mnt, &crt_sec); 
     switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " crt_hr:%d   crt_mnt:%d  crt_sec:%d \n", crt_hr,crt_mnt,crt_sec);

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

        
         switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " diff_secs :%d diff_mnts:%d  diff_hrs:%d and member_status: %s \n ", diff_secs,diff_mnts,diff_hrs, switch_channel_get_variable(channel,"participants_status"));
        if (strcmp(switch_channel_get_variable(channel,"participants_status"),"active_admin") == 0){
        switch_channel_set_variable(channel,"participants_status","admin");
        }
        else if (strcmp(switch_channel_get_variable(channel,"participants_status"),"active_member") == 0){
        switch_channel_set_variable(channel,"participants_status","member");
        }
         member_status =  switch_channel_get_variable(channel,"participants_status");
         switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "  member_status: %s \n ",member_status);

         create_sql = switch_mprintf("UPDATE `pbx_conference_cdr` SET bridge_time = '%d:%d:%d',session_end = '%s', participants_status = '%s'\
          WHERE uuid = '%s'", diff_hrs,diff_mnts,diff_secs, c_time(),member_status,uuid);   

         execute_sql2str(dsn, mutex, create_sql, result, NELEMS(result));
         switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " create_sql :%s  ", create_sql);
         switch_safe_free(create_sql); 
         

}


void destroy_event(switch_channel_t * channel,call_details_t *call, char *dsn, switch_mutex_t *mutex){

char* instance_count_sql= NULL;
char instance_count[20] = {'\0'};

       instance_count_sql = switch_mprintf("DELETE FROM pbx_conference_cdr WHERE instance_id = 0 or participants_status = 0 "); 
       execute_sql2str(dsn, mutex, instance_count_sql, instance_count, NELEMS(instance_count));
       switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " Instance_count_sql :%s: ", instance_count_sql);
           


}  
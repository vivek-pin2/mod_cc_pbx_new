/*
 * Freeswitch modular soft-switch application
 * All Rights Reserved © 2019 CloudConnect Communication Pvt. Ltd.
 *
 * The Initial Developer of the Original Code is
 * Ravindrakumar D. Bhatt <ravindra@cloud-connect.in>.
 * Contribution Event handler : Vivek Negi <vivek.negi@cloud-connect.in>.
 *
 * mod_cc_pbx.c --Implements broadcast based conference APP for outbound
 * trunk dailing
 *
 */

#include "cc_pbx.h"

#define xml_safe_free(_x) if (_x) switch_xml_free(_x); _x = NULL

SWITCH_MODULE_LOAD_FUNCTION(mod_cc_pbx_load);
SWITCH_MODULE_SHUTDOWN_FUNCTION(mod_cc_pbx_shutdown);
SWITCH_MODULE_DEFINITION(mod_cc_pbx, mod_cc_pbx_load, mod_cc_pbx_shutdown, NULL);


static const char *global_cf = "cc_pbx.conf";

static struct {
    char *odbc_dsn;
    char *real_path;
    char* custom_path;
    char* opsip_ip_port;

    switch_mutex_t *mutex;
    switch_memory_pool_t *pool;

} globals;

//void event_handler(switch_event_t *event);

static switch_status_t load_config(void){
    switch_xml_t xml,cfg,settings,param;
    switch_status_t status = SWITCH_STATUS_SUCCESS;

    if(!(xml = switch_xml_open_cfg(global_cf,&cfg,NULL))){
        switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_ERROR,"Open if %s failed.\n",global_cf);
        return SWITCH_STATUS_TERM;
    }



    if((settings = switch_xml_child(cfg,"settings"))){
       for(param = switch_xml_child(settings,"param");param;param = param->next){
            char *var = (char *) switch_xml_attr_soft(param, "name");
            char *val = (char *) switch_xml_attr_soft(param, "value");
            if(!strcasecmp(var,"odbc-dsn")){
                globals.odbc_dsn = strdup(val);
            }
            else if(!strcasecmp(var,"real_path")){
                globals.real_path = strdup(val);
            } 
            else if(!strcasecmp(var,"custom_prompt")){
                globals.custom_path = strdup(val);
            } 
            else if(!strcasecmp(var,"opsip_ip_port")){
                globals.opsip_ip_port = strdup(val);
            } 
            else{
                status = SWITCH_STATUS_TERM;
            }
       } 
    }

    xml_safe_free(xml);
    return status;
}






SWITCH_STANDARD_APP(cc_pbx_function){
    

    switch_status_t status = SWITCH_STATUS_SUCCESS;
    const char* dialstatus;
    char * temp_path=NULL;
    switch_channel_t * channel = switch_core_session_get_channel(session);
    //switch_call_cause_t cause = SWITCH_CAUSE_NORMAL_CLEARING;
 
 call_details_t call = {{0},{0},{0},{0},{0},{0},{0},{0},{0},{0},{0},{0}};
    if( ( status = handle_call(channel,globals.odbc_dsn,globals.mutex,globals.real_path,globals.custom_path,globals.opsip_ip_port,&call ) ) != SWITCH_STATUS_SUCCESS ){

	switch_channel_hangup(channel,SWITCH_CAUSE_CALL_REJECTED);
        return ;
    }

    // if callee is our  systems extension than only execute below logic for other type goto end
    dialstatus = switch_channel_get_variable(channel,"DIALSTATUS");
    switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_ERROR,"Hangup cause: %s\n",dialstatus);  
    if( dialstatus!=NULL  &&!strcmp(dialstatus,"GATEWAY_DOWN")  ){
	            sleep(2);
                    switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_ERROR," cause: %s\n",dialstatus);
                    temp_path = switch_mprintf("%s%s", globals.real_path, "gateway_down.wav");
                    switch_ivr_play_file(session, NULL, temp_path, NULL);
                    switch_safe_free(temp_path);
    }
     return;
}


SWITCH_MODULE_LOAD_FUNCTION(mod_cc_pbx_load)
{
    switch_application_interface_t *app_interface;
//  switch_api_interface_t *commands_api_interface;
    switch_status_t status;

    *module_interface = switch_loadable_module_create_module_interface(pool, modname);

    memset(&globals,0,sizeof(globals));
    globals.pool = pool;

    switch_mutex_init(&globals.mutex,SWITCH_MUTEX_NESTED,globals.pool);

    if( (status = load_config()) != SWITCH_STATUS_SUCCESS ){
        return status;
    }

    /*  if (switch_event_bind("mod_cc_pbx", SWITCH_EVENT_ALL , SWITCH_EVENT_SUBCLASS_ANY, event_handler,NULL) != SWITCH_STATUS_SUCCESS) {
   switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "Cannot bind to event handler!\n"); 

		return SWITCH_STATUS_TERM;
	} */

    SWITCH_ADD_APP(app_interface, "cc_pbx", "cc_pbx", "cc pbx application", cc_pbx_function, NULL, SAF_NONE);

    return SWITCH_STATUS_SUCCESS;
}

SWITCH_MODULE_SHUTDOWN_FUNCTION(mod_cc_pbx_shutdown)
{

    //switch_event_unbind_callback(event_handler);
    switch_safe_free(globals.odbc_dsn);
    switch_safe_free(globals.real_path);
    switch_mutex_destroy(globals.mutex);
    return SWITCH_STATUS_SUCCESS;

}



/*  void  event_handler(switch_event_t *event) {  

     char *buf;
     
     switch_event_serialize(event, &buf, SWITCH_TRUE);
  	switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_CONSOLE, "\nEVENT (text version)\n--------------------------------\n%s", buf);
   
 }
 */

// void  event_handler(switch_event_t *event) {  
//  
//       char *query= NULL;
//    
//       
//       const char *event_name = switch_event_get_header_nil(event, "Event-Name");
//       const char *type_call = switch_event_get_header_nil(event, "variable_direction");
//       const char *call_type= switch_event_get_header_nil(event, "variable_call_type");  
//       char *core_uuid= switch_event_get_header_nil(event, "Core-UUID"); 
//    
//      char *ref_id = switch_event_get_header_nil(event, "variable_ref_id"); 
//      char *application = switch_event_get_header_nil(event, "variable_application"); 
// 
//
//
//   /*--------------------------------------------------------------------CHANNEL_CREATE --------------------------------------------------*/
//    if (!strcasecmp(event_name,"CHANNEL_CREATE") ){
//
//         if ( !strcmp(type_call,"inbound")  || !(strcmp(call_type,"click2call")  && !strcmp(type_call,"outbound") )){
//       /*    query  = switch_mprintf("INSERT INTO cc_pbx_cdr (uuid,src,dst,sip_current_application,ip,current_status,callerid,direct_gateway) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s')",  
//              core_uuid,
//              src,
//              dest,
//              type_call,
//              switch_event_get_header_nil(event, "Caller-Network-Addr"),
//              switch_event_get_header_nil(event, "Answer-State"),
//              switch_event_get_header_nil(event, "variable_sip_req_uri"),
//              switch_event_get_header_nil(event, "variable_sip_gateway_name")
//              );
//              execute_sql(globals.odbc_dsn, query, globals.mutex);
//              switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "Create event  query:%s  \n",query);
//              switch_safe_free(query);
//
//
//*/
//    }}
//    
//   /*--------------------------------------------------------------------CHANNEL_ANSWER --------------------------------------------------*/
//  
//    if (!strcasecmp(event_name,"CHANNEL_ANSWER")){
//  
//     if ( !strcmp(type_call,"outbound")){
//    
//         query  = switch_mprintf("update cc_pbx_cdr set clr_read_codec='%s',clr_write_codec='%s' where uuid='%s'",  
//             switch_event_get_header_nil(event, "Channel-Read-Codec-Name"),
//             switch_event_get_header_nil(event, "Channel-Write-Codec-Name"),
//             core_uuid); 
//             execute_sql(globals.odbc_dsn, query, globals.mutex);
//             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " ANSWER  event query:%s  \n",query);
//
//             switch_safe_free(query);
//     }

 /*     if ( !strcmp(type_call,"inbound")  || !(strcmp(call_type,"click2call")  && !strcmp(type_call,"outbound"))){
    
         query  = switch_mprintf("update cc_pbx_cdr set \
             current_status='%s',ip_internal='%s' , codec='%s' ,latitude='NULL',\
             call_type ='%s',sip_current_application='%s',cle_read_codec='%s',cle_write_codec='%s',ref_id='%s' where uuid='%s'",  
                    event_name,
                    switch_event_get_header_nil(event, "Caller-Network-Addr"),
                    switch_event_get_header_nil(event, "variable_originator_codec"),                   // let,
                    call_type,
                    switch_event_get_header_nil(event, "variable_application"),
                    switch_event_get_header_nil(event, "variable_read_codec"),
                    switch_event_get_header_nil(event, "variable_write_codec"),
                    ref_id,
                    core_uuid
                    );
             execute_sql(globals.odbc_dsn, query, globals.mutex);
             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " ANSWER  event query:%s  \n",query);
             switch_safe_free(query);
     }
 */
        /*  
       if( !strcmp(application,"inbound")){
            query  = switch_mprintf("update cc_pbx_cdr set \
             current_status='%s',ip_internal='%s' , codec='%s' ,latitude='NULL',\
             call_type ='%s',sip_current_application='%s',cle_read_codec='%s',cle_write_codec='%s',ref_id='%s' where uuid='%s'",  
                    event_name,
                    switch_event_get_header_nil(event, "Caller-Network-Addr"),
                    switch_event_get_header_nil(event, "variable_originator_codec"),
                    // let,
                    call_type,
                    switch_event_get_header_nil(event, "variable_application"),
                    switch_event_get_header_nil(event, "variable_read_codec"),
                    switch_event_get_header_nil(event, "variable_write_codec"),
                    ref_id,
                    core_uuid);
             execute_sql(globals.odbc_dsn, query, globals.mutex);
             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " ANSWER  event query:%s  \n",query);
             switch_safe_free(query);
       

        }

    } */


    
     /*--------------------------------------------------------------------CHANNEL_BRIDGE --------------------------------------------------*/
/* 
    if (!strcasecmp(event_name,"CHANNEL_BRIDGE")){

       


     country_code = switch_event_get_header_nil(event, "variable_dial_prefix"); 
     cle_uuid     = switch_event_get_header_nil(event, "Bridge-B-Unique-ID"); 
     forward      = switch_event_get_header_nil(event, "Caller-Callee-ID-Number"); 
     ip_internal  = switch_event_get_header_nil(event, "variable_sip_from_host"); 
      
    if ( !strcmp(type_call,"inbound")  || !(strcmp(call_type,"click2call")  && !strcmp(type_call,"outbound") )){


    }

     if ( !strcmp(call_type,"outbound") || !strcmp(call_type,"click2call") ){

         query  = switch_mprintf("update cc_pbx_cdr set \
             direct_gateway='%s',cle_uuid='%s' ,buy_cost='%s',sell_cost='%s',\
             id_callplan='%s' , destination='%s' ,current_status='%s'  ,forward ='%s',ip_internal ='%s',\
             sip_current_application ='%s',customer_id='%s',clr_read_codec='%s'\
             ,clr_write_codec='%s' where uuid='%s'",  
                    gateway_grp,
                    cle_uuid,
                    buy_cost,
                    sell_cost,
                    call_plan,
                    country_code,
                    event_name,
                    forward,
                    ip_internal,
                    call_type,
                    cust_id,
                    caller_read_codec,
                    caller_write_codec,
                    core_uuid);
             execute_sql(globals.odbc_dsn, query, globals.mutex);
             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " Bridge  event query:%s  \n",query);
             switch_safe_free(query);
     }
           
      else if (!strcasecmp(application,"inbound") || !strcasecmp(application,"intercom")){

         query  = switch_mprintf("update cc_pbx_cdr set \
             cle_uuid='%s',current_status='%s'  ,forward ='%s',\
             sip_current_application ='%s',buy_cost='%s',sell_cost='%s',customer_id='%s',clr_read_codec='%s'\
             ,clr_write_codec='%s' where uuid='%s'",  
                    cle_uuid,
                    event_name,
                    forward,
                    call_type,
                    buy_cost,
                    sell_cost,
                    cust_id,
                    caller_read_codec,
                    caller_write_codec,
                    core_uuid);
             execute_sql(globals.odbc_dsn, query, globals.mutex);
             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " Bridge  event query:%s  \n",query);
             switch_safe_free(query);
      }
    

//feedback_cdr

     if (!strcasecmp(call_type,"call_queue") || !strcasecmp(application,"call_sticky_agent") || !strcasecmp(application,"call_cg_sticky_agent") || !strcasecmp(application,"call_group")){
               
      
            feedback =  switch_mprintf("insert into pbx_feedback(uuid,src,dst,customer_id,forward,ref_id )values('%s','%s','%s','%s','%s','%s'",
                core_uuid,
                src,
                dest,
                cust_id,
                forward,
                ref_id,
            );
             execute_sql(globals.odbc_dsn, feedback, globals.mutex);
             switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " Bridge  event feedback query:%s  \n",query);
             switch_safe_free(feedback);
    }
    }
 
}
*/

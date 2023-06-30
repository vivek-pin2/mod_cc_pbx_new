#include "cc_pbx.h"


switch_status_t handle_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, char *opsip_ip_port,call_details_t *call)
        {    

        switch_status_t status = SWITCH_STATUS_SUCCESS;
        switch_core_session_t *session = switch_channel_get_session(channel);
        const char *opsp_ip = switch_channel_get_variable(channel, "sip_network_ip");
        const char *opsp_port = switch_channel_get_variable(channel, "sip_network_port");
        const char *caller = switch_channel_get_variable(channel, "ani");
        const char *call_type = switch_channel_get_variable(channel, "call_type");
        const char *fd_id = switch_channel_get_variable(channel, "fd_id");
        const char *cust_id = switch_channel_get_variable(channel, "cust_id");
        const char *sip_h_X = switch_channel_get_variable(channel, "sip_h_X-switch");
        const char *callee = switch_channel_get_variable(channel, "destination_number");
        
        char id[20],did_call[2],gw_limit[2] = {'\0'};

        char *data;
        char *temp_path;
        char **tokl =NULL;
        int num;
        const static char* clr_uuid;
        call->flags.recording_path = "/var/www/html/fs_backend/upload";

        switch_channel_set_variable(channel, "opsip_ip_port",opsip_ip_port);
        switch_channel_set_variable(channel, "application", "intercom");
        
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "Caller :%s  %s", caller,sip_h_X);
        switch_core_session_execute_application(session,"bind_meta_app","1 b s valet_park::my_lot auto in 5901 5999");
        switch_core_session_execute_application(session,"bind_meta_app","2 b s fifo::80@$${domain} in undef local_stream://moh");
       // switch_core_session_execute_application(session, "info",NULL);


            
        if (!IS_NULL(caller))
        {  
         
        if (get_ext_details(channel, &call->caller, dsn, mutex, caller))
        {
        switch_channel_set_variable(channel, "cust_id",call->caller.cust_id);
        }
        
        if (!(call->caller.is_multi_registration)) 
        {
        data =switch_mprintf("hash ${domain} $%s 100 ",caller);
        switch_core_session_execute_application(session,"limit",data); 
        if (!IS_NULL(switch_channel_get_variable(channel, "limit_usage"))){
        if (atoi(switch_channel_get_variable(channel, "limit_usage")) == 1)
        {
        clr_uuid = switch_channel_get_variable(channel, "call_uuid");
        }

        if (atoi(switch_channel_get_variable(channel, "limit_usage")) >= 2 )
        {
        switch_channel_set_variable(channel, "limit_usage", "2");
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "clr_uuid:%s",clr_uuid);
        temp_path = switch_mprintf("ringback=%s%s", path, "busy_on_another_call.wav");
        switch_core_session_execute_application(session, "set", temp_path);
        }
        }
        }
        else
        {
        switch_channel_set_variable(channel, "limit_usage", "0");
        }

        if (!IS_NULL(call_type))
        {
        if (!strcmp(call_type, "call_feedback"))
        {
        struct stack *pt = newStack(5);
        switch_channel_set_variable(channel, "sip_network_ip", opsp_ip);
        switch_channel_set_variable(channel, "sip_network_port", opsp_port);
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        call->did.dst_id = atoi(fd_id);
        call->did.cust_id = (char *)cust_id;
        call->did.is_init = true;
        handle_ivr(channel, dsn, mutex, path,custom_path,call, pt, 1);
        switch_channel_set_variable(channel, "application", "outbound");
        return status;
        }
        } }
       
        else
        {

        if (!IS_NULL(call_type))
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "Api call_type:%s  ",call_type); 
        if (!strcmp(call_type, "call_feedback"))
        {
        struct stack *pt = newStack(5);
        handle_ivr(channel, dsn, mutex, path,custom_path,call, pt, 1);
         return status; 
        }
        if (!strcmp(call_type, "call_plugin")  && !IS_NULL(switch_channel_get_variable(channel, "plugin_data")))
        {
        temp_path = switch_mprintf("%s%s", path, "thankyou_selfcare.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        data =switch_mprintf("%s", switch_channel_get_variable(channel, "plugin_data")); 
        tokl = split(data, &num, "_",channel);
        handle_plugin_call(channel,dsn,mutex,path,custom_path,call,tokl,caller);
        return status; 
        }
        }}
        
        
 
        if ((is_black_listed(channel, dsn, mutex, call,call->caller.num)))
        {
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "call_blacklist.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }



        if ( callee != NULL && callee[0] == '*'){
        switch_core_session_execute_application(session, "set", "ringback=%(2000,4000,440.0,480.0)");
        switch (strlen(callee))
        {
        case 2:
        if (callee[0] != '*')
        {
        temp_path = switch_mprintf("%s%s", path, "please_check_number_try_again.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }

        if (call->caller.is_sd_allowed == true)
        {
        switch_channel_set_variable(channel, "call_type", "call_speeddial");
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        handle_sd(channel, dsn, mutex,path,custom_path ,call);
        }
        else
        { 
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }
        break;
        case 3:
        if (callee[0] != '*')
        {
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        break;
        }

        if (call->caller.is_init)
        {
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        feature_code(session, callee, caller, call, dsn, mutex,path,custom_path);
        }
        break;


        case 5:
        if (call->caller.is_init)
        {
        switch_channel_set_variable(channel, "call_type", "call_valetpark");
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        valetpark(session, callee);
        }
        break;
        default:
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "feature_code_not_available.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        status = SWITCH_STATUS_FALSE;
        return false;
        } 
        } 




        if ( !IS_NULL(callee)  && callee[0] != '*' )
        {

         
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " Incoming callee :%s",callee);


      /*        if (!IS_NULL(switch_channel_get_variable(channel, "patch_data")))
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "  patch_data :%s",callee);
        call->flags.is_call_outbound = true;
        switch_core_session_execute_application(session, "set", "ringback=%(2000,4000,440.0,480.0)");
        if (dialoutrule(channel, dsn, mutex,path ,custom_path,call,callee) && outbound(session, dsn, mutex, path, custom_path, call, callee))
        {
        if (call->obd.is_init || call->flags.is_outbound_mnt ||  call->flags.is_outbound_grp_mnt )
        { 
        bridge_call(session, call, callee,dsn,mutex);    
        }
        else
        { 
        switch_channel_set_variable(channel, "custom_hangup","1012");
        } 
        }
         return true;    
        }
         */
        if (callee[0]=='p'){ 
        data =switch_mprintf("%s", callee); 
        tokl = split(data, &num, "_",channel);
        if (!(strcasecmp(tokl[0],"plugin"))) 
        { 
        //handle_plugin
        handle_plugin_call(channel,dsn,mutex,path,custom_path,call,tokl,caller);
        }
        }

        else if ((callee[0] >= 48 && callee[0] <= 57) || callee[0] == 43) 
        {
         
        if ( (atoi(callee) >= 100 && atoi(callee) <= 199)  || strlen(callee) == 1)
        { 
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "not_authorized_to_dial.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;

        } 

        if (strlen(callee) >= 2 && strlen(callee)  <=4 )
        {
        callee = switch_mprintf("%s%s", call->caller.cust_id, callee);
        } 

        else if (strlen(callee) == 5){
        if (get_ext_details(channel, &call->callee, dsn, mutex, callee)  && (call->callee.is_init))
        {  
        switch_channel_set_variable(channel, "call_type", "sip_extn");
        if (!handle_sip_call(channel, dsn, mutex, path, custom_path, call))
        {
        status = SWITCH_STATUS_FALSE;
        }
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;

        }

        else  if (verify_internal_exten(channel, dsn, mutex, call, callee,path))
        {       
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "Feature call::%s",callee);
        switch_core_session_execute_application(session, "set", "ringback=%(2000,4000,440.0,480.0)");
        call->flags.is_call_internal = true;
        if (call->cg.is_init)
        {
        handle_cg(channel, call, dsn, mutex,path,custom_path);
        }
        else if (call->conf.is_init)
        {
        handle_conf(channel,call,dsn,mutex, path, custom_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);  
        return false;         

        }
        handle_prompt(channel,switch_channel_get_variable(channel, "DIALSTATUS"), path, custom_path);  

        }
        else
        {

        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "feature_code_not_available.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }

        }

        else if (call->caller.cust_id != NULL && !strncmp(callee,call->caller.cust_id,strlen(call->caller.cust_id))){
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "SIP TRANSFER:%s",callee);

        }
        else if (get_ext_details(channel, &call->callee, dsn, mutex, callee))
        {

        if (call->callee.is_init)
        {
        switch_channel_set_variable(channel, "call_type", "sip_extn");
        switch_channel_set_variable(channel, "sip_req_user", callee);
        if (!handle_sip_call(channel, dsn, mutex, path, custom_path, call))
        status = SWITCH_STATUS_FALSE;

        }
        }
        
        else
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "PSTN TRANSFER:%s",callee);
        if (verify_did(channel, dsn, mutex, &call->did))
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "DID CALL %d  caller :%d", call->did.is_init,call->caller.is_init );
        {
        switch_channel_set_variable(channel, "cust_id",call->did.cust_id);
        if (call->did.actv_ftr_id <=2 && call->did.actv_ftr_id >=9){
        switch_channel_answer(channel);
        }
        sprintf(id, "%d", call->did.id);
        switch_channel_set_variable(channel, "cust_id", call->did.cust_id);
        sprintf(did_call, "%d", call->did.is_init);
        switch_channel_set_variable(channel, "did_call", did_call);
        switch_channel_set_variable(channel, "application", "inbound");
        switch_channel_set_variable(channel, "callee", "inbound");
        switch_channel_set_variable(channel, "sell_rate", call->did.selling_rate);
        switch_channel_set_variable(channel, "billing_type", call->did.bill_type);
        switch_channel_set_variable(channel, "connect_chrg", call->did.conn_charge);
        switch_channel_set_variable(channel, "provider_id", id);

        if ((is_black_listed(channel, dsn, mutex, call,caller)))

        {
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "call_blacklist.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }

        handle_did_dest(channel, dsn, mutex, path,custom_path,call);

        }
        }

        else if (dialoutrule (channel, dsn, mutex,path ,custom_path,call,callee))
        {

        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "CALL TYPE : OUTBOUND  : %d  mnt:%d ",call->caller.is_outbound_allowed, call->caller.is_mnt_plan_enabled );   
        (call->caller.is_outbound_allowed == 0) ? call->caller.is_outbound_allowed  = call->caller.is_mnt_plan_enabled :call->caller.is_outbound_allowed ;

        if (call->caller.is_outbound_allowed )
        {
        switch_channel_set_variable(channel, "call_type", "outbound");
        switch_channel_set_variable(channel, "application", "outbound");
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        //callee=call->callee.dout_num;

        call->flags.is_call_outbound = true;
        if (outbound(session, dsn, mutex,path,custom_path ,call, callee) == false)
        {
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return SWITCH_STATUS_FALSE;
        return false;
        }

        (call->obd.gwty_status == 0) ? call->obd.gwty_status = call->mnt.gwty_status : call->obd.gwty_status;
        (call->obd.is_init == 0) ? call->obd.is_init = call->mnt.is_init : call->obd.is_init;

        if (!(call->obd.gwty_status) && call->obd.is_init)
        {
        switch_channel_set_variable(channel, "custom_hangup","1015");
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);

        }
        else if(call->obd.is_init)
        {

        (call->obd.gw_id  == NULL) ? call->obd.gw_id = call->mnt.gw_id : call->obd.gw_id ;

        if (call->obd.gw_id != 0 ){
        data= switch_mprintf("call switch_verify_gateway_concurrent_limit(%s)",call->obd.gw_id);
        execute_sql2str(dsn, mutex, data,gw_limit , NELEMS(gw_limit));
        if (atoi(gw_limit) == 1)
        {

        temp_path = switch_mprintf("%s%s", path, "gw_limit_exhx.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_set_variable(channel, "custom_hangup","1001");
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }
        else
        {
        if (call->caller.is_recording_allowed)
        {
        set_recording(channel, "Outbound Call", call, dsn, mutex,path,custom_path);
        }
        bridge_call(session, call, callee,dsn,mutex);       
        }

        }

        }

        else if (!call->obd.is_init  &&  !(call->flags.is_roaming))
        {    
        switch_channel_set_variable(channel, "custom_hangup","1012");
        temp_path = switch_mprintf("%s%s", path, "dialout_rate_missing.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        return 0;

        }
        else 
        { 
        sleep(0.5);
        switch_channel_set_variable(channel, "custom_hangup","1010");
        temp_path = switch_mprintf("%s%s", path, "roaming_expired.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        return 0;
        }
        }
        else
        {
        sleep(0.5);
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "NO  OUTBOUND  : %d  mnt:%d ",call->caller.is_outbound_allowed, call->caller.is_mnt_plan_enabled );   
        switch_channel_set_variable(channel, "custom_hangup","1017");
        temp_path = switch_mprintf("%s%s", path, "dialout_disable.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        return 0;
        }
        }
         //switch_core_session_execute_application(session, "info",NULL);
         switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " Blind transfer :%s ",switch_channel_get_variable(channel, "sip_h_Referred-By"));
         if (!IS_NULL(switch_channel_get_variable(channel, "sip_h_Referred-By")))
        { 
        call->flags.is_call_outbound = false;
        callee= switch_channel_get_variable(channel, "destination_number");
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "transfer_destination:%s  ",callee);
        
        if ( (atoi(callee) >= 100 && atoi(callee) <= 199)  || strlen(callee) == 1)
        { 
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "not_authorized_to_dial.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        } 

        else if (strlen(callee) >= 2 && strlen(callee)  <=4 )
        {
        switch_channel_set_variable(channel, "sip_h_X-calleetype", "cc-ecpl");
        callee = switch_mprintf("%s%s", call->caller.cust_id, callee);
        } 
        
        else if (get_ext_details(channel, &call->callee, dsn, mutex, callee) && call->callee.is_init)
        {
        switch_channel_set_variable(channel, "call_type", "sip_extn");
        switch_channel_set_variable(channel, "sip_req_user", callee);
        handle_sip_call(channel, dsn, mutex, path, custom_path, call);
        return true;
        }
        
        else
        {
        call->flags.is_call_outbound = true;
        dialoutrule(channel, dsn, mutex,path ,custom_path,call,callee);
        outbound(session, dsn, mutex, path, custom_path, call, callee);
        if (call->obd.is_init || call->flags.is_outbound_mnt ||  call->flags.is_outbound_grp_mnt )
        { 
        bridge_call(session, call, callee,dsn,mutex);    
        }
        else
        { 
        switch_channel_set_variable(channel, "custom_hangup","1012");
        temp_path = switch_mprintf("%s%s", path, "dialout_rate_missing.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        return 0;
        } 
        }
        }

       else
        {
         return true;
        }
        } 
       
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "FINAL CALLEE %s",callee);
        get_ext_details(channel, &call->callee, dsn, mutex, callee);
        switch_channel_set_variable(channel, "sip_req_user",callee);
        
        if (call->caller.is_init && !call->cg.is_init  && !call->conf.is_init )
        {
        switch_channel_set_variable(channel, "call_type", "sip_extn");
        switch_channel_set_variable(channel, "cust_id", call->caller.cust_id);
        if (!handle_sip_call(channel, dsn, mutex, path, custom_path, call))
        status = SWITCH_STATUS_FALSE;       
        }
        }
        switch_safe_free(tokl); 
        }
        return status;
        }



void handle_plugin_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path,call_details_t *call,char **tokl, const char *caller)
        {
        struct stack *pt = newStack(5);
        switch_core_session_t *session = switch_channel_get_session(channel);
        switch_channel_set_variable(channel, "call_type", "call_plugin");

        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, " feature index %s",switch_channel_get_variable(channel, "split_index"));
        if (atoi(switch_channel_get_variable(channel, "split_index")) > 2){
        if (!strcasecmp(tokl[1], "ivr") )
        {
        switch_channel_answer(channel);
        switch_channel_set_variable(channel, "ref_id",tokl[2]);
        call->did.cust_id = switch_mprintf("%s",switch_channel_get_variable(channel, "cust_id"));
        call->did.is_outbound_on = true;
        handle_ivr(channel, dsn, mutex, path,custom_path,call, pt, 1);

        }
        else if (!strcasecmp(tokl[1], "queue") )
        {

        call->did.dst_id = atoi(tokl[2]);
        handle_queue(channel, dsn, mutex, path, custom_path, call, 1);
        }
        else if (!strcasecmp(tokl[1], "cg") )
        { 
        call->did.dst_id = atoi(tokl[2]);
        if (verify_internal_exten(channel, dsn, mutex, call,tokl[2],path))
        {
        if (call->cg.is_init)
        {
        switch_channel_answer(channel);
        call->caller.cust_id = call->did.cust_id;
        handle_cg(channel, call, dsn, mutex, path, custom_path);
        }
        }
        }

        else if (!strcasecmp(tokl[1], "sip"))
        {
        call->flags.is_inbound_sip = true;
        switch_channel_answer(channel);
        switch_channel_set_variable_printf(channel, "ext_id", "%s", tokl[2]);
        get_ext_details(channel, &call->callee, dsn, mutex,tokl[2]);
        handle_sip_call(channel, dsn, mutex, path, custom_path, call);  

        }
        else if (!strcasecmp(tokl[1], "contact") )
        {
        call->flags.is_call_outbound = true;
        if (dialoutrule(channel, dsn, mutex,path ,custom_path,call,tokl[2]) && outbound(session, dsn, mutex, path, custom_path, call, tokl[2]))
        {
        if (call->obd.is_init || call->flags.is_outbound_mnt ||  call->flags.is_outbound_grp_mnt )
        { 
        bridge_call(session, call, tokl[2],dsn,mutex);    
        }
        else
        { 
        switch_channel_set_variable(channel, "custom_hangup","1012");
        } 
        }
        switch_safe_free(tokl[2]);

        }}}



originated_header originated_id_manipulation(switch_channel_t *channel,char clr_no[30], char clr_name[30],call_details_t *call)
        {
        char origination_caller_number[20]={'\0'}, caller_id_name[20]={'\0'},*efc_clr_name,*efc_clr_no; 
        switch_core_session_t *session = switch_channel_get_session(channel);
        const char *call_type = switch_channel_get_variable(channel, "call_type");
        originated_header org_hdr;

        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "call_type  :%s callerid_as_DID %d ",call_type,call->flags.callerid_as_DID);

        if (call->did.is_init){
        if (!(call->flags.callerid_as_DID)){
                if (clr_no[0] == '+')
                {
                clr_no = switch_mprintf("%s%s",call->did.country_prefix, clr_no + strlen(call->did.country_prefix));
                }
                else if (strlen(clr_no) > 8)
                {
                clr_no = switch_mprintf("+%s", clr_no);
                }
                else if  (clr_no[0] == '0' ){
                clr_no = switch_mprintf("%s%s", call->did.country_prefix,clr_no + 1);
                }
                
                strcpy(origination_caller_number,clr_no);
                strcpy(org_hdr.originated_name , clr_no);
        }
        else
        {
              clr_no = switch_mprintf("%s%s", call->did.country_prefix,call->did.num);
              strcpy(origination_caller_number,clr_no);
              strcpy(org_hdr.originated_name ,clr_no);
        }
        
        }

        else if  (call->caller.is_init  && call_type != NULL)
        {
        strcpy(origination_caller_number,clr_no);
        strcpy(caller_id_name,call->caller.caller_id_name);
        strcpy(org_hdr.originated_name , caller_id_name);
        } 
        else if ( call_type == NULL) {
        strcpy(origination_caller_number,clr_no);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "Caller-Caller-ID-Name :%s  sip_h_X-User-Agent:%s",switch_channel_get_variable(channel, "caller_id_name") ,switch_channel_get_variable(channel,"sip_h_User-Agent"));
        (switch_channel_get_variable(channel, "caller_id_name") != NULL) ? strcpy(caller_id_name,switch_channel_get_variable(channel, "caller_id_name")) :  strcpy(caller_id_name,call->caller.caller_id_name);
        (switch_channel_get_variable(channel, "caller_id_name") != NULL) ?  strcpy(org_hdr.originated_name , switch_channel_get_variable(channel, "caller_id_name")) : strcpy(org_hdr.originated_name , caller_id_name);

        }

        strcpy(org_hdr.originated_id_value , origination_caller_number);
        efc_clr_no = switch_mprintf("effective_caller_id_number=%s", origination_caller_number);
        switch_core_session_execute_application(session, "set", efc_clr_no);
        efc_clr_name = switch_mprintf("effective_caller_id_name=%s", org_hdr.originated_name);
        switch_core_session_execute_application(session, "set", efc_clr_name);
        switch_safe_free(efc_clr_no);
        switch_safe_free(efc_clr_name); 
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "After manipulation clr_no:%s caller_id_name:%s ",org_hdr.originated_id_value,org_hdr.originated_name );
        return org_hdr;
        }




bool handle_sip_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call)
        {  
        if (clr_status(channel))
        {
        const char* callee = switch_channel_get_variable(channel, "sip_req_user");
        const char* caller = switch_channel_get_variable(channel, "sip_from_user");
        const char* transfer = switch_channel_get_variable(channel, "transfer_number");
        switch_core_session_t *session = switch_channel_get_session(channel);
        const char* dialstatus;
        char result[128] = {'\0'};  
        char *rng_ton;
        char* temp_path,* data;
        const static char* clr_uuid;
        const char* call_type = switch_channel_get_variable(channel, "call_type"); 
        const char* rdnis = switch_channel_get_variable(channel, "rdnis");


        if (call_type == NULL ){
        call_type = "sip_extn";
        }
      
        if (!strcasecmp(call_type,"call_plugin") && callee== NULL )
        {
        callee = call->caller.num;   
        } 
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "transfer:%s  callee:%s  caller:%s  call_type:%s", transfer, callee, caller,call_type);
        if (call->callee.is_init )
        {
        callee= call->callee.num ;       
        if (!(call->callee.is_multi_registration)) 
        {
        data =switch_mprintf("hash ${domain} $%s 100 ",callee);
        switch_core_session_execute_application(session,"limit",data); 
        if (switch_channel_get_variable(channel, "limit_usage")  != NULL){
        if (atoi(switch_channel_get_variable(channel, "limit_usage")) == 1)
        {
        clr_uuid = switch_channel_get_variable(channel, "call_uuid");
        }
        else if (atoi(switch_channel_get_variable(channel, "limit_usage")) >= 2)
        {
        switch_channel_set_variable(channel, "limit_usage", "2");
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "clr_uuid:%s",clr_uuid);
        temp_path = switch_mprintf("ringback=%s%s", path, "busy_on_another_call.wav");
        switch_core_session_execute_application(session, "set", temp_path);
        }

        }
        }
        else
        {
        switch_channel_set_variable(channel, "limit_usage", "0");
        }
        if (call->callee.is_rng_ton && call->callee.rng_ton_id !=0 && switch_channel_get_variable(channel, "limit_usage")[0] != '2')
        {
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "FINAL  rng_tone CALLEE:%s \n",callee);
        rng_ton = switch_mprintf("select file_path from pbx_prompts where id=%d", call->callee.rng_ton_id);
        execute_sql2str(dsn, mutex, rng_ton, result, NELEMS(result));
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "%s id %s\n", rng_ton, result);
        if (strcmp(result, ""))
        {
        data = switch_mprintf("ringback=%s%s", custom_path, result);
        switch_core_session_execute_application(session, "set", data);
        }
        }

        else if ( !IS_NULL(rdnis)  && switch_channel_get_variable(channel, "limit_usage")[0] != '2' ) {
        switch_core_session_execute_application(session, "set", "ringback=%(2000,4000,440.0,480.0)");
        }    
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, " cle %s clr %s cle_cust_id  %s clr_cust_id %s",callee, caller,call->callee.cust_id,call->caller.cust_id);

        if ( !strcmp(callee,caller) || (call->callee.cust_id != NULL && call->caller.cust_id !=NULL  && strcmp(call->callee.cust_id,call->caller.cust_id)))
        {    
        temp_path = switch_mprintf("%s%s", path, "not_authorized_to_dial.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;

        }
        else if (call->flags.is_tc_unauth)
        {
        temp_path = switch_mprintf("%s%s", path, "tc_unauthorize_failover.wav");
        switch_core_session_execute_application(session, "playback",temp_path );
        }
        }
        else
        {
        switch_channel_set_variable(channel, "custom_hangup","1014");
        temp_path = switch_mprintf("%s%s", path, "please_check_number_try_again.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;  

        }
        switch_channel_set_variable(channel, "sms", call->callee.is_sms_allowed);
        switch_channel_set_variable(channel, "mobile", call->callee.mobile);
        /*--------------------------------------------------------- Handle DND number-----------------------------------------------------*/
        if (call->callee.is_dnd )
        {
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "ivr-dnd_activated.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }

        /*--------------------------------------------------------- Handle Blacklisted number-----------------------------------------------------*/

        if ((call->callee.blacklist) && (is_black_listed(channel, dsn, mutex,call,callee)))
        {
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "call_blacklist.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }

        if ((call->caller.blacklist) && (is_black_list_outgoing(channel, dsn, mutex,call,callee)))
        {
        sleep(1);
        temp_path = switch_mprintf("%s%s", path, "call_blacklist.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }
        /*--------------------------------------------------------- Handle call recording-----------------------------------------------------*/
        switch_log_printf(SWITCH_CHANNEL_SESSION_LOG(session), SWITCH_LOG_DEBUG, " callee recording %s", callee);

        if (call->caller.is_recording_allowed || call->did.is_recording_on)
        {
        if (call->did.is_recording_on)
        switch_channel_set_variable(channel, "sip_req_user", callee);
        set_recording(channel, "call", call, dsn, mutex,path,custom_path);

        }

        /*---------------------------------------------------------  Handle call forwarding-----------------------------------------------------*/

        if (call->callee.is_call_frwd)
        {
        check_call_frwd(channel, dsn, mutex, call);
        if (call->frwd[0].type != 0)
        {
        call->flags.is_frwd_all = true;
        forward_call(channel, dsn, mutex,path,custom_path, call, 0);
        return true;
        }
        }
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, ":callee %s ", callee);

        if(bridge_call(session, call, callee,dsn,mutex)){
        dialstatus =  switch_channel_get_variable(channel, "DIALSTATUS"); 
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "Hangup causeis: %s", dialstatus);

        if (call->callee.is_call_frwd)
        {
        int type = -1;

        if ((dialstatus != NULL) && !strcmp(dialstatus, "BUSY"))
        {
        type = 1;

        if (call->frwd[1].type)
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "BUSY FORWADING PMRT\n ");

        }
        }
        else if ((dialstatus != NULL) && !strcmp(dialstatus, "NOANSWER"))
        {
        type = 2;

        if (call->frwd[2].type){
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "NOANSWER FORWADING PMRT\n ");

        }
        }
        else if ((dialstatus != NULL) && !strcmp(dialstatus, "UNALLOCATED_NUMBER"))
        {
        type = 3;

        if (call->frwd[3].type){
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "UNALLOCATED_NUMBER FORWADING PMRT\n ");
        }
        }

        forward_call(channel, dsn, mutex,path,custom_path, call, type);
        }
        dialstatus = switch_channel_get_variable(channel, "DIALSTATUS");

        /*--------------------------------------------------------- FIND ME FOLLOW ME  -----------------------------------------------------*/

        if ((dialstatus != NULL)){
        if ((call->callee.is_fmfm) && (!strcmp(dialstatus, "UNALLOCATED_NUMBER")  || !strcmp(dialstatus, "BUSY") || !strcmp(dialstatus, "NOANSWER")))
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "FIND ME FOLLOW ME");          
        handle_fmfm(channel, dsn, mutex, path,custom_path,call);
        }
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "VOICEMAIL  isCallerHangup::%d callee:%s",call->flags.isCallerHangup ,callee);

        if ((call->callee.is_vm_on)  && !(call->flags.is_frwded) && call->flags.isCallerHangup )

        {       
        if (strcmp(call_type,"sip_extn")){
        switch_channel_answer(channel);

        }
        switch_channel_set_variable(channel, "ann_pmt", call->callee.ann_pmt);
        if (call->did.is_init)
        {
        callee = switch_channel_get_variable(channel, "sip_req_user");
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " DID voicemail callee:%s", callee);
        } 
       // switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "DIALSTATUS %s  ",switch_channel_get_variable(channel, "DIALSTATUS"));
        handle_prompt(channel,switch_channel_get_variable(channel, "DIALSTATUS"), path, custom_path);
        voicemail(session, NULL, NULL, callee);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return false;
        }
        }

        handle_prompt(channel,switch_channel_get_variable(channel, "DIALSTATUS"), path, custom_path);  
        }
        return true;
        }
        return false;

        }


bool handle_sd(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex,char * path,char * custom_path, call_details_t *call)
        {
        const char *callee = switch_channel_get_variable(channel, "sip_req_user");
        switch_core_session_t *session = switch_channel_get_session(channel);
        char *query = NULL;
        char *temp_path=NULL;
        unsigned int country_id = 0;
        char dial_num[20] = {'\0'};
        char result[128] = {'\0'};
        query = switch_mprintf("SELECT CONCAT_WS('#',number,country_id) from pbx_speed_dial WHERE customer_id = %s and extension_id = %d  and status='1'  AND digit='%s'", call->caller.cust_id, call->caller.id, callee);
        execute_sql2str(dsn, mutex, query, result, NELEMS(result));
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "  handle_sd %s\n", query);
        switch_safe_free(query);


        if (strcmp(result, ""))
        {
        sscanf(result, "%[^#]#%u", dial_num, &country_id);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "result :: %s, country : %d , num : %s \n", result, country_id, dial_num);

        if (country_id != 0)
        {
        if (call->caller.is_outbound_allowed)
        {
        call->flags.is_call_outbound = true;
        if (call->caller.is_recording_allowed)
        {
        set_recording(channel, "outbound", call, dsn, mutex,path,custom_path);

        } // maybe add prompt that not allwed
        dialoutrule (channel, dsn, mutex,path ,custom_path,call,dial_num);
        outbound(session, dsn, mutex,path,custom_path, call, dial_num);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "speed dial outbound :%d gw_id:%s", call->flags.is_outbound_mnt,call->obd.gw_id );

        if ((call->obd.is_init || call->flags.is_outbound_mnt || call->flags.is_outbound_grp_mnt))
        { // may add prompt that no gw found
        bridge_call(session, call, dial_num,dsn,mutex);
        }
        }
        }
        else
        {
        call->flags.is_call_speeddial = true;
        strcpy(call->callee.num, dial_num);
        switch_channel_set_variable(channel, "sip_req_user", call->callee.num);
        switch_log_printf(SWITCH_CHANNEL_SESSION_LOG(session), SWITCH_LOG_ERROR, "%s %s\n", dial_num, call->callee.num);
        get_ext_details(channel, &call->callee, dsn, mutex, dial_num);
        handle_sip_call(channel, dsn, mutex,path,custom_path, call);
        }
        }
        else
        {
       // switch_log_printf(SWITCH_CHANNEL_SESSION_LOG(session), SWITCH_LOG_ERROR, "Extension details not found for speed dial.\n");
        temp_path = switch_mprintf("%s%s", path, "speed_dial_not_assign.wav");
        switch_ivr_play_file(session, NULL, temp_path, NULL);
        switch_safe_free(temp_path);
        return false;
        }
        return true;
        }

static int sta_cg_init_callback(void *parg, int argc, char **argv, char **column_names)
        {
        sta_cg_details_t *sta_cg = (sta_cg_details_t *)parg;
        if (argc < 4)
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, " STA_cg  CALLBACK ERROR : NO DATA %d\n", argc);
        return -1;
        }
        for (int i = 0; i < argc; i++)
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "INTERNAL STA_cg %d %s %s\n", i, column_names[i], argv[i]);

        sta_cg->is_init = true;

        if (!IS_NULL(argv[0]) && strlen(argv[0]))
        {
        sta_cg->id = strdup(argv[0]);
        }

        if (!IS_NULL(argv[1]) && strlen(argv[1]))
        {
        sta_cg->agnt = strdup(argv[1]);
        }

        sta_cg->rcd = atoi(argv[2]);

        if (!IS_NULL(argv[3]) && strlen(argv[3]))
        {
        sta_cg->sticky_start_tm = strdup(argv[3]);
        }
        if (!IS_NULL(argv[4]) && strlen(argv[4]))
        {
        sta_cg->sticky_status = strdup(argv[4]);
        }

        return 0;
        }

int handle_cg_stcky_agnt(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex,char * path,char* custom_path, call_details_t *call)
        {

        switch_core_session_t *session = switch_channel_get_session(channel);
        const char *caller = switch_channel_get_variable(channel, "sip_from_user");
        const char *opsip_ip_port = switch_channel_get_variable(channel, "opsip_ip_port");
        char * cg_cust_id= NULL;
        const char *dialstatus ;
        char *contact = NULL;
        char *tmp_str=NULL;
        char *bs_ivr =NULL;
        char sticky_buffer[12];
        bs_ivr = switch_mprintf("%s%s",path,"basic_sticky_agent.wav");

        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "caller.cust_id : %s ,call->did.cust_id,:%s caller:%s sticky_agent:::%d  cust_id:%s", call->caller.cust_id, call->did.cust_id,caller,call->cg.sticky_agent,switch_channel_get_variable(channel, "cust_id"));
        if(call->caller.cust_id == NULL)
        {
        cg_cust_id = call->did.cust_id;
        }  
        else{
        cg_cust_id  = call->caller.cust_id;
        }    
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "cg_cust_id : %s\n ", cg_cust_id);


        (cg_cust_id == NULL) ? cg_cust_id = switch_mprintf("%s" ,switch_channel_get_variable(channel, "cust_id")) : cg_cust_id;

        switch_channel_set_variable(channel, "cust_id", cg_cust_id);

        if (call->cg.sticky_agent){


        if (cg_cust_id != NULL )
        {
        contact = switch_mprintf("SELECT cg.id,fd.forward,cg.recording, date(fd.hangup_time) as sticky_start_tm , \
        (CASE WHEN DATE_ADD(date(fd.hangup_time), INTERVAL cg.sticky_expire DAY) - (CURRENT_DATE ) >= 0 THEN '1' ELSE '0' END) as sticky_status\
        FROM `pbx_feedback` as fd, `pbx_callgroup` as cg where fd.ref_id=cg.id and fd.ref_id='%s' and fd.customer_id='%s' \
        and cg.sip like concat('%%',fd.forward,'%%') and fd.src in ('%s','%s') and cg.sticky_agent='1'  ORDER BY fd.hangup_time desc limit 1 ", call->cg.id,cg_cust_id,caller, switch_channel_get_variable(channel, "effective_caller_id_number"));
        execute_sql_callback(dsn, mutex, contact, sta_cg_init_callback, &call->sta_cg);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "Dial_string : %s\n ", contact);

        }
        }



        if (!IS_NULL(call->sta_cg.agnt))
        {
        if (atoi(call->sta_cg.sticky_status) == 1){
        switch_play_and_get_digits(session, 1, 1, 1, 15000, "#", bs_ivr, NULL, NULL, sticky_buffer, sizeof(sticky_buffer), "[0-9]+", 2000, NULL);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "Dial_string : %s\n", sticky_buffer);
        if (!strcmp(sticky_buffer, "1"))
        {
        // cg i< 3 before i cahnged to to 0 
        for (int i = 0; i <=0; i++)
        {
        switch_channel_set_variable(channel, "call_type", "call_cg_sticky_agent");
        switch_channel_set_variable(channel, "ref_id", call->sta_cg.id);
        tmp_str = switch_mprintf("[leg_timeout=%d,origination_caller_id_number='%s',origination_caller_id_name='%s']sofia/internal/%s@%s",call->cg.ring_timeout,switch_channel_get_variable(channel, "origination_caller_number"),switch_channel_get_variable(channel, "origination_caller_name"),call->sta_cg.agnt,opsip_ip_port);
        switch_core_session_execute_application(session, "bridge", tmp_str);
        if (call->sta_cg.rcd)
        {
        call->caller.cust_id = call->did.cust_id;
        strcpy(call->caller.num, call->sta_cg.agnt);
        set_recording(channel, "Call Group Sticky Agent", call, dsn, mutex,path,custom_path);
        }

        dialstatus = switch_channel_get_variable(channel, "DIALSTATUS");

        if ((dialstatus != NULL) && !strcmp(dialstatus, "BUSY"))
        {
        break;
        }
        else if (dialstatus != NULL && !strcmp(dialstatus, "NOANSWER"))
        {
        sleep(10);
        continue;
        }

        if (dialstatus != NULL && !strcmp(dialstatus, "UNALLOCATED_NUMBER"))
        {
        break;
        }
        else if (dialstatus != NULL && !strcmp(dialstatus, "SUCCESS"))
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, " dialstatus: %s\n", dialstatus);
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);

        return 1;
        }
        }
        }
        }
        }
        return 0;
        }



static int tf_init_callback(void *parg, int argc, char **argv, char **column_names)
        {
        tc_failover *tf = (tc_failover *)parg;
        if (argc < 2)
        {
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, " tc CALLBACK ERROR : NO DATA %d\n", argc);
        return -1;
        }
        for (int i = 0; i < argc; i++)
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_ERROR, "INTERNAL tc %d %s %s\n", i, column_names[i], argv[i]);
        tf->is_init = true;
        tf->actve_ftre = atoi(argv[0]);
        tf->actve_val = atoi(argv[1]);

        return 0;
        }



void handle_cg(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex,char * path,char * custom_path)
        {
        if (clr_status(channel)){
        switch_core_session_t *session = switch_channel_get_session(channel);
        const char *opsip_ip_port = switch_channel_get_variable(channel, "opsip_ip_port");
        //const char *opsp_port = switch_channel_get_variable(channel, "cg_active_id");
        char *dial_num ,*query, *temp_path/*, *cg_cust_id */= NULL;
        char *sign = (call->cg.grp_type == 1) ? "," : "|";
        char *token, *rest, *new_str, *tmp,*wel_pmt;
        int ring_tm=0;
        int count=1;
        const char* call_type= switch_channel_get_variable(channel, "call_type");

        const char *dialstatus = NULL;
        char cg_active_id[20]={'\0'},caller[30] = {'\0'};
        originated_header result;

        #define ring_tm_threshold 5 
        #define cg_limit 1 

        token = rest = new_str = tmp = NULL;
        rest = call->cg.extensions;

        strcpy(caller,switch_channel_get_variable(channel, "ani"));

        result = originated_id_manipulation(channel,caller,caller,call);

        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "originated_id_value number:%s originated_name:%s",result.originated_id_value, result.originated_name);

        if (handle_cg_stcky_agnt(channel, dsn, mutex,path,custom_path ,call) == 1)
        {
        switch_channel_hangup(channel, SWITCH_CAUSE_CALL_REJECTED);
        return;
        }
        
       if (call_type == NULL)
       {
       switch_channel_set_variable(channel, "call_type", "call_group");
       }
       else if (!strcasecmp(call_type,"call_plugin")) 
       {
       switch_channel_set_variable(channel, "call_type", "call_plugin");
       }
       switch_channel_set_variable(channel, "ref_id", call->cg.id);
       switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "call_type %s", switch_channel_get_variable(channel, "call_type"));
        token = call->cg.extensions;

        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "SIP String:%s",token);
        if (call->cg.grp_type == 1){
        ring_tm = call->cg.ring_timeout;

        }     

        //hunt group 
        else if (call->cg.grp_type == 2)
        {

        for(int i = 0; i <= strlen(rest); i++)
        {
        if(rest[i] == ',')  
        {
        count++;
        }
        }
        ring_tm = call->cg.ring_timeout/count;
        if (ring_tm > ring_tm_threshold ){
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "hunt group call ring_tm ----:%d & total sip count:%d cg.ring_timeout:%d",ring_tm,count,call->cg.ring_timeout);

        }
        else{  // minimum threshold 5 
        ring_tm = ring_tm_threshold;
        } }

        // welcoming ivr
        sleep(1);
        wel_pmt = switch_mprintf("%s%s", custom_path, call->cg.wc_pmt_path);
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, " file_exists %d",  file_exists(wel_pmt));
        if (file_exists(wel_pmt))
        {
         switch_core_session_execute_application(session,"playback",wel_pmt);
        }
       /*  else
        {
         wel_pmt = switch_mprintf("%s%s", path, "default_prompt.mp3");
         switch_core_session_execute_application(session,"playback",wel_pmt);
        }
       */


        while (token != NULL)
        {        
        token = strtok_r(NULL, ",", &rest);
        if(token != NULL){
        dial_num = switch_mprintf("[leg_timeout=%d,origination_caller_id_number='%s',outbound_caller_from_user='%s',origination_caller_id_name='%s']sofia/internal/%s@%s",ring_tm,result.originated_id_value,result.originated_id_value,result.originated_name, token,opsip_ip_port);
        }
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_DEBUG, "Bridge token extension: %s ", token);

        if (tmp == NULL)
        {
        new_str = switch_mprintf("%s", dial_num);
        }
        else
        {
        new_str = switch_mprintf("%s%s %s", tmp, sign, dial_num);
        }
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, "Bridge string::Token %s\n", dial_num);
        switch_safe_free(dial_num);
        switch_safe_free(tmp);
        tmp = new_str;

        }
        if (call->cg.is_recording_on)
        {
        set_recording(channel, "Call Group", call, dsn, mutex,path,custom_path);
        }
        switch_core_session_execute_application(session, "bridge", new_str);
        dialstatus =  switch_channel_get_variable(channel,"DIALSTATUS");
        switch_safe_free(new_str);


        if( (dialstatus != NULL && call->cg.un_failover)  && (!strcmp(dialstatus, "UNALLOCATED_NUMBER")  || !strcmp(dialstatus, "BUSY") 
        || !strcmp(dialstatus, "NOANSWER") || !strcmp(dialstatus, "ALLOTTED_TIMEOUT") ) )
        {
        int static  counter=0;  

        query = switch_mprintf("SELECT active_feature,active_feature_value FROM `pbx_callgroup` where id=%s", call->cg.id);
        execute_sql_callback(dsn, mutex, query, tf_init_callback,&call->tf);
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, " SQL Failover Call Group: %s\n  cg active id::%d ", query ,call->tf.actve_val);

        if (call->tf.actve_ftre == 6)

        {
        handle_tc_failover(channel, dsn, mutex, path, custom_path, call, call->tc.id,call->tf.actve_ftre,call->tf.actve_val);
        }
        else
        { counter +=1;
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "counter-->::%d",counter);
        if  (counter <= cg_limit)
        {
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_WARNING, "tc_actve_ftre:%d ,dialstatus:%s  call->cg.id:%s cg_cust_id:%s",call->tf.actve_ftre,dialstatus,call->cg.id,switch_channel_get_variable(channel,"cust_id"));
        sprintf(cg_active_id,"%d",call->tf.actve_val);
        switch_channel_set_variable(channel, "cg_active_id",cg_active_id);
        if (call->tf.actve_ftre != 1)
        {
        temp_path = switch_mprintf("%s%s", path, "tc_unauthorize_failover.wav");
        switch_core_session_execute_application(session, "playback",temp_path );
        switch_safe_free(temp_path); 
        }

        handle_tc_failover(channel, dsn, mutex, path, custom_path, call, call->tc.id,call->tf.actve_ftre,call->tf.actve_val);
        }
        if(counter >= cg_limit)
        {
        counter = 0;
        }
        }
        }
        }
        }



void handle_conf(switch_channel_t * channel,call_details_t *call ,char * dsn, switch_mutex_t *mutex,char *path, char *custom_path)
        {
        switch_core_session_t* session = switch_channel_get_session(channel); 
        char *profile_str = NULL, *tmp_str=NULL, *end_conf=NULL,* create_sql= NULL, participant_id[10]={'\0'}, instance_id[30]={'\0'}, admin_count[10]={'\0'};
        int count_sql=0,tries = 0;
        switch_time_exp_t tm;
        char date[50] = "", digit[50];
        const char  *result_pin = NULL;
        char *uuid;
        char * temp_path=NULL;
        char *conf_pin = NULL;
        char* admin_counter_sql= NULL;
        switch_size_t retsize;
        switch_time_t ts;
        switch_channel_set_variable(channel,"call_type","call_conference");
        switch_channel_set_variable(channel,"ref_id",call->conf.id);
        switch_channel_set_variable(channel,"conf_id",call->conf.id);
        switch_channel_set_variable(channel,"cust_id",call->conf.cust_id);
        switch_channel_set_variable(channel,"conf_name",call->conf.conf_name);
        switch_channel_set_variable(channel,"participants_status","0");

        ts = switch_time_now();
        switch_time_exp_lt(&tm, ts);
        switch_strftime(date,&retsize,sizeof(date),"%Y-%m-%d-%T",&tm);
        switch_channel_answer(channel);
        uuid = switch_channel_get_uuid(channel);
        conf_pin = switch_mprintf("%s%s", path, "/conf-pin.wav");
        //create event
        create_event(channel,call,dsn,mutex); 
        create_sql = switch_mprintf("SELECT COUNT(pcp.participant_id) FROM `pbx_conference` as pc \
        LEFT JOIN pbx_conference_participant as pcp on pcp.conference_id = pc.id \
        JOIN pbx_conference_cdr pcc on pcc.conf_id = pc.id \
        WHERE pc.customer_id = %s  and pcc.participant_id = %s AND pcc.participants_status like 'active_%%'",call->conf.cust_id, call->conf.participant_id);   

        execute_sql2str(dsn, mutex, create_sql, participant_id, NELEMS(participant_id));
        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "   participant_count:%s ",participant_id);
        switch_safe_free(create_sql); 

        count_sql = atoi(participant_id);



        if (count_sql == 0)

        { 

        create_sql = switch_mprintf("SELECT id  FROM `pbx_conference_cdr` ORDER BY `pbx_conference_cdr`.`id`  DESC LIMIT 1 ");   
        execute_sql2str(dsn, mutex, create_sql, instance_id, NELEMS(instance_id));
        strcpy(instance_id,switch_mprintf("%s%s%s",instance_id,call->conf.id,call->conf.participant_id));
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " create_sql :%s \n  instance_id:%s participant_count %s ", create_sql,instance_id,participant_id);
        switch_channel_set_variable(channel,"instance_id",instance_id); 
        members_status(channel,call,dsn,mutex,uuid);   
        }
        else 
        {
        create_sql = switch_mprintf("SELECT instance_id FROM `pbx_conference_cdr`  WHERE conf_id = %s ORDER by instance_id DESC LIMIT 1",call->conf.id);  
        execute_sql2str(dsn, mutex, create_sql, instance_id, NELEMS(instance_id));
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE,"create_sql :%s \n  instance_id:%s ", create_sql,instance_id);
        switch_channel_set_variable(channel,"instance_id",instance_id); 
        }


        /* if (atoi(participant_id) == 0)

        {
        switch_ivr_play_file(session, NULL,"/home/cloudconnect/pbx_new/upload/def_prompts/unathorized_conf.wav", NULL);

        switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " Your are not authorized person for this conference pls contact admin participant_id:%s ", participant_id);

        } */


        // else{



        while (tries < 3)
        {
        temp_path = switch_mprintf("%s%s!%s", custom_path, call->conf.wc_prompt, conf_pin);
        switch_channel_set_variable(channel, "playback_delimiter", "!");
        //temp_path = switch_mprintf("%s%s", custom_path, call->conf.wc_prompt);
        switch_play_and_get_digits(session, 5, 5, 1, 5000, "#", temp_path, NULL, NULL, digit, sizeof(digit), "[0-9]+", 3000, NULL);
        switch_safe_free(temp_path);


        result_pin = strdup(digit);
        // admin profile          
        if (strcmp(result_pin,call->conf.admin_pin) == 0 ){   
        //switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"conf_id admin::: %s \n",switch_channel_get_variable(channel,"conf_id"));


        admin_counter_sql = switch_mprintf("SELECT COUNT(1)  FROM  `pbx_conference_cdr` WHERE conf_id = %s  AND participants_status = 'active_admin'",call->conf.id);  
        execute_sql2str(dsn, mutex, admin_counter_sql, admin_count, NELEMS(admin_count));
        // switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_NOTICE, " admin_counter_sql :%s \n  \t admin_count:%s ", admin_counter_sql,admin_count);


        if (atoi(admin_count) == 0){

        switch_channel_set_variable(channel,"participants_status","active_admin");
        members_status(channel,call,dsn,mutex,uuid);


        // admin entry announcement
        if (call->conf.name_record){

        tmp_str = switch_mprintf("namefile=/%s/%s/recording/${uuid}-name.wav",call->flags.recording_path,call->caller.cust_id);
        switch_core_session_execute_application(session,"set",tmp_str);
        switch_core_session_execute_application(session,"playback","voicemail/vm-record_name1.wav");
        switch_core_session_execute_application(session,"playback","tone_stream://%(1000,0,500)"); 
        switch_core_session_execute_application(session,"record","${namefile} 4"); 
        tmp_str = switch_mprintf(" res=${sched_api +1 none conference  %s_%s  play file_string://conference/mod_joined_an.wav!${namefile}}",call->conf.cust_id,call->conf.ext );

        }

        switch_core_session_execute_application(session,"set",tmp_str); 
        // confernce recording with end conf tag
        if(call->conf.is_recording) {

        set_recording(channel,"Conference Call", call,dsn,mutex, path, custom_path); 
        //switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"Recording started");

        }
        if (!(call->conf.is_recording)){

        //tmp_str = switch_mprintf("3 a s record_session::%s/%s/recording/Conference_clr${caller_id_number}_cle*%s_%s.wav",recording_path,call->conf.cust_id,call->conf.ext,date);

        // set_recording(channel,"Conference Call", call,dsn,mutex); 

        switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"Moderator your recording is off press 3 to activate recording\n");      
        }

        if (call->conf.end_conf)
        {
        end_conf = "endconf";  
        // switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"This conference will end after admin left:%s", end_conf);
        }
        profile_str = switch_mprintf("%s_%s@advc_conf+flags{%s|moderator}",call->conf.cust_id,call->conf.ext,end_conf);
        //switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"admin_counter_sql++ :%s  profile_str::: %s \n",admin_counter_sql,profile_str);
        switch_core_session_execute_application(session,"conference",profile_str);
        }
        else  if (strcmp(result_pin,call->conf.admin_pin) == 0) {  
        temp_path = switch_mprintf("%s%s", path, "moderator_joined.wav");
        switch_ivr_play_file(session, NULL,temp_path, NULL);
        switch_safe_free(temp_path);

        switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE," moderator already joined:%s\n",admin_counter_sql);
        }
        }

        // members profile  
        if  (strcmp(result_pin,call->conf.mem_pin) == 0){

        //name recording  
        if (call->conf.name_record){

        tmp_str = switch_mprintf("namefile=/%s/%s/recording/${uuid}-name.wav", call->flags.recording_path);
        switch_core_session_execute_application(session,"set",tmp_str);
        switch_core_session_execute_application(session,"playback","voicemail/vm-record_name1.wav");
        switch_core_session_execute_application(session,"playback","tone_stream://%(1000,0,500)"); 
        switch_core_session_execute_application(session,"record","${namefile} 5");
        tmp_str = switch_mprintf(" res=${sched_api +1 none conference  %s_%s  play file_string://conference/conf-has_joined.wav!${namefile}}",call->conf.cust_id,call->conf.ext );

        switch_core_session_execute_application(session,"set",tmp_str); 
        }

        switch_channel_set_variable(channel,"participants_status","active_member");
        members_status(channel,call,dsn,mutex,uuid);


        if (call->conf.wait_moderator){
        profile_str = switch_mprintf("%s_%s@advc_conf+flags{wait-mod}",call->conf.cust_id,call->conf.ext);
        }
        else{
        profile_str = switch_mprintf("%s_%s@advc_conf",call->conf.cust_id,call->conf.ext);
        }
        switch_core_session_execute_application(session,"conference",profile_str);

        switch_safe_free(profile_str); 

        break;
        }

        if (tries == 2)
        {
        temp_path = switch_mprintf("%s%s", path, "max_tries.wav");
        switch_ivr_play_file(session, NULL,temp_path, NULL);
        switch_safe_free(temp_path);
        //switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"max tries \n");
        sleep(1);
        break;
        }

        else if (strlen(digit) == 0 )
        {
        temp_path = switch_mprintf("%s%s", path, "no_input.wav");
        switch_ivr_play_file(session, NULL,temp_path, NULL);
        switch_safe_free(temp_path);
        //switch_log_printf(SWITCH_CHANNEL_LOG,SWITCH_LOG_NOTICE,"Please provide input tries : %d \n",tries+1);

        }

        else if (!(strcmp(result_pin,call->conf.mem_pin))  + !(strcmp(result_pin,call->conf.admin_pin)) == 0 ) {
        temp_path = switch_mprintf("%s%s", path, "invalid_digit.wav");       
        switch_ivr_play_file(session, NULL,temp_path, NULL);
        switch_safe_free(temp_path);


        }

        tries++;
        }

        bridge_event(channel,call,dsn, mutex,uuid);
        destroy_event(channel,call,dsn, mutex);

        // } 


        }



bool clr_status(switch_channel_t *channel)
        {
        bool clr_status = true;

        if (!(IS_NULL(switch_channel_get_variable(channel, "sip_term_cause"))))
        {
        const char *hangup_cause [1] ={"487"};
        /*  for (size_t i=0; i < sizeof(hangup_cause)/sizeof(hangup_cause[0]) ; i++)
        { */
        clr_status =strcmp(switch_channel_get_variable(channel, "sip_term_cause"),hangup_cause[0]);
        if (!(clr_status) )
        {
        return false;
        }

        //}
        }
        //switch_log_printf(SWITCH_CHANNEL_LOG, SWITCH_LOG_INFO, "clr_status %d ",clr_status);

        return clr_status;
        }

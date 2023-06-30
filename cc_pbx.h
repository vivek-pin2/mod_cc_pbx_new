#ifndef _CC_PBX_H_
#define _CC_PBX_H_

#include <switch.h>
#include <stdbool.h>
#include <time.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <switch_event.h>

#define NELEMS(x) (sizeof(x) / sizeof((x)[0]))
#define IS_NULL(x) (x == NULL) ? true : false
#define MAX 10
#define NULL ((void *)0)

// appointment struct start.
typedef struct
{
char *apmt_id;
char *apmt_name;
char *open_time;
char *close_time;
char *tm_bk_srt;
char *wc_pmt_path;
char *invalid_pmt_path;
char *tm_pmt_path;
char phone_no1[5000];
char *phone_no2;
char *tm_bk_end;
int contact_id;
int grp_contact_id;
char *name;
char *ext_no;
uint16_t dig_tm_out;   // seconds
uint16_t intm_dig_out; // seconds
uint8_t mx_tm_out_try;
uint8_t mx_invalid_try;
char tm_interval[4];
bool is_ext;
bool is_pstn;
} apmt_details_t;


typedef struct  {
char originated_id_value[28], originated_name[23];
}
originated_header;



typedef struct
{
char real_path[200];
char custom_prompt[200];
char ip[100];
char local_ip[100];
int port;
} Path_details;

typedef struct
{
char *id;
int app_id;
char *did;
char *src;
char date_slot[50];
char time_start[50];
char time_end[50];
bool is_init;
} apmt_slots_details_t;

typedef struct
{
bool is_dnd;
bool is_init;
bool is_vm_on;
bool is_recording_allowed;
bool is_outbound_allowed;
bool is_mnt_plan_enabled;
bool is_sd_allowed;
bool is_call_frwd;
bool is_call_trns;
bool blacklist;
bool is_admin;
bool is_rng_ton;
bool is_fmfm;
uint8_t dial_timeout; // dial time out
char *cid_hdr_value;
char *cid_name;
char *external_cid;
char *codec;
unsigned int cid_hdr_type;
unsigned int pkg_id;
unsigned int rng_ton_id;
char *cust_id;
unsigned int id;
char num[20];
char *ann_pmt;
char *mobile;
const char *dout_num;
char *is_sms_allowed;
char *caller_id_name;
bool is_multi_registration;
} ext_detail_t;




typedef struct
{
bool is_callee_did;
bool is_did_free;
bool is_billing_on;
bool is_call_transferred;
bool is_frwd_all;
bool is_frwded;
bool is_outbound;
bool is_frwd_outbound;
bool is_call_internal;
bool is_call_inbound;
bool is_inbound_sip;
bool is_call_outbound;
bool is_call_speeddial;
bool is_outbound_mnt ;
bool is_outbound_grp_mnt;
bool is_tc_unauth;
bool is_roaming;
bool isCallerHangup;
char* recording_path;
bool callerid_as_DID;

} call_status_flag_t;

typedef struct
{
bool gw_grp_id;
bool is_lcr_on;
bool is_init;
bool is_size;
char *is_mnt;
char *talktime_mnt;

// min_dur;
// unsigned int incr_dur; // billing block
char *gw_id;
unsigned int rate_card_id;
unsigned int call_hdr_typ;
char *clr_id_hdr;
float crdt_lmt;
float blnce;
int billing_typ;
char *clr_id;
char *clr_pfile;
char *call_plan_id;
char *buy_rate;
char *incr_dur; // billing block
char *min_dur;
char *sell_rate;
char *dial_prefix;
char *bill_type;
char *gw_ip;
char *area_code;
char *gw_codec;
//char *gw_prepend;
char *gw_prepend_cid;
char *call_plan_rate_id;
char *strp_clr_id;
bool gwty_status;

} outbound_detail_t;

typedef struct
{
bool pkg_blng_typ;
char *dialout_id;
bool is_init;
bool is_size;
//unsigned int is_sign;
char *dlout_cp_id;
char *gw_id;
char *gw_ip;
char *gw_port;
char *gw_codec;
char *gw_prepend;
char *gw_prepend_cid;
char *gw_hdr_typ;
char *gw_caller_id;
char *gw_clr_id_hdr;
char *gw_id_prof;
char *is_mnt_plan;
char *remain_mnt;
bool is_group;
char *group_id;
char *group_mnt;
char *dial_prefix;
char *strp_clr_id;
bool gwty_status;
char *ext_minute;
char *ext_mnt_id;


} mnt_detail_t;

typedef struct
{
uint8_t type; // 0=Disabled,1=Voicemail,2=External,3=Extension
char num[15];
} call_frwd_t;

typedef struct
{
bool is_init;
bool is_recording_on;
uint8_t grp_type;
unsigned int ring_timeout;
unsigned int moh;
char *id;
char *extensions;
bool sticky_agent;
bool un_failover;
char* wc_pmt_path;
bool feature_enabled;
} callgrp_details_t;

typedef struct
{
bool is_init;
char * ring_timeout;
unsigned int id;
char *fmfm1;
char *fmfm2;
char *fmfm3;
} fmfm_details_t;

typedef struct
{
bool is_init;
char *id;
char *conf_name;
char *ext;
char *cust_id;
char *participant_id;
char *admin_pin;
char *mem_pin;
unsigned int moh;
bool is_recording;
char *wc_prompt;
bool wait_moderator;
bool name_record;
bool end_conf;
bool feature_enabled;


} conf_details_t;

typedef struct
{
bool is_init;
bool is_blacklist_on;
bool is_vm_on;
bool is_recording_on;
bool is_outbound_on;
bool is_call_barging_on;
uint8_t type;
unsigned int tm_gp_id;
int id;
char *cust_id;
char *bill_type;
unsigned int max_cc;
unsigned int actv_ftr_id;
unsigned int dst_id;
double fixrate;
char *selling_rate;
char *conn_charge;
char num[20]; // did_no
int crdt_lmt;
int blnce;
int billing_typ;
bool tm_grp_failover;
bool geo_tracking;
char country_prefix[10];
} did_details_t;

typedef struct
{
bool is_init;
char * unauth_usr;
char q_name[20];
char *welcome_pmt;
char *ann_pmt;
unsigned int max_wait_call;
bool p_anc; // periodic announcement
unsigned int p_anc_time;
bool play_pos_on_call;
bool play_pos_prdcly;
bool stcky_agnt;
bool recording;

} queue_details_t;

typedef struct
{
bool is_init;

char tc_name[20];
char *id;
char *cntct1;
char *cntct2;
char *mnt_id;
int mnt;
unsigned int max_wait_call;
char *welcome_pmt;
char *ann_pmt;
bool p_anc; // periodic announcement
unsigned int p_anc_time;
bool play_pos_on_call;
bool play_pos_prdcly;
char* ann_time;
bool tc_caller_id;

} tc_details_t;

typedef struct
{
bool is_init;
char tc_name[20];
char *id;
int mnt;
unsigned int max_wait_call;
char *welcome_pmt;
char *ann_pmt;
bool p_anc; // periodic announcement
unsigned int p_anc_time;
bool play_pos_on_call;
bool play_pos_prdcly;
bool unauth_failover;
bool tc_caller_id;



} unauth_tc_details_t;




typedef struct
{
bool is_init;
char *gw_id;
char *strip_clr_id;
char *prepend_clr_id;
char *clr_id_manipulation;

} clr_header_manipulation;

typedef struct
{
bool is_init;
int actve_ftre;
int actve_val;
} tc_failover;

typedef struct
{
bool is_init;
char *id;
int rcd;
int sat;
char *agnt;
char *sticky_start_tm_que;
char *sticky_status_que;

} sta_details_t;

typedef struct
{
bool is_init;
char *id;
int rcd;
char *agnt;
char *sticky_start_tm;
char *sticky_status;

} sta_cg_details_t;

typedef struct
{
bool is_init;
char *strip_digit;
char *prepend_digit;
char *exceptional_rule;
int black_list;
int dialout_manipulation;
int id;
int dialout_group_id;
} dialout_rule_details_t;

typedef struct
{
bool is_init;
char ivr_name[20];
char ivr_prm[200];
char ivr_dgt[200];
char *welcome_pmt;
char *repeat_pmt;
char *invalid_pmt;
char *timeout_pmt;
unsigned int timeout;
unsigned int dgt_timeout;
unsigned int mx_timeout;
unsigned int invld_count;
unsigned int drct_ext_call;
unsigned int is_direct_ext_dial;
} ivr_details_t;
/*typedef struct{
bool is_init;
char* tm_start;
char *  tm_finish;
char *mt_st_dy;
char * mt_ft_dy;
char * sedule_weekly ;
char * sedule_weekly_cstm;
char * holidy;
}time_details;*/

typedef struct
{
bool is_init;
int bling_typ;
char *blnce;
char *crdt_lmt;
} feture_details_t;


typedef struct
{
ext_detail_t caller;
ext_detail_t callee;
did_details_t did;
outbound_detail_t obd;
call_status_flag_t flags;
callgrp_details_t cg;
conf_details_t conf;
queue_details_t cq;
ivr_details_t cv;
tc_details_t tc;
unauth_tc_details_t un_tc;
clr_header_manipulation cli_data;
tc_failover tf;
sta_details_t sta;
sta_cg_details_t sta_cg;
feture_details_t fd;
// time_details tm;
call_frwd_t frwd[4]; // 4 -> all,busy,noans,unavail
fmfm_details_t fmfm;
mnt_detail_t mnt;
apmt_details_t apmt;
apmt_slots_details_t apmt_slots;
dialout_rule_details_t drule;

} call_details_t;

struct node
{
char *data;
char *key;
struct node *next;
};

struct stack
{
int maxsize;
int top;
int *items;
};

typedef struct
{
int items[MAX];
int top;
} st;


// fs_dbh
switch_status_t execute_sql(char *odbc_dsn, char *sql, switch_mutex_t *mutex);
char *execute_sql2str(char *odbc_dsn, switch_mutex_t *mutex, char *sql, char *resbuf, size_t len);
switch_bool_t execute_sql_callback(char *odbc_dsn, switch_mutex_t *mutex, char *sql, switch_core_db_callback_func_t callback, void *pdata);

// cc_pbx_features
switch_status_t handle_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path_info, char *custom_path, char *opsip_ip_port ,call_details_t *call_info);
bool handle_sip_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);
bool handle_sd(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);
void eaves_drop(switch_core_session_t *session, const char *extension, call_details_t *call_info, char *dsn, switch_mutex_t *mutex);
void ivr(switch_core_session_t *session, uint8_t min, uint8_t max, char *audio_file, const char *result, call_details_t *call_info, char *dsn, switch_mutex_t *mutex);
void feature_code(switch_core_session_t *session, const char *callee, const char *caller, call_details_t *call_info, char *dsn,
                switch_mutex_t *mutex, char *path, char *custom_path);
void valetpark(switch_core_session_t *session, const char *callee);
void park(switch_core_session_t *session, const char *callee);
char **split(char string[], int *num, char *sep,switch_channel_t *channel);
void addLast(struct node **head, char *val, char *key);
struct node *search(struct node *head, char *key);
void printList(struct node *head);
int  handle_cg_stcky_agnt(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);


// cc_pbx_function
bool verify_apmt_slots(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path);
void handle_appointment(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call, char *path, char *custom_path);
void handle_patch_api(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call, char *path, char *custom_path);
int cust_ivr(switch_core_session_t *session, int min, int max, int max_tries, int digit_timeout, char *file, char *invalid_file, char *tm_out_pmt, int timeout, int dig_1, int dig_2, char *path);
void book_appointment(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call, int bk_day, char *path, char *custom_path);
void handle_prompt(switch_channel_t *channel, const char *dialstatus, char *path, char *custom_path);
void handle_test(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex);

bool is_black_listed(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call, const char *blist_num);
bool is_black_list_outgoing(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call,const char *blist_num);
bool get_ext_details(switch_channel_t *channel, ext_detail_t *extn, char *dsn, switch_mutex_t *mutex, const char *num);
void forward_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, int i);
void set_recording(switch_channel_t *channel, const char *type, call_details_t *call, char *dsn, switch_mutex_t *mutex, char *recording_path, char *custom_path);
void voicemail(switch_core_session_t *session, char *check, char *auth, const char *num);

bool bridge_call(switch_core_session_t *session, call_details_t *call, const char *dial_num, char *dsn, switch_mutex_t *mutex);
void check_call_frwd(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call);
bool outbound(switch_core_session_t *session, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, const char *num);
bool verify_did(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, did_details_t *did);

bool verify_internal_exten(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, call_details_t *call, const char *num,char *path);
void handle_cg(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path);
void handle_fmfm(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);
void handle_ivr(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, struct stack *pt, int ivr);
void handle_did_dest(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);
void handle_tc_failover(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, char *tc_id,int actve_ftre,int actve_val);
void handle_queue(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, int i);

bool handle_stcky_agnt(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call);
void handle_play_bck(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, char *id);
void handle_conf(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path);

void create_event(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex);
void members_status(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex, const char *uuid);
void bridge_event(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex, const char *uuid);
void destroy_event(switch_channel_t *channel, call_details_t *call, char *dsn, switch_mutex_t *mutex);
bool dialoutrule(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path, call_details_t *call, const char *dial_num);
originated_header originated_id_manipulation(switch_channel_t *channel,char clr_no[30], char clr_name[30],call_details_t *call);

void handle_plugin_call(switch_channel_t *channel, char *dsn, switch_mutex_t *mutex, char *path, char *custom_path,call_details_t *call_info,char **tokl,const char *caller);

void log_print(char* filename, int line, char *fmt,...);

#define LOG_PRINT(...) log_print(__FILE__, __LINE__, __VA_ARGS__ )

char *c_time();
//char  *recording_path_res(switch_channel_t *channel, char *rcdr_path);
int pop(struct stack *pt);
int peek(struct stack *pt);
void push(struct stack *pt, int x);
int isFull(struct stack *pt);
int isEmpty(struct stack *pt);
int size(struct stack *pt);
struct stack *newStack(int capacity);
bool file_exists (char *filename);
bool clr_status(switch_channel_t *channel);

#endif

var xml = require("xml");
var express = require("express");
var bodyParser = require("body-parser");
var app = express();
var parseString = require('xml2js').parseString;
const config = require('./config.json');
const xmlformat = require('./xmlformat.js');
const { queue } = require("./xmlformat");


app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
let nodeport = config.server.nodeport;
let nodeip = config.server.ip;




app.post('/', function (req, res) {
  let getparmsdata = [];
  let getvariabledata = [];
  let ipaddress = [];





  res.setHeader('Content-Type', 'text/xml');
  console.log(req.body.section);
 switch (req.body.section) {
    case 'configuration':
      {
        if (req.body.key_value == 'acl.conf') {
          xmlformat.conn.query(`select ip from  gateway union select ip from server_details  UNION select ip FROM pbx_whitelist_ip `, function (err, result) {
            if (err) throw err;
            for (var i = 0; i < result.length; i++) {
              ipaddress.push(result[i].ip)
            }
            res.send(xmlformat.acldata(ipaddress))

          })
        }
       /* else if (req.body.key_value == 'conference.conf') {
          xmlformat.conn.query("SELECT conf.*, GROUP_CONCAT(DISTINCT (pro.file_path)) as file_path FROM `pbx_conference` as conf LEFT JOIN `pbx_prompts` as pro on (conf.moh = pro.id or conf.welcome_prompt = pro.id)  where conf.status ='1' GROUP BY conf.id ", function (err, result) {
            if (err) throw err;
           
               res.send (xmlformat.confrencedata(result));

          })
        }*/
	    
       else if (req.body.key_value == 'sofia.conf') {

        console.log("req gateway ***********", req.body)

         

            xmlformat.conn.query(`select param_name , param_value from sofia_internal `, function (err, result) {
              if (err) throw err;
              
                xmlformat.conn.query(` select * from gateway where sofia_profile ='0'`, function (err, in_gatewayresult) {
                    if (err) throw err;
                xmlformat.conn.query(` select * from gateway where sofia_profile ='1'`, function (err, ex_gatewayresult) {
                      if (err) throw err;
		        xmlformat.conn.query(`select * from sofia_external`, function (err, externalresult) {
                if (err) throw err;


              res.send(xmlformat.sofiainternaledata(result,in_gatewayresult,ex_gatewayresult,externalresult));
            })
	   })
	    })
        })
          } 
        
         
          else if (req.body.key_value == 'callcenter.conf') {

            console.log( "queue___profile",req.body['CC-Queue'])
            if (req.body['CC-Queue'] != undefined){
            console.log( "**calling_profile**",req.body['CC-Queue'].replace(/@default/g,''))
            queue_id = req.body['CC-Queue'].replace(/@default/g,'')
          
            if(queue_id.match(/tc/gi) =="tc"){
              var tc_id =queue_id.replace("tc_", "")
               console.log(" id---",tc_id); 
              
 
               xmlformat.conn.query("SELECT tc.id,tc.name,tc.max_waiting_call,tc.max_wait_time,tc.welcome_prompt,tc.moh,tc.ring_strategy,tc.recording,\
                     tc.customer_id,pro.file_path as file_path ,max_no_answer,wrap_up_time,reject_delay_time,no_answer_delay_time,busy_delay_time,max_wait_time \
                     ,if (tier_rule_nanw ,'true','false') as tier_rule_nanw FROM `pbx_tc` as tc LEFT JOIN `pbx_prompts`  as pro on (tc.moh = pro.id)  where tc.id= "+tc_id+" GROUP BY tc.id",
                    function (err, result)  {
                   xmlformat.conn.query("SELECT GROUP_CONCAT(cnt_map.phone_number1,cnt_map.phone_number2) agent,GROUP_CONCAT(ext_map.ext_number) as sip ,tc.id as id  FROM pbx_tc \
                    as tc LEFT JOIN `pbx_prompts` as pro on (tc.moh = pro.id) LEFT JOIN `pbx_tc_mapping` as tc_map  on (tc.id =tc_map.tc_id)\
                     LEFT JOIN `pbx_contact_list` as cnt_map  on (tc_map.ref_id=cnt_map.id) LEFT JOIN `extension_master` as ext_map \
                      on (tc_map.ref_id=ext_map.id) where ( tc_map.type='P' or tc_map.type='E' )   and tc.id = "+tc_id+" GROUP BY tc.id", 
                     function (err,agent_tc)  {
                       if (err) throw err;
                          res.send(xmlformat.queue(result,agent_tc,"tc"))
                      }) })
                       
                   }
            else 
            {   
            xmlformat.conn.query("SELECT que.id,que.name,que.max_waiting_call,que.welcome_prompt,que.moh,que.ring_strategy,que.recording,que.customer_id,pro.file_path as file_path\
            ,max_no_answer,wrap_up_time,reject_delay_time,no_answer_delay_time,busy_delay_time,max_wait_time ,if (tier_rule_nanw ,'true','false') as tier_rule_nanw FROM `pbx_queue` as que\
            LEFT JOIN `pbx_prompts`  as pro on (que.moh = pro.id) where que.status ='1' and que.id = "+queue_id+" GROUP BY que.id ", function (err, result)   {
            xmlformat.conn.query("SELECT agent as sip,id from pbx_queue where id ="+queue_id,
             function (err, agent)  {
             if (err) throw err;
                res.send(xmlformat.queue(result,agent,"queue"))
            })
     })
    }
  }

            else {
            console.log( "**calling_profile** freeswitch  restart")
             
            xmlformat.conn.query("SELECT que.id,que.name,que.max_waiting_call,que.welcome_prompt,que.moh,que.ring_strategy,que.recording,que.customer_id,pro.file_path as file_path \
            ,max_no_answer,wrap_up_time,reject_delay_time,no_answer_delay_time,busy_delay_time,max_wait_time ,if (tier_rule_nanw ,'true','false') as tier_rule_nanw FROM `pbx_queue` as que\
             LEFT JOIN `pbx_prompts`  as pro on (que.moh = pro.id) where que.status ='1' and que.id  GROUP BY que.id ", function (err, result)   {
             if (err) throw err;  
            xmlformat.conn.query("SELECT agent as sip,id from pbx_queue",
             function (err, agent)  {
             if (err) throw err;

           
                res.send(xmlformat.queue(result,agent,"queue"))
               
            })
     })
    }
        
           
          }    
                       
                          
                        
                        
        else {
          res.send(xmlformat.file_not_found());

        }
        break;
      }
    case 'dialplan':
      xml = xmlformat.file_not_found();
      break;

    case 'directory':
      console.log("action",typeof (req.body))
      console.log("action",req.body['Event-Calling-File'])
      if((req.body['Event-Calling-File'])=="mod_voicemail.c"){
      console.log(req.body.user)
      xmlformat.conn.query("SELECT voicemail,id ,sip_password,vm_password,email ,caller_id_name,external_caller_id,status,customer_id  FROM extension_master where  ext_number =" +   '"'+req.body.user+ '"'
, function (err, result) {
        if (err) throw err;
        if (result[0] == null ) {
         // res.send(xmlformat.file_not_found());
         res.sendStatus(402);

        }
        else {
          if (result[0].voicemail == 1) {
                
            getparmsdata.push({ password: result[0].sip_password },
            { 'vm-password': result[0].vm_password },
            {'vm-storage-dir':"/var/www/html/fs_backend/upload/"+result[0].customer_id+"/vm/"+req.body.user}
            )
            xmlformat.conn.query("select otherEmail, voicemailToEmail ,delVoicemailAfterEmail,deliverVoicemailTo from pbx_voicemail where  extension_id=" +   '"'+result[0].id+ '"'
            , function (err, mail) {
        if (err) throw err;
           console.log(mail[0]);
           if(mail[0]!=null){
            if(mail[0].voicemailToEmail == 1){
           getparmsdata.push(
            {"vm-email-all-messages":"true"},
            { "vm-attach-file":"true"})
            if(mail[0].deliverVoicemailTo == 1){
             getparmsdata.push(
              { "vm-mailto": result[0].email+","+ mail[0].otherEmail})        
            } 
            else{
              getparmsdata.push(
              { "vm-mailto": result[0].email})
              }
           if(mail[0].delVoicemailAfterEmail == 1){
               getparmsdata.push( 
               {"vm-keep-local-after-email":"false" })
              }
          }
       }
       console.log(getparmsdata);
        
        getvariabledata.push({ caller_id_name: result[0].caller_id_name },
            { external_caller_id: result[0].external_caller_id }
         )
          
          console.log(xmlformat.directorydataxml(getparmsdata, getvariabledata, req.body.user, req.body.key_value))
          res.send(xmlformat.directorydataxml(getparmsdata, getvariabledata, req.body.user, req.body.key_value));
          
       })
                                                                                                                                        
          }
          else
          {
            getparmsdata.push({ 'vm-password': result[0].vm_password })
          getvariabledata.push({ caller_id_name: result[0].caller_id_name },
            { external_caller_id: result[0].external_caller_id }
	 )
             console.log("vivek",getparmsdata);
  
          console.log(xmlformat.directorydataxml(getparmsdata, getvariabledata, req.body.user, req.body.key_value))
          res.send(xmlformat.directorydataxml(getparmsdata, getvariabledata, req.body.user, req.body.key_value));
            }
        }
          
            
      });
        }
      break;
    case 'cdr':
      xml = console.log("cdr", xmlformat.file_not_found());
      break;
    case 'chatplan':
      xml = console.log("c", xmlformat.file_not_found());
      break;
    case 'phrases':
      xml = console.log("p", xmlformat.file_not_found());
      break;
    default:
        xml = console.log(xmlformat.file_not_found());
     console.log("CDR")
    /*  console.log(req.body.cdr);
     parseString(req.body.cdr, function (err, result) {
    // jsondata=( (JSON.stringify(result, null,2)));
    }); */
 
        

		}
	                                                                                                                                   
});

 

app.listen(nodeport, nodeip, function () {
  console.log('listening on port: ', nodeport);

})



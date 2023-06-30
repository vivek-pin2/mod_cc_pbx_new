var mysql = require('mysql');
var XMLWriter = require('xml-writer');
const config = require('./config');
var format = require('xml-formatter');

var opsip_ip_port = config.server.opsip_ip_port;
console.log("-------------------opsip_ip_port bsnl-------",opsip_ip_port)



var conn = mysql.createPool({
  connectionLimit : 1000,
  connectTimeout  : 60 * 60 * 1000,
  acquireTimeout  : 60 * 60 * 1000,
  timeout         : 60 * 60 * 1000,
  host: config.mysqlinfo.host,
  user: config.mysqlinfo.user,
  password: config.mysqlinfo.password,
  database: config.mysqlinfo.database,
  port: 3306,
  waitForConnections: true,
  connectionLimit: 100

});


function file_not_found() {
  xml = '<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>'
    + '<document type=\"freeswitch/xml\">'
    + '<section name=\"result\">'
    + '<result status=\"not found\"/>'
    + '</section>'
    + '</document>';
  // console.log(xml);
  return xml
};

function directorydataxml(getparmsdata, getvariabledata, sip_auth_username, key_value) {
  var variablexml = []
  variablexml.push({
    toll_allow: "domestic, international, local"
  },
    { accountcode: sip_auth_username },
    { user_context: config.xml.user_context},
    { effective_caller_id_name: `${Object.values(getvariabledata[0])}` },
    { effective_caller_id_number: sip_auth_username },
    { outbound_caller_id_name: `${Object.values(getvariabledata[0])}` },
    { outbound_caller_id_number: `${Object.values(getvariabledata[1])}` },
    { callgroup: "techsupport" },
      )
  xw = new XMLWriter;
  xw.startDocument('1.0', 'UTF-8', 'no');
  xw.startElement('document');
  xw.writeAttribute('type', 'freeswitch/xml');
  xw.startElement("section");
  xw.writeAttribute('name', "directory");
  xw.startElement('domain');
  xw.writeAttribute('name', `${key_value}`);
  xw.startElement('groups');
  xw.startElement('group')
  xw.writeAttribute('name', "default")
  xw.startElement('users');
  xw.startElement('user');

  xw.writeAttribute('id', `${sip_auth_username}`);
  xw.startElement('params');
  for (var i = 0; i < (getparmsdata.length); i++) {

    xw.startElement('param')
    xw.writeAttribute("name", `${Object.keys(getparmsdata[i])}`);
    xw.writeAttribute("value", `${Object.values(getparmsdata[i])}`);
    xw.endElement('param');
  }
  xw.endElement('parms');
  xw.startElement('variables');
  for (var i = 0; i < variablexml.length; i++) {
    xw.startElement('variable');
    xw.writeAttribute('name', `${Object.keys(variablexml[i])}`);
    xw.writeAttribute('value', `${Object.values(variablexml[i])}`);
    xw.endElement('variable');
  }
  xw.endElement('variables');


  xw.endElement('user');

  xw.endElement('users');
  xw.endElement('group');
  xw.endElement('groups');

  xw.endElement("section");
  xw.endElement();
  xw.endDocument();
  //console.log(xw.toString())
  return (format(xw.toString()))
}
function acldata(ipaddress) {

  xw = new XMLWriter;
  xw.startDocument('1.0', 'UTF-8', 'no');
  xw.startElement('document');
  xw.writeAttribute('type', 'freeswitch/xml');
  xw.startElement("section");
  xw.writeAttribute('name', "configuration");

  xw.startElement('configuration');
  xw.writeAttribute('name', 'acl.conf');
  xw.writeAttribute('description', 'Network Lists');
  xw.startElement('network-lists');
  xw.startElement('list')
  xw.writeAttribute('name', 'domains');
  xw.writeAttribute('default', 'deny');
  for (var i = 0; i < ipaddress.length; i++) {
    xw.startElement('node ');
    xw.writeAttribute('type', 'allow');
    xw.writeAttribute('cidr', `${ipaddress[i]}/32`);
    xw.endElement('node');
  }

  xw.endElement('list');
  xw.endElement('network-lists');
  xw.endElement('configuration');
  xw.endElement("section")
  xw.endElement('document');
  xw.endDocument();
 // console.log(xw.toString())
  return (format(xw.toString()))

}

function confrencedata(confarence) {
  var controlattribute = [];
  var controladmin=[];
  
  var paramattribute = [];
     controladmin.push(
    { "mute": "1" },
    { "deaf mute": "0" },
    {"lock":"2"},   
 //   {"execute_application":"3"},
    {"vol listen dn":"4"},
   // {"execute_application":"5"},
    {"vol listen up":"6"},
    {"vol talk dn":"7"},
    {"vol talk up":"9"},
   // {"execute_application":"*"},
   // {"hangup":"#"}


)
 
 controlattribute.push(
    { "deaf mute": "0" },
    {"mute":"1"},
    {"":"2"},
    {"":"3"},
    {"vol listen dn":"4"},
    {"":"5"},
    {"vol listen up":"6"},
    {"vol talk dn":"7"},
    {"":"8"},
    {"vol talk up":"9"},
 //   {"execute_application":"*"},
    //{"hangup":"#"}
   

  )
  xw = new XMLWriter;
  xw.startDocument('1.0', 'UTF-8', 'no');
  xw.startElement('document');
  xw.writeAttribute('type', 'freeswitch/xml');
  xw.startElement("section");
  xw.writeAttribute('name', "configuration");

  xw.startElement('configuration');
  xw.writeAttribute('name', 'conference.conf');
  xw.writeAttribute('description', 'Audio Conference');
  xw.startElement('caller-controls');
  xw.startElement('group')
  xw.writeAttribute('name', 'default_members');
  for (i = 0; i < controlattribute.length; i++) {
    xw.startElement('control')
    xw.writeAttribute('action', `${Object.keys(controlattribute[i])}`);
    xw.writeAttribute('digits', `${Object.values(controlattribute[i])}`)
    xw.endElement('control')
  }
    xw.startElement('control')
    xw.writeAttribute('action', "execute_application");
    xw.writeAttribute('digits', "*");
    xw.writeAttribute('data', "playback ivr/8000/ivr-please_enjoy_music_while_party_reached.wav");
    xw.endElement('control')

  xw.endElement('group')
  xw.startElement('group')
  xw.writeAttribute('name', 'default_admin');
  for (i = 0; i < controladmin.length; i++) {
    xw.startElement('control')
    xw.writeAttribute('action', `${Object.keys(controladmin[i])}`);
    xw.writeAttribute('digits', `${Object.values(controladmin[i])}`)
    xw.endElement('control')
  }
      xw.startElement('control');
    xw.writeAttribute('action',"execute_application");
    xw.writeAttribute('digits',"3");
   xw.writeAttribute('data',"execute_extension 100 XML default");

    xw.endElement('control')

      xw.startElement('control')
    xw.writeAttribute('action',"execute_application");
    xw.writeAttribute('digits',"5");
     xw.writeAttribute('data',"execute_extension Rollcall XML default");
    xw.endElement('control')   
   xw.startElement('control')
    xw.writeAttribute('action',"execute_application");
    xw.writeAttribute('digits',"*");
    xw.writeAttribute('data',"playback ivr/8000/ivr-please_enjoy_music_while_party_reached.wav");
    xw.endElement('control')
  xw.endElement('group')

  xw.endElement('caller-controls')
  xw.startElement('profiles')


for (var i = 0; i < confarence.length; i++) {

        if(confarence[i].moh!=0 && confarence[i].welcome_prompt!=0)
        {
         var res=confarence[i].file_path.split(",")
           confarence[i].moh="/var/www/html/pbx/app"+res[0];
 confarence[i].welcome_prompt="/var/www/html/pbx/app"+res[1];
        }
        else if(confarence[i].moh!=0 && confarence[i].welcome_prompt==0)
        {      confarence[i].welcome_prompt="tone_stream://%(200,0,500,600,700)";
                confarence[i].moh="/var/www/html/pbx/app"+confarence[i].file_path;
        }
        else if(confarence[i].moh==0 && confarence[i].welcome_prompt!=0){
                 confarence[i].welcome_prompt="/var/www/html/pbx/app"+confarence[i].file_path;
                confarence[i].moh="$${hold_music}";
        }
        else{
                 confarence[i].welcome_prompt="tone_stream://%(200,0,500,600,700)";
                  confarence[i].moh="$${hold_music}";
        }


paramattribute.push(
    { "domain": "$${domain}" },
    { "rate": "8000" },
    { "interval": "20" },
    { "energy-level": "100" },
    { "pin-retries" : "3"},
    { "muted-sound": "conference/conf-muted.wav" },
    { "unmuted-sound": "conference/conf-unmuted.wav" },
    {"moderator-controls":"default_admin"},
    {"caller-controls":"default_members"},  
    { "moh-sound": `${confarence[i].moh}` },
    { "enter-sound": "tone_stream://%(200,0,500,600,700)" },
    { "exit-sound": "tone_stream://%(500,0,300,200,100,50,25)" },
    { "kicked-sound": "conference/conf-kicked.wav" },
    { "locked-sound": "conference/conf-locked.wav" },
    { "is-locked-sound": "conference/conf-is-locked.wav" },
    { "is-unlocked-sound": "conference/conf-is-unlocked.wav" },
    { "pin-sound": "conference/conf-pin.wav" },
    { "bad-pin-sound": "conference/conf-bad-pin.wav" },
    { "max-members": "20" },
    { "pin": `${confarence[i].participant_pin}` },
    { "moderator-pin": `${confarence[i].admin_pin}` },
  )
   if(confarence[i].recording!=0 )
    {  paramattribute.push(
         {"auto-record":"/var/www/html/fs_backend/upload/"+confarence[i].customer_id+
                               "/recording/conf_clr${caller_id_number}_cle${destination_number}_${strftime(%Y-%m-%d-%H:%M:%S)}.wav" }
)
      }


  xw.startElement('profile')
  xw.writeAttribute('name', confarence[i].customer_id+"_"+confarence[i].conf_ext)
for (var j = 0; j < paramattribute.length; j++) {
    xw.startElement("param")
    xw.writeAttribute('name', `${Object.keys(paramattribute[j])}`)
    xw.writeAttribute('value', `${Object.values(paramattribute[j])}`)
    xw.endElement("param")

  }


  xw.endElement('profile')
  paramattribute.length = 0

 }


  xw.endElement('profiles')

  xw.endElement('configuration');
  xw.endElement("section")
  xw.endElement('document');
  xw.endDocument();
//console.log(format(xw.toString()))
  return (format(xw.toString()))

}


function sofiainternaledata(sofiainternal,in_gatewayresult,ex_gatewayresult,sofiaexternal) {

 
  var gatewayparam = [];
  var realm = null ,from_domain= null,reg_proxy = null, from_user = null, ip = null;
 
  xw = new XMLWriter;
 
  xw.startDocument('1.0', 'UTF-8', 'no');
  xw.startElement('document');
  xw.writeAttribute('type', 'freeswitch/xml');
  xw.startElement("section");
  xw.writeAttribute('name', "configuration");
  xw.startElement("configuration");
  xw.writeAttribute(" name","sofia.conf")
  xw.writeAttribute("description","sofia Endpoint")
  xw.startElement("profiles")
  xw.startElement('profile');
  xw.writeAttribute('name', 'internal');
  xw.startElement("aliases");
  xw.endElement("aliases");
  xw.startElement("gateways");

  for (var i = 0; i < in_gatewayresult.length; i++) {
    
    xw.startElement("include");
    xw.startElement("gateway")
     if(in_gatewayresult[i].register ==0)
     {
      in_gatewayresult[i].register="false"
      
     }
     else
     {
      in_gatewayresult[i].register="true";
      if (in_gatewayresult[i].callerID == null)
      {
        from_user= in_gatewayresult[i].auth_username;
      }
      else{
        from_user= in_gatewayresult[i].callerID;
      }
     }	  
     
   switch(in_gatewayresult[i].transport_type) {

       case "1":
            in_gatewayresult[i].transport_type="tcp"
            break;
        case "2":
            in_gatewayresult[i].transport_type="tls"
            break;
          default:
              in_gatewayresult[i].transport_type="udp"

     }
     if(in_gatewayresult[i].ip=="")
       { 
        ip = in_gatewayresult[i].domain
         //console.log(in_gatewayresult[i].domain)
         }
        else 
           { 
        ip =in_gatewayresult[i].ip
        }
       if (in_gatewayresult[i].realm==""){
            realm = ip;
          }else{
           
              realm =  in_gatewayresult[i].realm;
             }        

       if (in_gatewayresult[i].is_outbound_proxy=='0'){
           from_domain =  in_gatewayresult[i].outbound_proxy;
           console.log("from_domain_internal",from_domain);
             
          }else{
            from_domain =  ip;

            console.log("---from_domain--",from_domain);
             }        

       if (in_gatewayresult[i].is_register_proxy=='0'){
           reg_proxy = in_gatewayresult[i].register_proxy;

             
          }else{
           
            reg_proxy =  ip;
             }   
             
      // internal register is false hardcore until we make dyanmmic from front-end (BSNL 20-05-22) 
     gatewayparam.push(
      {"realm": realm},
      { "proxy": ip + ":" + in_gatewayresult[i].port },
      { "register-proxy": reg_proxy },
      { "from-domain":from_domain },
      { "register": "false"},
      { "context": "cc_pbx"},
      { "register-transport": `${in_gatewayresult[i].transport_type}` },
    
      { "from-user": from_user},
      { "extension": from_user},
      { "extension-in-contact": "true" },
      
     
    /*   {"ping": `${in_gatewayresult[i].ping}`},
      {"retry-seconds": `${in_gatewayresult[i].retry_sec}`}, */
      
    )
   
    if (in_gatewayresult[i].register == "true") {
      gatewayparam.push(
        { "username": in_gatewayresult[i].auth_username },
        //{ "from-user": from_user},
        { "password": in_gatewayresult[i].password },
        { "expire-seconds": in_gatewayresult[i].expiry_sec },
        { "caller-id-in-from":"true" },
        { "all-reg-options-ping":"true" }
        //{ "register-proxy": outbound_proxy }
      ) } 
        xw.writeAttribute("name", "gw_in_" + `${in_gatewayresult[i].id}`)

      for (var j = 0; j < gatewayparam.length; j++) {
       
        xw.startElement("param")
        xw.writeAttribute("name", `${Object.keys(gatewayparam[j])}`)
        xw.writeAttribute("value", `${Object.values(gatewayparam[j])}`)
        xw.endElement("param")
      }
     xw.endElement("gateway");
     xw.endElement("include")
     gatewayparam.length = 0
    }

  xw.endElement("gateways");
  xw.startElement("domains")
  xw.startElement("domain")
  xw.writeAttribute('name', 'all');
  xw.writeAttribute("alias", "true");
  xw.writeAttribute("parse", "false");
  xw.endElement("domain")
  xw.endElement("domains")
  xw.startElement("settings");

  for (var i = 0; i < sofiainternal.length; i++) {
    xw.startElement("param")
    xw.writeAttribute("name", `${sofiainternal[i].param_name}`)
    xw.writeAttribute("value", `${sofiainternal[i].param_value}`)
    xw.endElement("param")
  }

  xw.endElement("settings");
  xw.endElement("profile");
  xw.startElement('profile');
  xw.writeAttribute('name', 'external');
  xw.startElement("aliases");
  xw.endElement("aliases");
  xw.startElement("gateways");
  for (var i = 0; i < ex_gatewayresult.length; i++) {
    
    xw.startElement("include");
    xw.startElement("gateway")
     if(ex_gatewayresult[i].register == 0)
     {
      ex_gatewayresult[i].register="false";
      if (ex_gatewayresult[i].from_user != null)
      {
     
        from_user= ex_gatewayresult[i].from_user;
        
      }
     }
     else
     {
      ex_gatewayresult[i].register="true";
      from_user= ex_gatewayresult[i].auth_username;
      console.log("---auth_username--",from_user);
     }	  

   switch(ex_gatewayresult[i].transport_type) {

       case "1":
            ex_gatewayresult[i].transport_type="tcp"
            break;
        case "2":
            ex_gatewayresult[i].transport_type="tls"
            break;
          default:
              ex_gatewayresult[i].transport_type="udp"

     }
     if(ex_gatewayresult[i].ip=="")
       { 
        var  ip = ex_gatewayresult[i].domain
         console.log(ex_gatewayresult[i].domain)
         }
        else 
           { 
          var ip =ex_gatewayresult[i].ip
        }
      // realm --------------------
       if (ex_gatewayresult[i].realm=="" || ex_gatewayresult[i].realm=='0'){
            realm = ip;
          }else{
              realm =  ex_gatewayresult[i].realm;
             }        
       if (ex_gatewayresult[i].is_outbound_proxy =='0'){
           from_domain =  ex_gatewayresult[i].outbound_proxy;
           console.log("from_domain",from_domain);
          }else{
            from_domain = ip;
            console.log("--------from_domain------",from_domain,"ip",ip);
             }        

       if (ex_gatewayresult[i].is_register_proxy=='0'){
           reg_proxy = ex_gatewayresult[i].register_proxy;
             console.log("--------from_domain------",from_domain,"ip",ip);
          }else{
            reg_proxy =  ip;
             }   
      console.log("ex_gatewayresult[i].callerID external profle gateway ----",ex_gatewayresult[i].callerID, "id-",ex_gatewayresult[i].id, "contact-params ",ex_gatewayresult[i].calling_profile  );
    console.log(" profile gateway-------------",ex_gatewayresult[i])
      
             
     gatewayparam.push(
      {"realm": realm},
      { "proxy": ip + ":" + ex_gatewayresult[i].port },
      { "register-proxy": reg_proxy },
      { "from-domain":from_domain },
      { "register": ex_gatewayresult[i].register },
      { "register-transport": `${ex_gatewayresult[i].transport_type}` },
    
      { "from-user": from_user},
      { "extension": from_user},
      { "extension-in-contact": "true" },
      { "contact-params": ex_gatewayresult[i].calling_profile },
      
      //{"ping": `${ex_gatewayresult[i].ping}`},
      //{"retry-seconds": `${ex_gatewayresult[i].retry_sec}`}
        
    )
   
    if (ex_gatewayresult[i].register == "true") {
      gatewayparam.push(
        { "username": ex_gatewayresult[i].auth_username },
        { "from-user": from_user},
        { "password": ex_gatewayresult[i].password },
        { "expire-seconds": ex_gatewayresult[i].expiry_sec },
        { "caller-id-in-from":"true" },
        {"all-reg-options-ping":"true" },
        {"nat-options-ping":"true" },
        {"ping": `${ex_gatewayresult[i].ping}`},
        {"ping-min": "1"},
        {"ping-max": "10"},
        {"retry-seconds": `${ex_gatewayresult[i].retry_sec}`},
        { "outbound-proxy":  ip + ":" + ex_gatewayresult[i].port }
        
        )
       } 
        xw.writeAttribute("name", "gw_" + `${ex_gatewayresult[i].id}`)

      for (var j = 0; j < gatewayparam.length; j++) {
        //console.log(gatewayparam.length)
        xw.startElement("param")
        xw.writeAttribute("name", `${Object.keys(gatewayparam[j])}`)
        xw.writeAttribute("value", `${Object.values(gatewayparam[j])}`)
        xw.endElement("param")
       
      }
       xw.startElement("variables")
       xw.writeAttribute("direction", `both`)
       xw.writeAttribute("name", `dtmf_type`)
       xw.writeAttribute("value", `info`)
       xw.endElement("variables")
     
      xw.endElement("gateway")
     xw.endElement("include")
     gatewayparam.length = 0
    }



  xw.endElement("gateways")
  xw.startElement("domains")
  xw.startElement("domain")
  xw.writeAttribute('name', 'all');
  xw.writeAttribute("alias", "false");
  xw.writeAttribute("parse", "true");
  xw.endElement("domain")
  xw.endElement("domains")
  xw.startElement("settings");
   for (var i = 0; i < sofiaexternal.length; i++) {
    xw.startElement("param")
    xw.writeAttribute("name", `${sofiaexternal[i].param_name}`)
    xw.writeAttribute("value", `${sofiaexternal[i].param_value}`)
    xw.endElement("param")
  }



  xw.endElement("settings");
  xw.endElement("profile");
  xw.endElement("profiles")
  xw.endElement("configuration")
  xw.endElement("section")
  xw.endElement('document');
  xw.endDocument();

  return (format(xw.toString()))
}



function queue(result,phn_nmbr,calling_profile){
 var queueparam = [];
 xw = new XMLWriter;

  xw.startDocument('1.0', 'UTF-8', 'no');
  xw.startElement('document');
  xw.writeAttribute('type', 'freeswitch/xml');
  xw.startElement("section");
  xw.writeAttribute('name', "configuration");
  xw.startElement("configuration");
  xw.writeAttribute(" name","callcenter.conf")
  xw.writeAttribute("description","CallCenter")
  xw.startElement("settings")
 /*  xw.startElement('param')
  xw.writeAttribute("name","odbc-dsn")
  xw.writeAttribute("value","freeswitch_bcknd:ccuser:cloudVirAmiNag119")
  xw.endElement("param")  */

  xw.endElement("settings");

 xw.startElement("queues")
 
for(var i=0;i<result.length;i++)
{  
   xw.startElement('queue');
   if (calling_profile == "queue"){xw.writeAttribute('name',result[i].id+"@default");}
   
   else {xw.writeAttribute('name',"tc_"+result[i].id+"@default");}

switch(result[i].ring_strategy) {

        case "0":
            result[i].ring_strategy="ring-all"
            break;
       case "1":
            result[i].ring_strategy="round-robin"
            break;
       case "2":
            result[i].ring_strategy="random"
            break;
       case "3":
            result[i].ring_strategy="longest-idle-agent"
            break;
       case "4":
            result[i].ring_strategy="top-down"
            break;
       case "5":
            result[i].ring_strategy="ring-progressively"
            break;
       case "6":
            result[i].ring_strategy="sequentially-by-agent-order"
            break; 
   

     }
    //console.log(result[i].recording)
   if(result[i].recording==1)
      { 
        result[i].recording="/var/www/html/fs_backend/upload/"+result[i].customer_id+
                               "/recording/queue_clr${caller_id_number}_cle${destination_number}_${strftime(%Y-%m-%d-%H:%M:%S)}.wav"
        }
     else if(result[i].recording=="tc_1"){
     result[i].recording="/var/www/html/fs_backend/upload/"+result[i].customer_id+
                               "/recording/tc_clr${caller_id_number}_cle${destination_number}_${strftime(%Y-%m-%d-%H:%M:%S)}.wav"
        }

      
    else {
           
   result[i].recording="NULL"
     }
    if(result[i].moh==0)
      {
       result[i].moh="$${hold_music}"    
     }
      else 
      {
          result[i].moh= "/var/www/html/pbx/app"+result[i].file_path
       }
  queueparam.push(
    {"strategy":result[i].ring_strategy},
    {"moh-sound":result[i].moh},
    {"record-template":result[i].recording},
    {"time-base-score":"system"},
    {"max-wait-time":result[i].max_wait_time}, 
    {"max-wait-time-with-no-agent":"0"}, 
    {"max-wait-time-with-no-agent-time-reached":"5"},
    {"tier-rules-apply":"false"},
    {"tier-rule-wait-second":"300"},
    {"tier-rule-wait-multiply-level":"false"},
    {"tier-rule-no-agent-no-wait":result[i].tier_rule_nanw},
    {"discard-abandoned-after":"60"},
    {"abandoned-resume-allowed":"false"},
 


   
)
for(var j=0;j<queueparam.length;j++){
   xw.startElement("param")
   xw.writeAttribute("name",`${Object.keys(queueparam[j])}`)
   xw.writeAttribute("value",`${Object.values(queueparam[j])}`) 
   xw.endElement("param")
   }
xw.endElement('queue');
queueparam.length = 0

}
xw.endElement("queues")
xw.startElement("agents")

for(var i=0;i<phn_nmbr.length;i++)
{ 
if (phn_nmbr[i].sip != null){
var sip= phn_nmbr[i].sip.split(",")
for(var j=0;j<sip.length;j++)
{ 

 xw.startElement('agent');
 if (calling_profile =="queue") {
   xw.writeAttribute("name",result[i].id+"_"+sip[j]+"@default")
 }else{xw.writeAttribute("name","tc_"+result[i].id+"_"+sip[j]+"@default")}
 xw.writeAttribute("type","callback")
 xw.writeAttribute("contact","[leg_timeout=15]sofia/internal/"+sip[j]+"@"+opsip_ip_port)
 xw.writeAttribute("status","Available")
 xw.writeAttribute("reserve-agents","true") 
 xw.writeAttribute("truncate-agents-on-load","true") 
 xw.writeAttribute("truncate-tiers-on-load","true") 
 xw.writeAttribute("max-no-answer",result[i].max_no_answer)
 xw.writeAttribute("wrap-up-time",result[i].wrap_up_time)
 xw.writeAttribute("reject-delay-time",result[i].reject_delay_time)
 xw.writeAttribute("no-answer-delay-time",result[i].no_answer_delay_time)
 xw.writeAttribute("busy-delay-time",result[i].busy_delay_time)
 xw.endElement('agent');
 

}

}
if (phn_nmbr[i].agent != null){ 
var pstn= phn_nmbr[i].agent.split(",")
console.log("pstn for tc------>",pstn ,"tc_id",result[i].id);
for(var j=0;j<pstn.length;j++)
{ 
 xw.startElement('agent');
 xw.writeAttribute("name","tc_"+result[i].id+"_"+pstn[j]+"@default")
 xw.writeAttribute("type","callback")
 xw.writeAttribute("contact","{absolute_codec_string='PCMA,PCMU',sip_cid_type=rpid,outbound_caller_from_user=01171366794,origination_caller_id_name='01171366794',origination_caller_id_number=01171366794,leg_timeout=60}sofia/gateway/gw_73/"+pstn[j])
 xw.writeAttribute("status","Available") 
 xw.writeAttribute("max-no-answer",'10')
 xw.writeAttribute("wrap-up-time","10")
 xw.writeAttribute("reject-delay-time","10")
 xw.writeAttribute("busy-delay-time","60")
 xw.endElement('agent');
}
}
}

 xw.endElement("agents")
 xw.startElement("tiers") 

for(var i=0;i<phn_nmbr.length;i++)
{
if (phn_nmbr[i].sip != null){
  var sip= phn_nmbr[i].sip.split(",")
for(var j=0;j<sip.length;j++)
 {

 xw.startElement('tier');
 if (calling_profile == "queue") {
  xw.writeAttribute("agent",result[i].id+"_"+sip[j]+"@default");
 xw.writeAttribute("queue",phn_nmbr[i].id+"@default");
  
 }else{
  
 xw.writeAttribute("agent","tc_"+result[i].id+"_"+sip[j]+"@default");
 xw.writeAttribute("queue","tc_"+phn_nmbr[i].id+"@default");
 }
 
 xw.writeAttribute("level",j+1)
 xw.writeAttribute("position",j+1)
 xw.endElement('tier');
}

}
if (phn_nmbr[i].agent != null){
  var pstn= phn_nmbr[i].agent.split(",")
for(var j=0;j<pstn.length;j++)
 {

 xw.startElement('tier');
 if (calling_profile == "queue") {
  xw.writeAttribute("agent",result[i].id+"_"+pstn[j]+"@default");
  xw.writeAttribute("queue",phn_nmbr[i].id+"@default");
 }else{
  xw.writeAttribute("agent","tc_"+result[i].id+"_"+pstn[j]+"@default");
  xw.writeAttribute("queue","tc_"+phn_nmbr[i].id+"@default");
 }

 xw.writeAttribute("level",j+1)
 xw.writeAttribute("position",j+1)
 xw.endElement('tier');
}

}
}
 xw.endElement("tiers")
  xw.endElement("configuration")
  xw.endElement("section")
  xw.endElement('document');
  xw.endDocument();
//console.log(format(xw.toString()))
return(format(xw.toString()))

} 


module.exports = { conn, directorydataxml, file_not_found, acldata, confrencedata ,sofiainternaledata,queue }




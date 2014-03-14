#  Copyright 2011 Jon Rifkin
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# WARNING!! THIS IS A DERIVED VERSION OF PYCAS!
# This is not the originial version of pycas.py --- it is a copy of 
# there work modified to be used by PPBottleApp.py (NOT CGI).
# That work was done by Robert L. Read, and is not finished.  
# However, as a dervied work, I believe it remains subject to the 
# Apache 2.0 license under which I received it from 
# https://wiki.jasig.org/display/CASC/Pycas  --- Robert L. Read, 2014

# Note: This differes from the original pycas.py mainly by being more
# "purely functional" in organization, as befits a file used from WSGI
# and not CGI.


#!/usr/bin/python

#  Debug
## import os
## print "Content-type: text/html\n"
## import sys
## sys.stderr = sys.stdout






#-----------------------------------------------------------------------
#  Usage  --- THIS IS NO LNGER CORRECT, THIS VERSIION DOES NOT SUPPORT 
#  CGI.
#-----------------------------------------------------------------------
#
#  Purpose
#      Authenticate users against a CAS server from your python cgi scripts.
#
#  Using in your script
#
#      import pycas
#      status, id, cookie = pycas.login(CAS_SERVER,THIS_SCRIPT)
#
#  Required Parameters
#
#      - CAS_SERVER : the url of your CAS server 
#                     (for example, https://login.yoursite.edu).
#      - THIS_SCRIPT: the url of the calling python cgi script.
#
#  Returned Values
#
#      - status:  return code, 0 for success.
#      - id    :  the user name returned by cas.
#      - cookie:  when non-blank, send this cookie to the client's 
#                 browser so it can authenticate for the rest of the
#                 session.
#
#  Optional Parmaters:
#      - lifetime:  lifetime of the cookie in seconds, enforced by pycas. 
#                   Default is 0, meaning unlimited lifetime.
#      - path:      Authentication cookie applies for all urls under 'path'. 
#                   Defaults to "/" (all urls).
#      - protocol:  CAS protocol version.  Default is 2.  Can be set to 1.
#      - secure:    Default is 1, which authenticates for https connections only.
#      - opt:       set to 'renew' or 'gateway' for these CAS options.
#
#        Examples:
#          status, id, cookie = pycas.login(CAS_SERVER,THIS_SCRIPT,protocol=1,secure=0)
#          status, id, cookie = pycas.login(CAS_SERVER,THIS_SCRIPT,path="/cgi-bin/accts")
#
#   Status Codes are listed below.
#

#-----------------------------------------------------------------------
#  Constants
#-----------------------------------------------------------------------
#
#  Secret used to produce hash.   This can be any string.  Hackers
#  who know this string can forge this script's authentication cookie.
import requests

#  Name field for pycas cookie
PYCAS_NAME = "pycas"

#  CAS Staus Codes:  returned to calling program by login() function.
CAS_OK               = 0  #  CAS authentication successful.
CAS_COOKIE_EXPIRED   = 1  #  PYCAS cookie exceeded its lifetime.
CAS_COOKIE_INVALID   = 2  #  PYCAS cookie is invalid (probably corrupted).
CAS_TICKET_INVALID   = 3  #  CAS server ticket invalid.
CAS_GATEWAY          = 4  #  CAS server returned without ticket while in gateway mode.


#  Status codes returned internally by function get_cookie_status().
COOKIE_AUTH    = 0        #  PYCAS cookie is valid.
COOKIE_NONE    = 1        #  No PYCAS cookie found.
COOKIE_GATEWAY = 2        #  PYCAS gateway cookie found.
COOKIE_INVALID = 3        #  Invalid PYCAS cookie found.

#  Status codes returned internally by function get_ticket_status().
TICKET_OK      = 0        #  Valid CAS server ticket found.
TICKET_NONE    = 1        #  No CAS server ticket found.
TICKET_INVALID = 2        #  Invalid CAS server ticket found.
TICKET_NOPIV   = 3        #  No CAS server ticket found.

CAS_MSG = (
"CAS authentication successful.",
"PYCAS cookie exceeded its lifetime.",
"PYCAS cookie is invalid (probably corrupted).",
"CAS server ticket invalid.",
"CAS server returned without ticket while in gateway mode.",
)

###Optional log file for debugging
LOG_FILE="/tmp/cas.log"


#-----------------------------------------------------------------------
#  Imports
#-----------------------------------------------------------------------
import os
import cgi
import md5
import time
import urllib
import urlparse


#-----------------------------------------------------------------------
#  Functions
#-----------------------------------------------------------------------

#  For debugging.
def writelog(msg):
	f = open(LOG_FILE,"a")
	timestr = time.strftime("%Y-%m-%d %H:%M:%S ");
	f.write(timestr + msg + "\n");
	f.close()

#  Used for parsing xml.  Search str for first occurance of
#  <tag>.....</tag> and return text (striped of leading and
#  trailing whitespace) between tags.  Return "" if tag not
#  found.
def parse_tag(s,tag):
   tag1_pos1 = s.find("<" + tag)
   #  No tag found, return empty string.
   if tag1_pos1==-1: return ""
   tag1_pos2 = s.find(">",tag1_pos1)
   if tag1_pos2==-1: return ""
   tag2_pos1 = s.find("</" + tag,tag1_pos2)
   if tag2_pos1==-1: return ""
   return s[tag1_pos2+1:tag2_pos1].strip()


#  Split string in exactly two pieces, return '' for missing pieces.
def split2(s,sep):
	parts = s.split(sep,1) + ["",""]
	return parts[0], parts[1]

#  Use hash and secret to encrypt string.
def makehash(s,secert):
	m = md5.new()
	m.update(s)
	m.update(secret)
	return m.hexdigest()[0:8]
	
	
#  Form cookie
def make_pycas_cookie(val, domain, path, secure, expires=None):
	cookie = "Set-Cookie: %s=%s;domain=%s;path=%s" % (PYCAS_NAME, val, domain, path)
	if secure:
		cookie += ";secure"
	if expires:
		cookie += ";expires=" + expires
	return cookie

#  Send redirect to client.  This function does not return, i.e. it teminates this script.
def do_redirect(cas_host, service_url, opt, secure):
	cas_url  = cas_host + "/cas/login?service=" + service_url
	if opt in ("renew","gateway"):
		cas_url += "&%s=true" % opt
	#  Print redirect page to browser
	print "Refresh: 0; url=%s" % cas_url
	print "Content-type: text/html"
	if opt=="gateway":
		domain,path = urlparse.urlparse(service_url)[1:3]
		print make_pycas_cookie("gateway", domain, path, secure)
	print """
If your browser does not redirect you, then please follow <a href="%s">this link</a>.
""" % (cas_url)
	raise SystemExit

#  Send redirect to client.  This function does not return, i.e. it teminates this script.
def get_url_redirect_as_string(cas_host, service_url, opt, secure):
	cas_url  = cas_host + "/cas/login?service=" + service_url
	if opt in ("renew","gateway"):
		cas_url += "&%s=true" % opt
	#  Print redirect page to browser

        return cas_url

def get_cookie_as_string(cas_host, service_url, opt, secure):
	if opt=="gateway":
		domain,path = urlparse.urlparse(service_url)[1:3]
		return make_pycas_cookie("gateway", domain, path, secure)
# I'm not sure what the Else should be---it would have been clearer if
# this were functional rather than imperative.

	



#  Retrieve id from pycas cookie and test data for validity 
# (to prevent mailicious users from falsely authenticating).
#  Return status and id (id will be empty string if unknown).
def decode_cookie(cookie_vals,cas_secret,lifetime=None):

	#  Test for now cookies
	if cookie_vals is None:
		return COOKIE_NONE, ""

	#  Test each cookie value
	cookie_attrs = []
	for cookie_val in cookie_vals:
		#  Remove trailing ;
		if cookie_val and cookie_val[-1]==";":
			cookie_val = cookie_val[0:-1]

		#  Test for pycas gateway cookie
		if cookie_val=="gateway":
			cookie_attrs.append(COOKIE_GATEWAY)

		#  Test for valid pycas authentication cookie.
		else:
			# Separate cookie parts
			oldhash     = cookie_val[0:8]
			timestr, id_ = split2(cookie_val[8:],":")
			#  Verify hash
			newhash=makehash(timestr + ":" + id_, cas_secret)
			if oldhash==makehash(timestr + ":" + id_, cas_secret):
				#  Check lifetime
				if lifetime:
					if str(int(time.time()+int(lifetime)))<timestr:
						#  OK:  Cookie still valid.
						cookie_attrs.append(COOKIE_AUTH)
					else:
						# ERROR:  Cookie exceeded lifetime
						cookie_attrs.append(COOKIE_EXPIRED)
				else:
					#  OK:  Cookie valid (it has no lifetime)
					cookie_attrs.append(COOKIE_AUTH)
					
			else:
				#  ERROR:  Cookie value are not consistent
				cookie_attrs.append(COOKIE_INVALID)

	#  Return status according to attribute values

	#  Valid authentication cookie takes precedence
	if COOKIE_AUTH in cookie_attrs:
		return COOKIE_AUTH, id_
	#  Gateway cookie takes next precedence
	if COOKIE_GATEWAY in cookie_attrs:
		return COOKIE_GATEWAY, ""
	#  If we've gotten here, there should be only one attribute left.
	return cookie_attrs[0], ""


#  Validate ticket using cas 1.0 protocol
def validate_cas_1(cas_host, service_url, ticket):
	#  Second Call to CAS server: Ticket found, verify it.
	cas_validate = cas_host + "/cas/validate?ticket=" + ticket + "&service=" + service_url
	f_validate   = urllib.urlopen(cas_validate)
	#  Get first line - should be yes or no
	response = f_validate.readline()
	#  Ticket does not validate, return error
	if response=="no\n":
		f_validate.close()
		return TICKET_INVALID, ""
	#  Ticket validates
	else:
		#  Get id
		id_ = f_validate.readline()
		f_validate.close()
		id_ = id_.strip()
		return TICKET_OK, id_



#  Validate ticket using cas 2.0 protocol
#    The 2.0 protocol allows the use of the mutually exclusive "renew" and "gateway" options.
def validate_cas_2(cas_host, service_url, ticket, opt):
	#  Second Call to CAS server: Ticket found, verify it.
	cas_validate = cas_host + "/cas/serviceValidate?ticket=" + ticket + "&service=" + service_url
	if opt:
		cas_validate += "&%s=true" % opt
	f_validate   = urllib.urlopen(cas_validate)
	#  Get first line - should be yes or no
	response = f_validate.read()
	id_ = parse_tag(response,"cas:user")
	#  Ticket does not validate, return error
	if id_ == "":
		return TICKET_INVALID, ""
	#  Ticket validates
	else:
		return TICKET_OK, id_


#  Validate ticket using cas 2.0 protocol
#    The 2.0 protocol allows the use of the mutually exclusive "renew" and "gateway" options.
def validate_cas_2x_urllib(cas_host, cas_proxy, service_url, ticket, opt):

	#  Second Call to CAS server: Ticket found, verify it.
	cas_validate = cas_host + "/cas/serviceValidate?ticket=" + ticket + "&service=" + service_url
	if opt:
		cas_validate += "&%s=true" % opt

	f_validate   = urllib.urlopen(cas_validate)
	#  Get first line - should be yes or no
	response = f_validate.read()

	id_ = parse_tag(response,"cas:user")
	#  Ticket does not validate, return error
	if id == "":
		return TICKET_INVALID, "", "", ""
	#  Ticket validates
	else:
                pivcard = parse_tag(response,"maxAttribute:samlAuthenticationStatementAuthMethod")
                agencyThatRequired = parse_tag(response,"maxAttribute:EAuth-LOA")
		return TICKET_OK, id_, pivcard, agencyThatRequired

def validate_cas_2x(cas_host, cas_proxy, service_url, ticket, opt):

	#  Second Call to CAS server: Ticket found, verify it.
	cas_validate = cas_host + "/cas/serviceValidate?ticket=" + ticket + "&service=" + service_url
	if opt:
		cas_validate += "&%s=true" % opt
#        writelog("cas_validate = "+cas_validate)
#   f_validate   = urllib.urlopen(cas_validate)
	#  Get first line - should be yes or no
#	response = f_validate.read()
 #       writelog("response = "+response)
 	r = requests.get(cas_validate,proxies=cas_proxy)
 	response = r.text
	id_ = parse_tag(response,"cas:user")
	#  Ticket does not validate, return error
	if id_ == "":
		return TICKET_INVALID, "", "", ""
	#  Ticket validates
	else:
#                writelog("validate response = "+response)
                pivcard = parse_tag(response,"maxAttribute:samlAuthenticationStatementAuthMethod")
                
                eauth_but_not_valid = parse_tag(response,"maxAttribute:EAuth-LOA")
#                writelog("pivcard = "+pivcard)
#                writelog("agencyThatRequired = "+agencyThatRequired)
		return TICKET_OK, id_, pivcard, eauth_but_not_valid


#  Read cookies from env variable HTTP_COOKIE.
def get_cookies():
	#  Read all cookie pairs
	try:
		cookie_pairs = os.getenv("HTTP_COOKIE").split()
	except AttributeError:
		cookie_pairs = []
	cookies = {}
	for cookie_pair in cookie_pairs:
		key,val = split2(cookie_pair.strip(),"=")
		if cookies.has_key(key):
			cookies[key].append(val)
		else:
			cookies[key] = [val,]
	return cookies


#  Check pycas cookie
def get_cookie_status(cas_secret):
	cookies = get_cookies()
	return decode_cookie(cookies.get(PYCAS_NAME),cas_secret)


def get_ticket_status(cas_host,service_url,protocol,opt):
	if cgi.FieldStorage().has_key("ticket"):
		ticket = cgi.FieldStorage()["ticket"].value
                return get_ticket_status_from_ticket(ticket,cas_host,service_url,protocol,opt)
	else:
                writelog("returning TICKET_NONE ")
		return TICKET_NONE, ""

def get_ticket_status_from_ticket(ticket,cas_host,service_url,protocol,opt):
        if protocol==1:
                ticket_status, id_=validate_cas_1(cas_host, service_url, ticket, opt)
        else:
                ticket_status, id_=validate_cas_2(cas_host, service_url, ticket, opt)

#        writelog("ticket status"+repr(ticket_status))
        #  Make cookie and return id
        if ticket_status==TICKET_OK:
                return TICKET_OK, id_
        #  Return error status
        else:
                return ticket_status, ""

def get_ticket_status_from_ticket_piv_required(assurancelevel_p,ticket,cas_host,cas_proxy,service_url,protocol,opt):
        if protocol==1:
                ticket_status, id_ = validate_cas_1(cas_host, service_url, ticket, opt)
        else:
                ticket_status, id_, piv, eauth=validate_cas_2x(cas_host, cas_proxy, service_url, ticket, opt)

#        writelog("ticket status"+repr(ticket_status))
#        writelog("piv status"+repr(piv))
#        writelog("pivx status"+repr(pivx))
        #  Make cookie and return id
        # MAX is actually returning a value here (in pivx), I think I need
        # to search for "assurancelevel3", because it is sending 
        # "assurance2" when there is no PIV card!
#        if ticket_status==TICKET_OK and (piv == "urn:max:fips-201-pivcard" or  (assurancelevel_p(pivx))):

        # This is supposed to be a simple boolean!  But...
        # it is returning a set containing a boolean!  I know not why.
        if ticket_status==TICKET_OK and (True in assurancelevel_p(eauth,piv)):
                return TICKET_OK, id_
        #  Return error status
        else:
                if ticket_status==TICKET_OK:
                        return TICKET_NOPIV, ""
                else:
                        return TICKET_NONE, ""


#-----------------------------------------------------------------------
#  Exported functions
#-----------------------------------------------------------------------

# This function should be merged with the above function "login"

# Note:  assurcane_level_p is a a function applied to return results.
# I takes to arguments and should look something like this:
# CAS_LEVEL_OF_ASSURANCE_PREDICATE_LOA2_AND_PIV = lambda loa,piv: {
#   (("http://idmanagement.gov/icam/2009/12/saml_2.0_profile/assurancelevel2" == loa)
#    or
#  ("http://idmanagement.gov/icam/2009/12/saml_2.0_profile/assurancelevel3" == loa))
#  and
#   ("urn:max:fips-201-pivcard" == piv)
#
# }
def check_authenticated_p(assurance_level_p,ticket,cas_host,cas_proxy,cas_secret,service_url, lifetime=None, secure=1, protocol=2, path="/", opt=""):

 #       writelog("login begun")
	#  Check cookie for previous pycas state, with is either
	#     COOKIE_AUTH    - client already authenticated by pycas.
	#     COOKIE_GATEWAY - client returning from CAS_SERVER with gateway option set.
	#  Other cookie status are 
	#     COOKIE_NONE    - no cookie found.
	#     COOKIE_INVALID - invalid cookie found.
	cookie_status, id_ = get_cookie_status(cas_secret)

 #       writelog("got cookie status")

	if cookie_status==COOKIE_AUTH:
                writelog("CAS_OK")
		return CAS_OK, id_, ""

	if cookie_status==COOKIE_INVALID:
		return CAS_COOKIE_INVALID, "", ""

	#  Check ticket ticket returned by CAS server, ticket status can be
	#     TICKET_OK      - a valid authentication ticket from CAS server
	#     TICKET_INVALID - an invalid authentication ticket.
	#     TICKET_NONE    - no ticket found.
	#  If ticket is ok, then user has authenticated, return id and 
	#  a pycas cookie for calling program to send to web browser.

#        writelog("getting cookie status")

	ticket_status, id_ = get_ticket_status_from_ticket_piv_required(assurance_level_p,ticket,cas_host,cas_proxy,service_url,protocol,opt)

	if ticket_status==TICKET_OK:
		timestr     = str(int(time.time()))
		hash_        = makehash(timestr + ":" + id_, cas_secret)
		cookie_val  = hash_ + timestr + ":" + id_
		domain      = urlparse.urlparse(service_url)[1]
		return CAS_OK, id_, make_pycas_cookie(cookie_val, domain, path, secure)

	elif ticket_status==TICKET_INVALID:
		return CAS_TICKET_INVALID, "", ""


	#  If unathenticated and in gateway mode, return gateway status and clear
	#  pycas cookie (which was set to gateway by do_redirect()).
	if opt=="gateway":
		if cookie_status==COOKIE_GATEWAY:
			domain,path = urlparse.urlparse(service_url)[1:3]
			#  Set cookie expiration in the past to clear the cookie.
			past_date = time.strftime("%a, %d-%b-%Y %H:%M:%S %Z",time.localtime(time.time()-48*60*60))
			return CAS_GATEWAY, "", make_pycas_cookie("",domain,path,secure,past_date)
        return CAS_TICKET_INVALID, "", ""


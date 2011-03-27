#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright © 2011 Guy Sheffer <guysoft@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
Created on Mar 7, 2011

@author: Guy Sheffer <guysoft@gmail.com>
'''


import sqlite3

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth

#import Transliterate
import cgitb
import cgi


cgitb.enable()

print "Content-Type: text/plain;charset=utf-8"
print

'''
consumer_key =''
consumer_secret = ''
'''
from gate_config import *

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'

'''
def getToken():
		auth = tweepy.OAuthHandler(consumer_key,consumer_secret )
		
		try:
			redirect_url = auth.get_authorization_url()
		except tweepy.TweepError:
			print 'Error! Failed to get request token.'
			
		return redirect_url
'''
def getOauthToken():
	signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
	oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
	oauth_client               = oauth.Client(oauth_consumer)
	resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')
	
	request_token = dict(parse_qsl(content))
	
	if resp['status'] == '200':
		return request_token['oauth_token'], request_token['oauth_token_secret']
	else:
		print "error getting token"
	return
		
		

def store(phone,token,oauth_token_secret):
	
	conn = sqlite3.connect(DB_PATH)
	c = conn.cursor()
	
	#remove previous attempts
	sql = "delete from phonelist  where phone=?"
	
	
	variables = (phone,)
	c.execute(sql,variables)
	
	
	c.close()
	
	c = conn.cursor()
	
	# Insert a row of data
	sql = "insert into phonelist  values (?,?,?)"
	variables = (token,oauth_token_secret,phone)
	
	c.execute(sql,variables)	
	# Save (commit) the changes
	conn.commit()
	

	
	# We can also close the cursor if we are done with it
	c.close()
	
	
	
	
	return

def getTokenUrl(phone):
	oauth_token,oauth_token_secret = getOauthToken()
	store(phone,oauth_token,oauth_token_secret)
	
	
	print '%s?oauth_token=%s' % (AUTHORIZATION_URL, oauth_token)
	
# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
phone = form.getvalue('phone')
phone = phone.replace(" ","").replace("-","")
if phone.startswith("0"):
	phone = COUNTRY_PREFIX + phone[1:]

if phone!= None:
	#print phone
	
	getTokenUrl(phone)
	#create a token and add to db

    
else:
  print 'Please enter a number'

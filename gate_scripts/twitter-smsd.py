#!/usr/bin/python
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
Created on Feb 9, 2011

@author: Guy Sheffer <guysoft@gmail.com>
'''

import os
import sys
import TwitterBot
import tweepy
import sqlite3
import time
import traceback
import shutil
from twitter import TwitterError

from gate_config import *
'''
consumer_key =''
consumer_secret = ''
DB_PATH ="/path/to/gate_scripts/smstwitter.sqlite"
LOG_PATH="/path/to/gate_scripts/sms_gate.log"
'''

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class SMSdeamon():
    '''
    Main class of our daemon __init__ is invoked on any new incoming SMS
    '''

    def debug(self,message):
        '''
        Send debug calls to a logfile, its useful because we can't see a shell at runtime
        '''
        try:
            message = message.encode("utf-8")
        except:
            self.debug("on message")
        try:
            print message
        except:
            self.debug("on print")
        try:
            self.f.write(time.strftime("%Y/%m/%d %H:%M:%S ", time.localtime()) + str(message) + "\n");
        except:
            self.debug("on write")
        return
        
        
    def getKey(self,key,tokenSecret,pin):
        '''
        Returns a turple of the key and secret
        '''
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_request_token(key, tokenSecret)
        
        
        
        try:
            auth.get_access_token(pin)
            self.debug(auth.access_token.key)
            self.debug(auth.access_token.secret)
            return auth.access_token.key,auth.access_token.secret
        except tweepy.TweepError:
            self.debug('Error! Failed to get access token.')
        return 
    
    def __init__(self):
        '''
        Init all the gateway services
        '''
        self.f = open(LOG_PATH,'a')
        self.debug("\nIncoming SMS:")
        SMS_MESSAGES = os.environ['SMS_MESSAGES']
        
        for i in range(1,int(SMS_MESSAGES) + 1):
            message = os.environ['SMS_' + str(i)+'_TEXT']
            number = os.environ['SMS_' + str(i)+'_NUMBER']
            
            
            '''
            #Here one can debug other gates
            if number == '+972123456789':
                a = TwitterBot.Bot("COSTOMER_TOKEN",'CUSTOMER_SECRET')
                try:
                    a.Tweet(message)
                except AttributeError:
                    self.debug("Got a module' object has no attribute error on tweet send")
            
            else:
            
                self.TwitterGateway(number,message)
            '''
            self.TwitterGateway(number,message)
        
        self.f.close()
        return
        
    def TwitterGateway(self,number,message):
        '''
        This is the twitter gateway, it will check if s user is authenticated, if so it will post the message
        If the user is not in our registered users, its assumed we got a pin authentication number,
        and we will try and authenticate him over twitter, if we find his number in the list of numbers pending authentication
        '''
        self.debug('checking if ' +  number[1:] + ' in auth table')
        newUser = True;#is this a register attempt
        try:
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            variables = (number[1:],)
            
            sql = 'select * from auth where phone=?';
            print sql
            c.execute(sql,variables)
            
            for row in c:#should run once
                self.debug('Found ' +  number[1:] + ' in auth table')
                newUser = False;
                key = row[0]
                number = row[1]
                secret = row[2]
                
                self.debug(row)
                
                #THERE IS A BUG HERE!!!
                try:
                    debug = number +" Preparing to tweet:" + message.decode("utf-8")
                    self.debug(debug)
                except:
                    self.debug("Er - can't print your tweet")
                
                #we have an auth for this number, lets tweet for him.
                try:
                    a = TwitterBot.Bot(key,secret)
                    a.Tweet(message)
                    self.debug("Successful")
                except (AttributeError,ValueError) as e:
                    self.debug(e.message)
                    self.debug("Got a module' object has no attribute error on tweet send")
                except TwitterError as e:
                    self.debug(e.message)
                    self.debug("Trying again to tweet in 10 seconds")
                    try:
                        time.sleep(10)
                        a = TwitterBot.Bot(key,secret)
                        a.Tweet(message)
                        self.debug("Successful on second attempt")
                    except:
                        self.debug("failed on second tweet attempt")
                break;
            c.close()

        
            if newUser:
                self.debug('Not Found ' +  number[1:] + ' in auth table, testing in phonelist')
                
                self.debug("im new")
                sql = 'select * from phonelist where phone=?';
                
                c = conn.cursor()
                variables = (number[1:],)
                c.execute(sql,variables)
                
                for row in c:#should run once
                    self.debug('Found ' +  number[1:] + ' in phonelist, authing with ' + message)
                    #print row
                    serverToken = row[0]
                    tokenSecret = row[1]
                    phone = row[2]
                                      
                    message = message.rstrip()
                    
                    c.close()
                    
                    #lets try and authenticate
                    #message = message.strip(u'\u200F')
                    if not is_number(message):
                        message = filter( lambda x: x in '0123456789.', message )
                        self.debug("striping to " + message)
                    userKey,userSecret = self.getKey(serverToken,tokenSecret,message)
                    
                    c = conn.cursor()
                               
                    # Insert a row of data
                    sql = "insert into auth  values (?,?,?)"
                    variables = (userKey,phone,userSecret)
                    
                    c.execute(sql,variables)    
                    # Save (commit) the changes
                    conn.commit()
                    break;
        except:
            conn.close()
            #traceback.print_stack()
            self.debug("exception!")
            
            try:
                traceback.print_exc(self.f)
            except:
                pass
                    
        conn.close()#its important to close the db even after an exception! Otherwise db might break
        self.debug("Closing db")
        return

        

if __name__ == '__main__':
    #I recommend to uncomment this if you are running a small gate and don't want to loose the DB, backup backup!
    #shutil.copy(DB_PATH, DB_PATH +'.' + str(time.time()))
    a = SMSdeamon()


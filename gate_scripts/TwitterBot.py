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
Created on Feb 7, 2011

@author: Guy Sheffer <guysoft@gmail.com>
'''

import tweepy
import twitter
from twitter import TwitterError

import time
from threading import Thread
import sys
from urllib2 import URLError

#added for internal stuff
import subprocess
import random
import os
import dateutil.parser
import sqlite3
import datetime
import traceback

from gate_config import *

#NOTE: This is not the same DB form the gate_config, might want to merge this one day
DB_PATH = '';
'''
consumer_key =''
consumer_secret = ''
'''

key = ''
token = ''

serverKey=''
secret =''

REMINDER_OFFSET = 120

class Bot():
    '''
    A twitter bot, can do many things
    '''
    SLEEP_TIME = 70;
    TWEETS_LENGTH = 140;
        
    
    class TweetCounter(Thread):
        def __init__(self,bot,user,step):
            '''
            The bot object, the user and how many messages for each step
            '''
            Thread.__init__(self)
            
            self.lastTweet = 0 #when we last told the user
            self.step = step;
            self.user = user;
            self.bot = bot
            
        def run(self):
            guyTweetCount = self.bot.getTweetCount(self.user) + 5
            while self.bot.getRunning():
                try:
                    newguyTweetCount = self.bot.getTweetCount(self.user) + 5
                    
                    if newguyTweetCount > guyTweetCount:
                        self.bot.debug('user:' + self.user + " count:" + str(newguyTweetCount))
                        if ((guyTweetCount + 1) / self.step != guyTweetCount/self.step) and guyTweetCount > self.lastTweet:
                            self.bot.Tweet("@"+ self.user+" you are five tweets away from your " + str(guyTweetCount + 1) + ' tweet')
                            self.lastTweet = guyTweetCount;
                    
                    if guyTweetCount <= newguyTweetCount:
                        guyTweetCount = newguyTweetCount
                except URLError:
                    self.bot.debug("failed to pull url: URLError at run")
                except ValueError:
                    self.bot.debug("failed to pull url: ValueError at run")
                except:
                    self.bot.debug("error on pulling, not sure why")
                time.sleep(self.bot.SLEEP_TIME)
            return
            
    

            
        
    
    def getToken(self):
        auth = tweepy.OAuthHandler(consumer_key,consumer_secret )
        
        try:
            redirect_url = auth.get_authorization_url()
        except tweepy.TweepError:
            print 'Error! Failed to get request token.'
            
        print redirect_url
        
    def getKey(self):
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_request_token(key, secret)


        try:
            auth.get_access_token(token)
        except tweepy.TweepError:
            print 'Error! Failed to get access token.'
            
        print auth.access_token.key
        print auth.access_token.secret
        
        return
    
    def debug(self,message):
        '''
        Print a debug message
        '''
        try:    
            output= time.strftime("%Y/%m/%d %H:%M:%S ", time.localtime()) + str(message)
        except UnicodeEncodeError:
            output= time.strftime("%Y/%m/%d %H:%M:%S ", time.localtime()) + str(message.encode("utf-8"))
        print output
        return
    
    def Tweet(self,message,in_reply_to_status_id=None):
        '''
        Tweet a message
        '''
        self.api.PostUpdate(message, in_reply_to_status_id)
        self.debug('Tweeting:' + message)
        return
    
    def setRunning(self,status):
        self.running = status
        return
    def getRunning(self):
        return self.running
    
    def __init__(self,serverKey,access_token_secret):
        self.threads = []#the list of threads
        '''
        
        #search handlers
        
        self.addUserHandler("guysoft",self.onGuysoft)
        
        '''
        
        self.api = twitter.Api(consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        access_token_key=serverKey,
                        access_token_secret=access_token_secret)
        
        
    def initUsername(self):
        self.username =  self.api.VerifyCredentials().screen_name    
        
    def run(self):
        self.setRunning(True)
        for t in self.threads:
            t.start()
            
        while self.running:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self.debug('Got Key interrupt')
                self.setRunning(False)
                    
                sys.exit()
        return
    
    def tweetCounter(self,user,step):
        '''
        This function monitors a given user's tweets, and tweets at that user when 1 tweet away from the step
        '''
        guyTweetCount = self.getTweetCount(user) + 5
        while self.running:
            newguyTweetCount = self.getTweetCount(user) + 5
            if newguyTweetCount != guyTweetCount:
                self.debug('user:' + user + " count:" + str(newguyTweetCount))
                if (guyTweetCount + 1) / step != guyTweetCount/step:
                    self.Tweet("@"+ user+" you are one tweet away from your " + str(guyTweetCount + 1) + ' tweet')
            guyTweetCount = newguyTweetCount
            time.sleep(70)
        return
    
    def addTweetCountHandler(self,user,step):
        #t = Thread(target=self.tweetCounter, args=(user,step))
        t=self.TweetCounter(self,user,step)
        self.threads.append(t)
        return
    
    def addSearchHandler(self,search,func):
        t = Thread(target=self.searchHandler, args=(search,func))
        self.threads.append(t)
        return
    
    def addUserHandler(self,search,func):
        t = Thread(target=self.userHandler, args=(search,func))
        self.threads.append(t)
        return
    
    def getUsername(self):
        return self.username;
    
    def addMentionHandler(self,func,seconds=SLEEP_TIME):
        t = Thread(target=self.mentionsHandler, args=(func,seconds))
        self.threads.append(t)
        return
    
    def mentionsHandler(self,func,seconds):
        self.peridocCheck(self.api.GetMentions,func,seconds)
        return
    
    def peridocCheck(self,searchFunc,func,seconds):
        oldResults = searchFunc()

        while self.running:
            try:
                #get new results
                newResults = [];
                newResults =searchFunc()
                
                mentions = [];
                
                for newResult in newResults:
                    found = False;
                    for oldResult in oldResults:
                        if oldResult.id == newResult.id:
                            found = True;
                            break;
                        
                    if not found:
                        mentions.append(newResult)
                
                oldResults = newResults
                
                for tweet in mentions:
                    func(tweet)
            except URLError:
                self.debug("failed to pull url: URLError at peridocCheck")
            except:
                traceback.print_exc(file=sys.stdout)
                self.debug("failed to pull url: at peridocCheck")
            time.sleep(seconds)
        return
    
    def userHandler(self,search,func,seconds=SLEEP_TIME):
        userid = self.api.GetUser(search).id
        self.debug(userid)
        try:
            self.peridocCheck((lambda: self.api.GetUserTimeline(userid)),func,seconds)
        except ValueError:
            self.debug("Value Error on userHandler for "+ search)
        return
        
    def searchHandler(self,search,func,seconds=SLEEP_TIME):
        '''
        Thread function that handles a search and callback function when new result is found
        '''
        self.peridocCheck((lambda: self.api.GetSearch(search)),func,seconds)
        return


    def getTweetCount(self,user):
        return self.api.GetUser(user).statuses_count
    
    def onReply(self,tweet):
        '''
        Handles a mention to the bot
        '''
        return

    
if __name__ == '__main__':
    
    a = Bot(serverKey,secret)
    a.initUsername()
    
    a.addMentionHandler(a.onReply)
    a.run()
    

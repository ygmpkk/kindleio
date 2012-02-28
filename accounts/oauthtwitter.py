#!/usr/bin/env python
# 
# Copyright under  the latest Apache License 2.0

'''
A modification of the python twitter oauth library by Hameedullah Khan.
Instead of inheritance from the python-twitter library, it currently
exists standalone with an all encompasing ApiCall function. There are
plans to provide wrapper functions around common requests in the future.

Requires:
  simplejson
  oauth2

http://code.google.com/p/oauth-python-twitter2/
'''

__author__ = "Konpaku Kogasa, Hameedullah Khan"
__version__ = "0.1"

# Library modules
import urllib
import urllib2
import urlparse
import time

# Non library modules
from django.utils import simplejson
import oauth

from twitter import Api, User, Status, TWITTER_API

# Taken from oauth implementation at: http://github.com/harperreed/twitteroauth-python/tree/master
REQUEST_TOKEN_URL = 'https://twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'http://twitter.com/oauth/authorize'
SIGNIN_URL = 'http://twitter.com/oauth/authenticate'


class OAuthApi(Api):
    def __init__(self, consumer_key, consumer_secret, 
                 token=None, token_secret=None, verified=False):
    	if token and token_secret:
    		token = oauth.Token(token, token_secret)
    	else:
            token = None
        Api.__init__(self, verified=verified)
        self._Consumer = oauth.Consumer(consumer_key, consumer_secret)
        self._signature_method = oauth.SignatureMethod_HMAC_SHA1()
        self._access_token = token 

    def _GetOpener(self):
        opener = urllib2.build_opener()
        return opener

    def _FetchUrl(self, url, post_data=None, parameters=None):
        '''Fetch a URL, optionally caching for a specified time.
        Args:
            url: The URL to retrieve
            post_data:
                A dict of (str, unicode) key/value pairs. If set, POST will be used.
        parameters:
            A dict whose key/value pairs should encoded and added
            to the query string. [OPTIONAL]
        Returns:
            A string containing the body of the response.
        '''
        # Build the extra parameters dict
        extra_params = {}
        if self._default_params:
          extra_params.update(self._default_params)
        if parameters:
          extra_params.update(parameters)
    
        # Add key/value parameters to the query string of the url
        #url = self._BuildUrl(url, extra_params=extra_params)
    
        if post_data is not None:
            http_method = "POST"
            extra_params.update(dict([(k, self._Encode(v)) for k, v in post_data.items() if v is not None]))
        else:
            http_method = "GET"
        
        req = self._makeOAuthRequest(url, params=extra_params, http_method=http_method)

        # Get a url opener that can handle Oauth basic auth
        opener = self._GetOpener()
        
        if post_data is not None:
            encoded_post_data = req.to_postdata()
        else:
            encoded_post_data = ""
            url = req.to_url()
            
        # Open and return the URL immediately if we're not going to cache
        # OR we are posting data
        if encoded_post_data:
            url_data = opener.open(url, encoded_post_data).read()
        else:
            url_data = opener.open(url).read()
        opener.close()
    
        # Always return the latest version
        return url_data
    
    def _makeOAuthRequest(self, url, token=None,
                                        params=None, http_method="GET"):
        '''Make a OAuth request from url and parameters
        
        Args:
          url: The Url to use for creating OAuth Request
          parameters:
             The URL parameters
          http_method:
             The HTTP method to use
        Returns:
          A OAauthRequest object
        '''
        
        oauth_base_params = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time())
        }
        
        if params:
            params.update(oauth_base_params)
        else:
            params = oauth_base_params
        
        if not token:
            token = self._access_token
        request = oauth.Request(method=http_method,url=url,parameters=params)
        request.sign_request(self._signature_method, self._Consumer, token)
        return request

    def getAuthorizationURL(self, token, url=AUTHORIZATION_URL):
        '''Create a signed authorization URL
        
        Returns:
          A signed OAuthRequest authorization URL 
        '''
        req = self._makeOAuthRequest(url, token=token)
        return "%s?oauth_token=%s" % (url, req['oauth_token'])

    def getRequestToken(self, url=REQUEST_TOKEN_URL):
        '''Get a Request Token from Twitter
        
        Returns:
          A OAuthToken object containing a request token
        '''
        resp, content = oauth.Client(self._Consumer).request(url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])

        return oauth.Token.from_string(content)

    def getAccessToken(self, url=ACCESS_TOKEN_URL):
        token = self._FetchUrl(url)
        return oauth.Token.from_string(token) 

    def GetUserInfo(self, url='http://api.twitter.com/1/account/verify_credentials.json'):
        '''Get user information from twitter

        Returns:
            Returns the twitter.User object
        '''
        json = self._FetchUrl(url)
        data = simplejson.loads(json)
        self._CheckForTwitterError(data)
        return User.NewFromJsonDict(data)


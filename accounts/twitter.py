#coding=utf-8
#!/usr/bin/python2.4
#
# Copyright 2007 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''A library that provides a python interface to the Twitter API'''

__author__ = 'dewitt@google.com'
__version__ = '0.6-devel'

# make sure end with '/'
TWITTER_API = 'https://api.twitter.com/1/'

from django.utils import simplejson
import base64
import calendar
import os
import rfc822
import sys
import tempfile
import textwrap
import time
import urllib
import urllib2
import urlparse
import re
import datetime

try:
  from hashlib import md5
except ImportError:
  from md5 import md5

MONTH_STRING = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def str_to_date(ds):
    res = re.search(r'(\w{3}) (\w{3}) (\d{2}) (\d{2}):(\d{2}):(\d{2}) \+(\d{4}) (\d{4})', ds)
    if res:
        return datetime.datetime(int(res.group(8)), # year
                                MONTH_STRING.index(res.group(2)) + 1, # month
                                int(res.group(3)), # day
                                int(res.group(4)), # hour
                                int(res.group(5)), # minuite
                                int(res.group(6))) # second
    else:
        return ds


CHARACTER_LIMIT = 140

class TwitterError(Exception):
  '''Base class for Twitter errors'''
  
  @property
  def message(self):
    '''Returns the first argument used to construct this error.'''
    return self.args[0]

class Status(object):
  '''A class representing the Status structure used by the twitter API.

  The Status structure exposes the following properties:

    status.created_at
    status.created_at_in_seconds # read only
    status.favorited
    status.in_reply_to_screen_name
    status.in_reply_to_user_id
    status.in_reply_to_status_id
    status.truncated
    status.source
    status.id
    status.text
    status.relative_created_at # read only
    status.user
    status.retweeted_by
    status.retweeted_id
  '''
  def __init__(self,
               created_at=None,
               favorited=None,
               id=None,
               text=None,
               user=None,
               retweeted_by=None,
               retweeted_id=None,
               in_reply_to_screen_name=None,
               in_reply_to_user_id=None,
               in_reply_to_status_id=None,
               truncated=None,
               source=None,
               now=None):
    '''An object to hold a Twitter status message.

    This class is normally instantiated by the twitter.Api class and
    returned in a sequence.

    Note: Dates are posted in the form "Sat Jan 27 04:17:38 +0000 2007"

    Args:
      created_at: The time this status message was posted
      favorited: Whether this is a favorite of the authenticated user
      id: The unique id of this status message
      text: The text of this status message
      relative_created_at:
        A human readable string representing the posting time
      user:
        A twitter.User instance representing the person posting the message
      now:
        The current time, if the client choses to set it.  Defaults to the
        wall clock time.
    '''
    self.created_at = created_at
    self.favorited = favorited
    self.id = id
    self.text = text
    self.user = user
    self.retweeted_by = retweeted_by
    self.retweeted_id = retweeted_id
    self.now = now
    self.in_reply_to_screen_name = in_reply_to_screen_name
    self.in_reply_to_user_id = in_reply_to_user_id
    self.in_reply_to_status_id = in_reply_to_status_id
    self.truncated = truncated
    self.source = source

  def GetCreatedAtInSeconds(self):
    '''Get the time this status message was posted, in seconds since the epoch.

    Returns:
      The time this status message was posted, in seconds since the epoch.
    '''
    return calendar.timegm(rfc822.parsedate(self.created_at))

  created_at_in_seconds = property(GetCreatedAtInSeconds,
                                   doc="The time this status message was "
                                       "posted, in seconds since the epoch")


  def GetRelativeCreatedAt(self):
    '''Get a human redable string representing the posting time

    Returns:
      A human readable string representing the posting time
    '''
    delta  = long(self.now) - long(self.created_at_in_seconds)

    if delta < 60:
      return '%d sec ago' % (delta)
    elif delta < 60 * 60:
      return '%d min ago' % (delta / 60)
    elif delta < 60 * 60 * 24:
      return '%d hours ago' % (delta / (60 * 60))
    else:
      return '%d days ago' % (delta / (60 * 60 * 24))

  relative_created_at = property(GetRelativeCreatedAt,
                                 doc='Get a human readable string representing'
                                     'the posting time')

  def GetNow(self):
    '''Get the wallclock time for this status message.

    Used to calculate relative_created_at.  Defaults to the time
    the object was instantiated.

    Returns:
      Whatever the status instance believes the current time to be,
      in seconds since the epoch.
    '''
    if self._now is None:
      self._now = time.time()
    return self._now

  def SetNow(self, now):
    '''Set the wallclock time for this status message.

    Used to calculate relative_created_at.  Defaults to the time
    the object was instantiated.

    Args:
      now: The wallclock time for this instance.
    '''
    self._now = now

  now = property(GetNow, SetNow,
                 doc='The wallclock time for this status instance.')


  def __str__(self):
    '''A string representation of this twitter.Status instance.

    The return value is the same as the JSON string representation.

    Returns:
      A string representation of this twitter.Status instance.
    '''
    return self.AsJsonString()

  def AsJsonString(self):
    '''A JSON string representation of this twitter.Status instance.

    Returns:
      A JSON string representation of this twitter.Status instance
   '''
    return simplejson.dumps(self.AsDict(), sort_keys=True)

  def AsDict(self):
    '''A dict representation of this twitter.Status instance.

    The return value uses the same key names as the JSON representation.

    Return:
      A dict representing this twitter.Status instance
    '''
    data = {}
    if self.created_at:
      data['created_at'] = self.created_at
    if self.favorited:
      data['favorited'] = self.favorited
    if self.id:
      data['id'] = self.id
    if self.text:
      data['text'] = self.text
    if self.user:
      data['user'] = self.user.AsDict()
    if self.in_reply_to_screen_name:
      data['in_reply_to_screen_name'] = self.in_reply_to_screen_name
    if self.in_reply_to_user_id:
      data['in_reply_to_user_id'] = self.in_reply_to_user_id
    if self.in_reply_to_status_id:
      data['in_reply_to_status_id'] = self.in_reply_to_status_id
    if self.truncated is not None:
      data['truncated'] = self.truncated
    if self.favorited is not None:
      data['favorited'] = self.favorited
    if self.source:
      data['source'] = self.source
    return data

  @staticmethod
  def NewFromJsonDict(data, retweeted_by=None, retweeted_id=None):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.Status instance
    '''
    if 'retweeted_status' in data:
        retweeted_by = None
        if 'user' in data:
            retweeted_by = data['user']
        return Status.NewFromJsonDict(data['retweeted_status'], retweeted_by, data['id'])

    if 'user' in data:
      user = User.NewFromJsonDict(data['user'])
      if retweeted_by:
          retweeted_by = User.NewFromJsonDict(retweeted_by)
    else:
      user = None
    return Status(created_at=data.get('created_at', None),
                  favorited=data.get('favorited', None),
                  id=data.get('id', None),
                  text=data.get('text', None),
                  in_reply_to_screen_name=data.get('in_reply_to_screen_name', None),
                  in_reply_to_user_id=data.get('in_reply_to_user_id', None),
                  in_reply_to_status_id=data.get('in_reply_to_status_id', None),
                  truncated=data.get('truncated', None),
                  source=data.get('source', None),
                  user=user,
                  retweeted_by=retweeted_by,
                  retweeted_id=retweeted_id)

class SavedSearch(object):
  '''A class representing the SavedSearch structure used by the twitter API.

  The SavedSearch structure exposes the following properties:

    search.id
    search.name
    search.query
    search.created_at
    search.position
    search.url
  '''
  def __init__(self,
               id=None,
               name=None,
               query=None,
               created_at=None,
               position=None,
               url=None):
    self.id = id
    self.name = name
    self.query = query
    self.created_at = created_at
    self.position = position
    self.url = url
    
  @staticmethod
  def NewFromJsonDict(data):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.SavedSearch instance
    '''
    return SavedSearch(id=data.get('id', None),
                         name=data.get('name', None),
                         query=data.get('query', None),
                         created_at=data.get('created_at', None),
                         position=data.get('position', None),
                         url=data.get('url', None))


class SearchResult(object):
  '''A class representing the SearchResult structure used by the twitter API.

  The SearchResult structure exposes the following properties:
    SearchResult.id
    SearchResult.text
    SearchResult.to_user_id
    SearchResult.to_user
    SearchResult.from_user_id
    SearchResult.from_user
    SearchResult.iso_language_code
    SearchResult.geo
    SearchResult.source
    SearchResult.profile_image_url
    SearchResult.created_at
  '''
  def __init__(self,
               id=None,
               text=None,
               to_user_id=None,
               to_user=None,
               from_user_id=None,
               from_user=None,
               iso_language_code=None,
               geo=None,
               source=None,
               profile_image_url=None,
               created_at=None):
    self.id=id
    self.text=text
    self.to_user_id=to_user_id
    self.to_user=to_user
    self.from_user_id=from_user_id
    self.from_user=from_user
    self.iso_language_code=iso_language_code
    self.geo=geo
    self.source=source
    self.profile_image_url=profile_image_url
    self.created_at=created_at
    
  @staticmethod
  def NewFromJsonDict(data):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.SavedSearch instance
    '''
    return SearchResult(id=data.get('id'),
                           text=data.get('text'),
                           to_user_id=data.get('to_user_id'),
                           to_user=data.get('to_user'),
                           from_user_id=data.get('from_user_id'),
                           from_user=data.get('from_user'),
                           iso_language_code=data.get('iso_language_code'),
                           geo=data.get('geo'),
                           source=data.get('source'),
                           profile_image_url=data.get('profile_image_url'),
                           created_at=data.get('created_at'))


class List(object):
  '''A class representing the List structure used by the twitter API.

  The List structure exposes the following properties:

    list.id
    list.name
    list.mode
    list.uri
    list.full_name
    list.member_count
    list.subscriber_count
    list.user
    list.slug
  '''
  def __init__(self,
               id=None,
               name=None,
               mode=None,
               uri=None,
               full_name=None,
               member_count=None,
               subscriber_count=None,
               user=None,
               slug=None):
    self.id = id
    self.name = name
    self.mode = mode
    self.uri = uri
    self.full_name = full_name
    self.member_count = member_count
    self.subscriber_count = subscriber_count
    self.user = user
    self.slug = slug
    
  @staticmethod
  def NewFromJsonDict(data):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.List instance
    '''
    if 'user' in data:
      user = User.NewFromJsonDict(data['user'])
    else:
      user = None
    return List(id=data.get('id', None),
                 name=data.get('name', None),
                 mode=data.get('mode', None),
                 uri=data.get('uri', None),
                 full_name=data.get('full_name', None),
                 member_count=data.get('member_count', None),
                 subscriber_count=data.get('member_count', None),
                 slug=data.get('slug', None),
                 user=user)

class User(object):
  '''A class representing the User structure used by the twitter API.

  The User structure exposes the following properties:

    user.id
    user.name
    user.screen_name
    user.location
    user.description
    user.url
    user.protected
    user.followers_count
    user.friends_count
    user.statuses_count
    user.favourites_count
    user.created_at
    user.utc_offset
    user.time_zone
    user.notifications
    user.verified
    user.following
    user.status
    user.profile_image_url
    user.profile_image_bigger_url
    user.profile_background_color
    user.profile_text_color
    user.profile_link_color
    user.profile_sidebar_fill_color
    user.profile_sidebar_border_color
    user.profile_background_image_url
    user.profile_background_tile

    user.tweet_rate
  '''
  def __init__(self,
               id=None,
               name=None,
               screen_name=None,
               location=None,
               description=None,
               profile_image_url=None,
               url=None,
               protected=None,
               followers_count=None,
               friends_count=None,
               statuses_count=None,
               favourites_count=None,
               created_at=None,
               utc_offset=None,
               time_zone=None,
               notifications=None,
               verified=None,
               following=None,
               status=None,
               profile_background_tile=None,
               profile_background_image_url=None,
               profile_sidebar_fill_color=None,
               profile_sidebar_border_color=None,
               profile_background_color=None,
               profile_link_color=None,
               profile_text_color=None,
               ):
    self.id = id
    self.name = name
    self.screen_name = screen_name
    self.location = location
    self.description = description
    self.profile_image_url = profile_image_url
    if profile_image_url:
        self.profile_image_bigger_url = profile_image_url.replace("_normal", "_bigger")
    else:
        self.profile_image_bigger_url = None
    self.url = url
    self.protected = protected
    self.followers_count = followers_count
    self.friends_count = friends_count
    self.statuses_count = statuses_count
    self.favourites_count = favourites_count
    self.created_at = created_at
    self.utc_offset = utc_offset
    self.time_zone = time_zone
    self.notifications = notifications
    self.verified = verified
    self.following = following
    self.status = status
    self.profile_background_tile = profile_background_tile
    self.profile_background_image_url = profile_background_image_url
    self.profile_sidebar_fill_color = profile_sidebar_fill_color
    self.profile_sidebar_border_color = profile_sidebar_border_color
    self.profile_background_color = profile_background_color
    self.profile_link_color = profile_link_color
    self.profile_text_color = profile_text_color
    self.CalcTweetRate()

  def __str__(self):
    '''A string representation of this twitter.User instance.

    The return value is the same as the JSON string representation.

    Returns:
      A string representation of this twitter.User instance.
    '''
    return self.AsJsonString()

  def AsJsonString(self):
    '''A JSON string representation of this twitter.User instance.

    Returns:
      A JSON string representation of this twitter.User instance
   '''
    return simplejson.dumps(self.AsDict(), sort_keys=True)

  def AsDict(self):
    '''A dict representation of this twitter.User instance.

    The return value uses the same key names as the JSON representation.

    Return:
      A dict representing this twitter.User instance
    '''
    
    data = {}
    if self.id:
      data['id'] = self.id
    if self.name:
      data['name'] = self.name
    if self.screen_name:
      data['screen_name'] = self.screen_name
    if self.location:
      data['location'] = self.location
    if self.description:
      data['description'] = self.description
    if self.profile_image_url:
      data['profile_image_url'] = self.profile_image_url
    if self.profile_image_bigger_url:
      data['profile_image_bigger_url'] = self.profile_image_bigger_url
    if self.url:
      data['url'] = self.url  
    if self.protected is not None:
      data['protected'] = self.protected
    if self.friends_count:
      data['friends_count'] = self.friends_count
    if self.followers_count:
      data['followers_count'] = self.followers_count
    if self.statuses_count:
      data['statuses_count'] = self.statuses_count
    if self.favourites_count:
      data['favourites_count'] = self.favourites_count
    if self.created_at:
      data['created_at'] = self.created_at
    if self.utc_offset:
      data['utc_offset'] = self.utc_offset
    if self.time_zone:
      data['time_zone'] = self.time_zone
    if self.notifications:
      data['notifications'] = self.notifications
    if self.verified:
      data['verified'] = self.verified
    if self.following:
      data['following'] = self.following
    if self.status:
      data['status'] = self.status.AsDict()
        
    if self.profile_background_tile:
      data['profile_background_tile'] = self.profile_background_tile
    if self.profile_background_image_url:
      data['profile_background_image_url'] = self.profile_background_image_url
    if self.profile_background_color:
      data['profile_background_color'] = self.profile_background_color
    if self.profile_link_color:
      data['profile_link_color'] = self.profile_link_color
    if self.profile_text_color:
      data['profile_text_color'] = self.profile_text_color
    if self.profile_sidebar_fill_color:
      data['profile_sidebar_fill_color'] = self.profile_sidebar_fill_color
    if self.profile_sidebar_border_color:
      data['profile_sidebar_border_color'] = self.profile_sidebar_border_color
    return data

  def CalcTweetRate(self):
    try:
      since = str_to_date(self.created_at)
      age = (datetime.datetime.now() - since).days
      if age <= 0:
        age = 1
      self.tweet_rate = "%.1f" % (self.statuses_count * 1.0 / age)
    except:
      self.tweet_rate = "N/A"

  @staticmethod
  def NewFromJsonDict(data):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.User instance
    '''
    if 'status' in data:
      status = Status.NewFromJsonDict(data['status'])
    else:
      status = None
    return User(id=data.get('id', None),
                name=data.get('name', None),
                screen_name=data.get('screen_name', None),
                location=data.get('location', None),
                description=data.get('description', None),
                statuses_count=data.get('statuses_count', None),
                followers_count=data.get('followers_count', None),
                favourites_count=data.get('favourites_count', None),
                friends_count=data.get('friends_count', None),
                profile_image_url=data.get('profile_image_url', None),
                profile_background_tile = data.get('profile_background_tile', None),
                profile_background_image_url = data.get('profile_background_image_url', None),
                profile_sidebar_fill_color = data.get('profile_sidebar_fill_color', None),
                profile_sidebar_border_color = data.get('profile_sidebar_border_color', None),
                profile_background_color = data.get('profile_background_color', None),
                profile_link_color = data.get('profile_link_color', None),
                profile_text_color = data.get('profile_text_color', None),
                protected = data.get('protected', None),
                utc_offset = data.get('utc_offset', None),
                time_zone = data.get('time_zone', None),
                following = data.get('following', None),
                created_at = data.get('created_at', None),
                notifications = data.get('notifications', None),
                verified = data.get('verified', None),
                url=data.get('url', None),
                status=status)

class DirectMessage(object):
  '''A class representing the DirectMessage structure used by the twitter API.

  The DirectMessage structure exposes the following properties:

    direct_message.id
    direct_message.created_at
    direct_message.created_at_in_seconds # read only
    direct_message.sender_id
    direct_message.sender_screen_name
    direct_message.recipient_id
    direct_message.recipient_screen_name
    direct_message.text
  '''

  def __init__(self,
               id=None,
               created_at=None,
               sender=None,
               sender_id=None,
               sender_screen_name=None,
               recipient_id=None,
               recipient_screen_name=None,
               text=None):
    '''An object to hold a Twitter direct message.

    This class is normally instantiated by the twitter.Api class and
    returned in a sequence.

    Note: Dates are posted in the form "Sat Jan 27 04:17:38 +0000 2007"

    Args:
      id: The unique id of this direct message
      created_at: The time this direct message was posted
      sender_id: The id of the twitter user that sent this message
      sender_screen_name: The name of the twitter user that sent this message
      recipient_id: The id of the twitter that received this message
      recipient_screen_name: The name of the twitter that received this message
      text: The text of this direct message
    '''
    self.sender = sender
    self.id = id
    self.created_at = created_at
    self.sender_id = sender_id
    self.sender_screen_name = sender_screen_name
    self.recipient_id = recipient_id
    self.recipient_screen_name = recipient_screen_name
    self.text = text

  def GetId(self):
    '''Get the unique id of this direct message.

    Returns:
      The unique id of this direct message
    '''
    return self._id

  def SetId(self, id):
    '''Set the unique id of this direct message.

    Args:
      id: The unique id of this direct message
    '''
    self._id = id

  id = property(GetId, SetId,
                doc='The unique id of this direct message.')

  def GetCreatedAtInSeconds(self):
    '''Get the time this direct message was posted, in seconds since the epoch.

    Returns:
      The time this direct message was posted, in seconds since the epoch.
    '''
    return calendar.timegm(rfc822.parsedate(self.created_at))

  created_at_in_seconds = property(GetCreatedAtInSeconds,
                                   doc="The time this direct message was "
                                       "posted, in seconds since the epoch")

  def GetSenderId(self):
    '''Get the unique sender id of this direct message.

    Returns:
      The unique sender id of this direct message
    '''
    return self._sender_id

  def SetSenderId(self, sender_id):
    '''Set the unique sender id of this direct message.

    Args:
      sender id: The unique sender id of this direct message
    '''
    self._sender_id = sender_id

  sender_id = property(GetSenderId, SetSenderId,
                doc='The unique sender id of this direct message.')

  def GetSenderScreenName(self):
    '''Get the unique sender screen name of this direct message.

    Returns:
      The unique sender screen name of this direct message
    '''
    return self._sender_screen_name

  def SetSenderScreenName(self, sender_screen_name):
    '''Set the unique sender screen name of this direct message.

    Args:
      sender_screen_name: The unique sender screen name of this direct message
    '''
    self._sender_screen_name = sender_screen_name

  sender_screen_name = property(GetSenderScreenName, SetSenderScreenName,
                doc='The unique sender screen name of this direct message.')

  def GetRecipientId(self):
    '''Get the unique recipient id of this direct message.

    Returns:
      The unique recipient id of this direct message
    '''
    return self._recipient_id

  def SetRecipientId(self, recipient_id):
    '''Set the unique recipient id of this direct message.

    Args:
      recipient id: The unique recipient id of this direct message
    '''
    self._recipient_id = recipient_id

  recipient_id = property(GetRecipientId, SetRecipientId,
                doc='The unique recipient id of this direct message.')

  def GetRecipientScreenName(self):
    '''Get the unique recipient screen name of this direct message.

    Returns:
      The unique recipient screen name of this direct message
    '''
    return self._recipient_screen_name

  def SetRecipientScreenName(self, recipient_screen_name):
    '''Set the unique recipient screen name of this direct message.

    Args:
      recipient_screen_name: The unique recipient screen name of this direct message
    '''
    self._recipient_screen_name = recipient_screen_name

  recipient_screen_name = property(GetRecipientScreenName, SetRecipientScreenName,
                doc='The unique recipient screen name of this direct message.')

  def GetText(self):
    '''Get the text of this direct message.

    Returns:
      The text of this direct message.
    '''
    return self._text

  def SetText(self, text):
    '''Set the text of this direct message.

    Args:
      text: The text of this direct message
    '''
    self._text = text

  text = property(GetText, SetText,
                  doc='The text of this direct message')

  def __ne__(self, other):
    return not self.__eq__(other)

  def __eq__(self, other):
    try:
      return other and \
          self.id == other.id and \
          self.created_at == other.created_at and \
          self.sender_id == other.sender_id and \
          self.sender_screen_name == other.sender_screen_name and \
          self.recipient_id == other.recipient_id and \
          self.recipient_screen_name == other.recipient_screen_name and \
          self.text == other.text
    except AttributeError:
      return False

  def __str__(self):
    '''A string representation of this twitter.DirectMessage instance.

    The return value is the same as the JSON string representation.

    Returns:
      A string representation of this twitter.DirectMessage instance.
    '''
    return self.AsJsonString()

  def AsJsonString(self):
    '''A JSON string representation of this twitter.DirectMessage instance.

    Returns:
      A JSON string representation of this twitter.DirectMessage instance
   '''
    return simplejson.dumps(self.AsDict(), sort_keys=True)

  def AsDict(self):
    '''A dict representation of this twitter.DirectMessage instance.

    The return value uses the same key names as the JSON representation.

    Return:
      A dict representing this twitter.DirectMessage instance
    '''
    data = {}
    if self.id:
      data['id'] = self.id
    if self.created_at:
      data['created_at'] = self.created_at
    if self.sender_id:
      data['sender_id'] = self.sender_id
    if self.sender_screen_name:
      data['sender_screen_name'] = self.sender_screen_name
    if self.recipient_id:
      data['recipient_id'] = self.recipient_id
    if self.recipient_screen_name:
      data['recipient_screen_name'] = self.recipient_screen_name
    if self.text:
      data['text'] = self.text
    return data

  @staticmethod
  def NewFromJsonDict(data):
    '''Create a new instance based on a JSON dict.

    Args:
      data: A JSON dict, as converted from the JSON in the twitter API
    Returns:
      A twitter.DirectMessage instance
    '''
    sender = None
    sender_json = data.get('sender', None)
    if sender_json:
        sender = User.NewFromJsonDict(sender_json)
    return DirectMessage(created_at=data.get('created_at', None),
                         recipient_id=data.get('recipient_id', None),
                         sender_id=data.get('sender_id', None),
                         sender = sender,
                         text=data.get('text', None),
                         sender_screen_name=data.get('sender_screen_name', None),
                         id=data.get('id', None),
                         recipient_screen_name=data.get('recipient_screen_name', None))

class Api(object):
  '''A python interface into the Twitter API '''

  _API_REALM = 'Twitter API'

  def __init__(self, verified=False, input_encoding=None, request_headers=None):
    '''Instantiate a new twitter.Api object.

    Args:
      username: The username of the twitter account.  [optional]
      password: The password for the twitter account. [optional]
      input_encoding: The encoding used to encode input strings. [optional]
      request_header: A dictionary of additional HTTP request headers. [optional]
    '''
    self._urllib = urllib2
    self._InitializeRequestHeaders(request_headers)
    self._InitializeUserAgent()
    self._InitializeDefaultParameters()
    self._input_encoding = input_encoding
    self.verified = verified

  def Verify(self):
    ''' Login verify

    Returns:
      True or False
    '''
    url = TWITTER_API + 'account/verify_credentials.json'
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def GetPublicTimeline(self, since_id=None):
    '''Fetch the sequnce of public twitter.Status message for all users.

    Args:
      since_id:
        Returns only public statuses with an ID greater than (that is,
        more recent than) the specified ID. [Optional]

    Returns:
      An sequence of twitter.Status instances, one for each message
    '''
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    url = TWITTER_API + 'statuses/public_timeline.json'
    json = self._FetchUrl(url,  parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetHomeTimeline(self,
                         count=None,
                         since_id=None,
                         max_id=None,
                         page=None):
    '''Fetch the sequence of twitter.Status messages for a user's friends

    Returns:
      A sequence of twitter.Status instances, one for each message
    '''
    if not self.verified:
      raise TwitterError("User must be specified if API is not authenticated.")
    else:
      url = TWITTER_API + 'statuses/home_timeline.json'
    parameters = {}
    if count is not None:
      try:
        if int(count) > 200:
          raise TwitterError("'count' may not be greater than 200")
      except ValueError:
        raise TwitterError("'count' must be an integer")
      parameters['count'] = count
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
      
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetListStatuses(self,
                         id,
                         user,
                         count=None,
                         since_id=None,
                         max_id=None,
                         page=None):
    '''Fetch the sequence of twitter.Status messages for a user's lists

    The twitter.Api instance must be authenticated if the user is private.

    Args:
      id:
        Specifies the list ID
      count: 
        Specifies the number of statuses to retrieve. May not be
        greater than 200. [Optional]
      since:
        Narrows the returned results to just those statuses created
        after the specified HTTP-formatted date. [Optional]
      since_id:
        Returns only public statuses with an ID greater than (that is,
        more recent than) the specified ID. [Optional]

    Returns:
      A sequence of twitter.Status instances, one for each message
    '''
    if not self.verified:
      raise TwitterError("User must be specified if API is not authenticated.")

    parameters = {}
    if count is not None:
      try:
        if int(count) > 200:
          raise TwitterError("'count' may not be greater than 200")
      except ValueError:
        raise TwitterError("'count' must be an integer")
      parameters['count'] = count
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
      
    url = TWITTER_API + '%s/lists/%s/statuses.json' % (user, id)
      
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetUserTimeline(self, user=None, max_id=None, count=None, since=None, since_id=None):
    '''Fetch the sequence of public twitter.Status messages for a single user.

    The twitter.Api instance must be authenticated if the user is private.
    
    mitnk add arg: max_id,

    Args:
      max_id:
        Returns only statuses with an ID less than (that is, older than) 
        or equal to the specified ID. 
      user:
        either the username (short_name) or id of the user to retrieve.  If
        not specified, then the current authenticated user is used. [optional]
      count: the number of status messages to retrieve [optional]
      since:
        Narrows the returned results to just those statuses created
        after the specified HTTP-formatted date. [optional]
      since_id:
        Returns only public statuses with an ID greater than (that is,
        more recent than) the specified ID. [Optional]

    Returns:
      A sequence of twitter.Status instances, one for each message up to count
    '''
    try:
      if count:
        int(count)
    except:
      raise TwitterError("Count must be an integer")
    parameters = {}
    if count:
      parameters['count'] = count
    if since:
      parameters['since'] = since
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if user:
      url = TWITTER_API + 'statuses/user_timeline/%s.json' % user
    elif not user and not self.verified:
      raise TwitterError("User must be specified if API is not authenticated.")
    else:
      url = TWITTER_API + 'statuses/user_timeline.json'
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetFavorites(self, user=None, page=None):
    '''Return a list of Status objects representing favorited tweets. By default, returns the 
       (up to) 20 most recent tweets for the authenticated user.
       
       Args:
          user: the username or id of the user whose favorites you are fetching.  If
          not specified, defaults to the authenticated user. [optional]
         
         page: Optional. Retrieves the 20 next most recent favorite statuses.
    '''
    parameters = {}
    if page:
      parameters['page'] = page
    if user:
      url = TWITTER_API + 'favorites/%s.json' % user
    elif not user and not self.verified:
      raise TwitterError("User must be specified if API is not authenticated.")
    else:
      url = TWITTER_API + 'favorites.json'

    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetStatusRetweetsBy(self, tweet_id):
    url = TWITTER_API + ('statuses/%s/retweeted_by.json' % tweet_id)
    parameters = {}
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [User.NewFromJsonDict(x) for x in data]


  def GetRetweetsOfMe(self, count=None, since_id=None, max_id=None, page=None):
    '''Returns the 20 most recent mentions (status containing @username) for the authenticating user.'''
    url = TWITTER_API + 'statuses/retweets_of_me.json'
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if count:
      parameters['count'] = count
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]


  def GetRetweets(self, since_id=None, max_id=None, page=None):
    '''Returns the 20 most recent mentions (status containing @username) for the authenticating user.'''
    url = TWITTER_API + 'statuses/retweeted_to_me.json'
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetMentions(self, since_id=None, max_id=None, page=None):
    '''Returns the 20 most recent mentions (status containing @username) for the authenticating user.'''
    url = TWITTER_API + 'statuses/mentions.json'
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetFriendIds(self, user_id=None, screen_name=None):
    '''Fetch an array of numeric IDs for every user the specified user is following. If called with no arguments,
       the results are friend IDs for the authenticated user.  Note that it is unlikely that there is ever a good reason
       to use both of the kwargs.
      
       Args:
         user_id: Optional.  Specfies the ID of the user for whom to return the friends list.
         screen_name:  Optional.  Specfies the screen name of the user for whom to return the friends list.
    
    '''
    url = TWITTER_API + 'friends/ids.json'
    parameters = {}
    if user_id:
      parameters['user_id'] = user_id
    if screen_name:
      parameters['screen_name'] = screen_name
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return data
 
 
  def GetFollowerIds(self, user_id=None, screen_name=None):
    '''Fetch an array of numeric IDs for every user the specified user is followed by. If called with no arguments,
       the results are follower IDs for the authenticated user.  Note that it is unlikely that there is ever a good reason
       to use both of the kwargs.
      
       Args:
         user_id: Optional.  Specfies the ID of the user for whom to return the followers list.
         screen_name:  Optional.  Specfies the screen name of the user for whom to return the followers list.
    
    '''
    url = TWITTER_API + 'followers/ids.json'
    parameters = {}
    if user_id:
      parameters['user_id'] = user_id
    if screen_name:
      parameters['screen_name'] = screen_name
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return data

  def GetStatus(self, id):
    '''Returns a single status message.

    The twitter.Api instance must be authenticated if the status message is private.

    Args:
      id: The numerical ID of the status you're trying to retrieve.

    Returns:
      A twitter.Status instance representing that status message
    '''
    try:
      if id:
        long(id)
    except:
      raise TwitterError("id must be an long integer")
    url = TWITTER_API + 'statuses/show/%s.json' % id
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def Retweet(self, id):
    '''Retweet a spacial tweet

    The twitter.Api instance must be authenticated and thee
    authenticating user must be the author of the specified status.

    Args:
      id: The numerical ID of the status you're trying to destroy.

    Returns:
      A twitter.Status instance representing the destroyed status message
    '''
    try:
      if id:
        long(id)
    except:
      raise TwitterError("id must be an integer")
    url = TWITTER_API + 'statuses/retweet/%s.json' % id
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def DestroyStatus(self, id):
    '''Destroys the status specified by the required ID parameter.

    The twitter.Api instance must be authenticated and thee
    authenticating user must be the author of the specified status.

    Args:
      id: The numerical ID of the status you're trying to destroy.

    Returns:
      A twitter.Status instance representing the destroyed status message
    '''
    try:
      if id:
        long(id)
    except:
      raise TwitterError("id must be an integer")
    url = TWITTER_API + 'statuses/destroy/%s.json' % id
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def PostUpdate(self, status, in_reply_to_status_id=None):
    '''Post a twitter status message from the authenticated user.

    The twitter.Api instance must be authenticated.

    Args:
      status:
        The message text to be posted.  Must be less than or equal to
        140 characters.
      in_reply_to_status_id:
        The ID of an existing status that the status to be posted is
        in reply to.  This implicitly sets the in_reply_to_user_id
        attribute of the resulting status to the user ID of the
        message being replied to.  Invalid/missing status IDs will be
        ignored. [Optional]
    Returns:
      A twitter.Status instance representing the message posted.
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")

    url = TWITTER_API + 'statuses/update.json'

    if len(status) > CHARACTER_LIMIT:
      raise TwitterError("Text must be less than or equal to %d characters. "
                         "Consider using PostUpdates." % CHARACTER_LIMIT)

    data = {'status': status}
    if in_reply_to_status_id:
      data['in_reply_to_status_id'] = in_reply_to_status_id

    json = self._FetchUrl(url, post_data=data)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def PostUpdates(self, status, continuation=None, in_reply_to_status_id=None, **kwargs):
    '''Post one or more twitter status messages from the authenticated user.

    Unlike api.PostUpdate, this method will post multiple status updates
    if the message is longer than 140 characters.

    The twitter.Api instance must be authenticated.

    Args:
      status:
        The message text to be posted.  May be longer than 140 characters.
      continuation:
        The character string, if any, to be appended to all but the
        last message.  Note that Twitter strips trailing '...' strings
        from messages.  Consider using the unicode \u2026 character
        (horizontal ellipsis) instead. [Defaults to None]
      **kwargs:
        See api.PostUpdate for a list of accepted parameters.
    Returns:
      A of list twitter.Status instance representing the messages posted.
    '''
    results = list()
    if continuation is None:
      continuation = ''
    line_length = CHARACTER_LIMIT - len(continuation)
    lines = textwrap.wrap(status, line_length)
    for line in lines[0:-1]:
      results.append(self.PostUpdate(line + continuation, 
                                     in_reply_to_status_id=in_reply_to_status_id, 
                                     **kwargs))
    results.append(self.PostUpdate(lines[-1], 
                                   in_reply_to_status_id=in_reply_to_status_id,
                                   **kwargs))
    return results

  def GetReplies(self, since=None, since_id=None, page=None): 
    '''Get a sequence of status messages representing the 20 most recent
    replies (status updates prefixed with @username) to the authenticating
    user.

    Args:
      page: 
      since:
        Narrows the returned results to just those statuses created
        after the specified HTTP-formatted date. [optional]
      since_id:
        Returns only public statuses with an ID greater than (that is,
        more recent than) the specified ID. [Optional]

    Returns:
      A sequence of twitter.Status instances, one for each reply to the user.
    '''
    url = TWITTER_API + 'statuses/replies.json'
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    parameters = {}
    if since:
      parameters['since'] = since
    if since_id:
      parameters['since_id'] = since_id
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [Status.NewFromJsonDict(x) for x in data]

  def GetFriends(self, user=None, page=None):
    '''Fetch the sequence of twitter.User instances, one for each friend.

    Args:
      user: the username or id of the user whose friends you are fetching.  If
      not specified, defaults to the authenticated user. [optional]

    The twitter.Api instance must be authenticated.

    Returns:
      A sequence of twitter.User instances, one for each friend
    '''
    if not self.verified:
      raise TwitterError("twitter.Api instance must be authenticated")
    if user:
      url = TWITTER_API + 'statuses/friends/%s.json' % user 
    else:
      url = TWITTER_API + 'statuses/friends.json'
    parameters = {}
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [User.NewFromJsonDict(x) for x in data]

  def GetFollowers(self, user=None, page=None):
    '''Fetch the sequence of twitter.User instances, one for each follower

    The twitter.Api instance must be authenticated.

    Returns:
      A sequence of twitter.User instances, one for each follower
    '''
    if not self.verified:
      raise TwitterError("twitter.Api instance must be authenticated")
    if user:
        url = TWITTER_API + 'statuses/followers/%s.json' % user
    else:
        url = TWITTER_API + 'statuses/followers.json'
    parameters = {}
    if page:
      parameters['page'] = page
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [User.NewFromJsonDict(x) for x in data]

  def GetFeatured(self):
    '''Fetch the sequence of twitter.User instances featured on twitter.com

    The twitter.Api instance must be authenticated.

    Returns:
      A sequence of twitter.User instances
    '''
    url = TWITTER_API + 'statuses/featured.json'
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [User.NewFromJsonDict(x) for x in data]

  def GetUser(self, user):
    '''Returns a single user.

    The twitter.Api instance must be authenticated.

    Args:
      user: The username or id of the user to retrieve.

    Returns:
      A twitter.User instance representing that user
    '''
    url = TWITTER_API + 'users/show.json?screen_name=' + user
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def GetDirectMessages(self, count=20, since_id=None, max_id=None, page=None):
    """
    Returns:
      A sequence of twitter.DirectMessage instances
    """
    url = TWITTER_API + 'direct_messages.json'
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    parameters = {}
    if count:
      parameters['count'] = count
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page 
    json = self._FetchUrl(url, parameters=parameters)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [DirectMessage.NewFromJsonDict(x) for x in data]

  def PostDirectMessage(self, user, text):
    '''Post a twitter direct message from the authenticated user

    The twitter.Api instance must be authenticated.

    Args:
      user: The ID or screen name of the recipient user.
      text: The message text to be posted.  Must be less than 140 characters.

    Returns:
      A twitter.DirectMessage instance representing the message posted
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    url = TWITTER_API + 'direct_messages/new.json'
    data = {'text': text, 'user': user}
    json = self._FetchUrl(url, post_data=data)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return DirectMessage.NewFromJsonDict(data)

  def DestroyDirectMessage(self, id):
    '''Destroys the direct message specified in the required ID parameter.

    The twitter.Api instance must be authenticated, and the
    authenticating user must be the recipient of the specified direct
    message.

    Args:
      id: The id of the direct message to be destroyed

    Returns:
      A twitter.DirectMessage instance representing the message destroyed
    '''
    url = TWITTER_API + 'direct_messages/destroy/%s.json' % id
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return DirectMessage.NewFromJsonDict(data)

  def GetRemainingHits(self):
    '''
    Returns the remaining number of API requests available to the requesting
    user before the API limit is reached for the current hour. Calls to
    this method do not count against the rate limit. If authentication
    credentials are provided, the rate limit status for the authenticating user
    is returned.  Otherwise, the rate limit status for the requester's IP
    address is returned.

    Returns:
        The remaing number of hits, as an integer.
    '''
    url = TWITTER_API + 'account/rate_limit_status.json'
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return data.get('remaining_hits', None)

  def SetUserProfile(self, user):
    '''This method is created by mitnk.
    Update user profile.
    
    The twitter.Api instance must be authenticated.

    Args:
      user: The user instance

    Returns:
      A twitter.DirectMessage instance representing the message destroyed
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    url = TWITTER_API + 'account/update_profile.json'
    data = user.AsDict()
    json = self._FetchUrl(url, post_data=data)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def SearchTwitter(self, query, lang=None, rpp=50, 
                      page=0, max_id=None, since_id=None, geocode=None, show_user=None):
    '''Search Twitter
        Returns:
          ResultSet object, contains the results and other meta data.
    '''
    parameters = {}
    if isinstance(query, unicode):
        parameters['q'] = query.encode('utf-8')
    else:
        parameters['q'] = query
    
    if lang:
      parameters['lang'] = lang
    if rpp is not None:
      try:
        if int(rpp) > 100:
          raise TwitterError("'rpp' may not be greater than 100")
      except ValueError:
        raise TwitterError("'rpp' must be an integer")
      parameters['rpp'] = rpp
    if max_id:
      parameters['max_id'] = max_id
    if since_id:
      parameters['since_id'] = since_id
      
    url = 'http://search.twitter.com/search.json?' + urllib.urlencode(parameters)
    json = self._FetchUrl(url)


    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [SearchResult.NewFromJsonDict(x) for x in data['results']]
    
  def FollowingUser(self, mine_name, user):
    '''Check if the user specified in the user parameter is a friend of the authenticating user.

    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user to befriend.
    Returns:
      True or False
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
  
    url = TWITTER_API + 'friendships/exists.json?user_a=%s&user_b=%s' %(mine_name, user)
    try:
      res = urllib2.urlopen(url)
      for r in res:
        if r == 'true':
          return True
        break
    except:
      pass
    return False

  def GetTrends(self, flag="current"):
    '''Get Saved Searches.

    The twitter.Api instance must be authenticated.

    Returns:
      True or False
    '''
    
    if flag == "current":
        url = TWITTER_API + 'trends.json'
    else:
        url = 'http://search.twitter.com/trends/weekly.json?date=%s' % time.strftime("%Y-%m-%d")
        
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    
    if flag == "current":
        return [SavedSearch.NewFromJsonDict(x) for x in data.get('trends')]
    else:
        return [SavedSearch.NewFromJsonDict(x) for x in data.get('trends')[time.strftime("%Y-%m-%d")]]

  def GetSavedSearches(self):
    '''Get Saved Searches.

    The twitter.Api instance must be authenticated.

    Returns:
      True or False
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
  
    url = TWITTER_API + 'saved_searches.json'
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [SavedSearch.NewFromJsonDict(x) for x in data]

  def GetLists(self, user):
    '''Get Saved Searches.

    The twitter.Api instance must be authenticated.

    Returns:
      True or False
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    
    url = TWITTER_API + '%s/lists.json' % user
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [List.NewFromJsonDict(x) for x in data['lists']]

  def GetSubscriptionLists(self, username):
    '''Get Saved Searches.

    The twitter.Api instance must be authenticated.

    Returns:
      True or False
    '''
    if not self.verified:
      raise TwitterError("The twitter.Api instance must be authenticated.")
    
    url = TWITTER_API + '%s/lists/subscriptions.json' % username
    json = self._FetchUrl(url)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return [List.NewFromJsonDict(x) for x in data['lists']]

  def ReportSpam(self, user_id=None, user_name=None, id=None):
    '''Block a user
    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user to block.
    Returns:
      A twitter.User instance representing the blocked user.
    '''
    url = TWITTER_API + 'report_spam.json'
    data = {}
    if user_name:
      data['user_name'] = user_name
    if user_id:
      data['user_id'] = user_id
    if id:
      data['id'] = id
    json = self._FetchUrl(url, post_data=data)
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def Block(self, user):
    '''Block a user
    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user to block.
    Returns:
      A twitter.User instance representing the blocked user.
    '''
    url = TWITTER_API + 'blocks/create/%s.json' % user
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def Unblock(self, user):
    '''Unblock a user
    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user to block.
    Returns:
      A twitter.User instance representing the unblocked user.
    '''
    url = TWITTER_API + 'blocks/destroy/%s.json' % user
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def IsBlocked(self, user_id=None, user_name=None, id=None):
    '''If the authenticating user is blocking a target user
    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user.
    Returns:
      A twitter.User instance representing the target user.
    '''
    if user_id:
      url = TWITTER_API + 'blocks/exists.json?user_id=' + str(user_id)
    elif user_name:
      url = TWITTER_API + 'blocks/exists.json?screen_name=' + user_name
    else:
      url = TWITTER_API + 'blocks/exists/%s.json' % str(id)
    try:
      json = self._FetchUrl(url)
      data = simplejson.loads(json)
      self._CheckForTwitterError(data)
    except:
      return False
    return User.NewFromJsonDict(data)

  def CreateFriendship(self, user):
    '''Befriends the user specified in the user parameter as the authenticating user.

    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user to befriend.
    Returns:
      A twitter.User instance representing the befriended user.
    '''
    url = TWITTER_API + 'friendships/create/%s.json' % user
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def DestroyFriendship(self, user):
    '''Discontinues friendship with the user specified in the user parameter.

    The twitter.Api instance must be authenticated.

    Args:
      The ID or screen name of the user  with whom to discontinue friendship.
    Returns:
      A twitter.User instance representing the discontinued friend.
    '''
    url = TWITTER_API + 'friendships/destroy/%s.json' % user
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return User.NewFromJsonDict(data)

  def CreateFavorite(self, status_id):
    '''Favorites the status specified in the status parameter as the authenticating user.
    Returns the favorite status when successful.

    The twitter.Api instance must be authenticated.

    Args:
      The twitter.Status instance to mark as a favorite.
    Returns:
      A twitter.Status instance representing the newly-marked favorite.
    '''
    url = TWITTER_API + 'favorites/create/%s.json' % status_id
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def DestroyFavorite(self, status_id):
    '''Un-favorites the status specified in the ID parameter as the authenticating user.
    Returns the un-favorited status in the requested format when successful.

    The twitter.Api instance must be authenticated.

    Args:
      The twitter.Status to unmark as a favorite.
    Returns:
      A twitter.Status instance representing the newly-unmarked favorite.
    '''
    url = TWITTER_API + 'favorites/destroy/%s.json' % status_id
    json = self._FetchUrl(url, post_data={})
    data = simplejson.loads(json)
    self._CheckForTwitterError(data)
    return Status.NewFromJsonDict(data)

  def SetUserAgent(self, user_agent):
    '''Override the default user agent

    Args:
      user_agent: a string that should be send to the server as the User-agent
    '''
    self._request_headers['User-Agent'] = user_agent

  def _BuildUrl(self, url, path_elements=None, extra_params=None):
    # Break url into consituent parts
    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)

    # Add any additional path elements to the path
    if path_elements:
      # Filter out the path elements that have a value of None
      p = [i for i in path_elements if i]
      if not path.endswith('/'):
        path += '/'
      path += '/'.join(p)

    # Add any additional query parameters to the query string
    if extra_params and len(extra_params) > 0:
      extra_query = self._EncodeParameters(extra_params)
      # Add it to the existing query
      if query:
        query += '&' + extra_query
      else:
        query = extra_query

    # Return the rebuilt URL
    return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))

  def _InitializeRequestHeaders(self, request_headers):
    if request_headers:
      self._request_headers = request_headers
    else:
      self._request_headers = {}

  def _InitializeUserAgent(self):
    user_agent = 'Python-urllib/%s (python-twitter/%s)' % \
                 (self._urllib.__version__, __version__)
    self.SetUserAgent(user_agent)

  def _InitializeDefaultParameters(self):
    self._default_params = {}

  def _AddAuthorizationHeader(self, username, password):
    if username and password:
      basic_auth = base64.encodestring('%s:%s' % (username, password))[:-1]
      self._request_headers['Authorization'] = 'Basic %s' % basic_auth

  def _RemoveAuthorizationHeader(self):
    if self._request_headers and 'Authorization' in self._request_headers:
      del self._request_headers['Authorization']

  def _GetOpener(self, url, username=None, password=None):
    if username and password:
      self._AddAuthorizationHeader(username, password)
      handler = self._urllib.HTTPBasicAuthHandler()
      (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
      handler.add_password(Api._API_REALM, netloc, username, password)
      opener = self._urllib.build_opener(handler)
    else:
      opener = self._urllib.build_opener()
    opener.addheaders = self._request_headers.items()
    return opener

  def _Encode(self, s):
    if self._input_encoding:
      return unicode(s, self._input_encoding).encode('utf-8')
    else:
      return unicode(s).encode('utf-8')

  def _EncodeParameters(self, parameters):
    '''Return a string in key=value&key=value form

    Values of None are not included in the output string.

    Args:
      parameters:
        A dict of (key, value) tuples, where value is encoded as
        specified by self._encoding
    Returns:
      A URL-encoded string in "key=value&key=value" form
    '''
    if parameters is None:
      return None
    else:
      return urllib.urlencode(dict([(k, self._Encode(v)) for k, v in parameters.items() if v is not None]))

  def _EncodePostData(self, post_data):
    '''Return a string in key=value&key=value form

    Values are assumed to be encoded in the format specified by self._encoding,
    and are subsequently URL encoded.

    Args:
      post_data:
        A dict of (key, value) tuples, where value is encoded as
        specified by self._encoding
    Returns:
      A URL-encoded string in "key=value&key=value" form
    '''
    if post_data is None:
      return None
    else:
      return urllib.urlencode(dict([(k, self._Encode(v)) for k, v in post_data.items()]))

  def _CheckForTwitterError(self, data):
    """Raises a TwitterError if twitter returns an error message.

    Args:
      data: A python dict created from the Twitter json response
    Raises:
      TwitterError wrapping the twitter error message if one exists.
    """
    # Twitter errors are relatively unlikely, so it is faster
    # to check first, rather than try and catch the exception
    if 'error' in data:
      raise TwitterError(data['error'])


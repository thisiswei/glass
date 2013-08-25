# Copyright (C) 2013 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Datastore models for Starter Project"""

__author__ = 'alainv@google.com (Alain Vongsouvanh)'


from google.appengine.ext import db

from oauth2client.appengine import CredentialsProperty


class Credentials(db.Model):
  """Datastore entity for storing OAuth2.0 credentials.

  The CredentialsProperty is provided by the Google API Python Client, and is
  used by the Storage classes to store OAuth 2.0 credentials in the data store.
  """
  credentials = CredentialsProperty()

class User(db.Model):
  userid = db.StringProperty()
  given_name = db.StringProperty()
  family_name = db.StringProperty()
  name = db.StringProperty(required=True)
  email = db.StringProperty(required=True)
  created_at = db.DateProperty()
  birthday = db.StringProperty()

class Location(db.Model):
  email = db.StringProperty()
  created_at = db.DateTimeProperty()
  longitude = db.FloatProperty()
  latitude = db.FloatProperty()

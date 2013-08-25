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

"""Request Handler for /main endpoint."""

__author__ = 'alainv@google.com (Alain Vongsouvanh)'


from datetime import datetime
import json
import io
import jinja2
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import httplib2
from apiclient import errors
from apiclient.http import MediaIoBaseUpload
from apiclient.http import BatchHttpRequest
from oauth2client.appengine import StorageByKeyName

from model import Credentials
import util


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class _BatchCallback(object):
  """Class used to track batch request responses."""

  def __init__(self):
    """Initialize a new _BatchCallbaclk object."""
    self.success = 0
    self.failure = 0

  def callback(self, request_id, response, exception):
    """Method called on each HTTP Response from a batch request.

    For more information, see
      https://developers.google.com/api-client-library/python/guide/batch
    """
    if exception is None:
      self.success += 1
    else:
      self.failure += 1
      logging.error(
          'Failed to insert item for user %s: %s', request_id, exception)


class MainHandler(webapp2.RequestHandler):
  """Request Handler for the main endpoint."""

  def _render_template(self, message=None):
    """Render the main page template."""
    template_values = {'userId': self.userid}
    if message:
      template_values['message'] = message
    # self.mirror_service is initialized in util.auth_required.
    try:
      template_values['contact'] = self.mirror_service.contacts().get(
        id='Python Quick Start').execute()
    except errors.HttpError:
      logging.info('Unable to find Python Quick Start contact.')

    timeline_items = self.mirror_service.timeline().list(maxResults=3).execute()
    template_values['timelineItems'] = timeline_items.get('items', [])

    subscriptions = self.mirror_service.subscriptions().list().execute()
    for subscription in subscriptions.get('items', []):
      collection = subscription.get('collection')
      if collection == 'timeline':
        template_values['timelineSubscriptionExists'] = True
      elif collection == 'locations':
        template_values['locationSubscriptionExists'] = True

    template = jinja_environment.get_template('templates/index_2.html')
    self.response.out.write(template.render(template_values))

  @util.auth_required
  def get(self):
    """Render the main page."""
    # Get the flash message and delete it.
    message = memcache.get(key=self.userid)
    memcache.delete(key=self.userid)
    self._render_template(message)

  @util.auth_required
  def post(self):
    """Execute the request and render the template."""
    operation = self.request.get('operation')
    # Dict of operations to easily map keys to methods.
    operations = {
        'insertSubscription': self._insert_subscription,
        'deleteSubscription': self._delete_subscription,
        'insertItem': self._insert_item,
        'insertItemWithAction': self._insert_item_with_action,
        'insertItemAllUsers': self._insert_item_all_users,
        'insertContact': self._insert_contact,
        'deleteContact': self._delete_contact,
        'deleteTimelineItem': self._delete_timeline_item
    }
    if operation in operations:
      message = operations[operation]()
    else:
      message = "I don't know how to " + operation
    # Store the flash message for 5 seconds.
    memcache.set(key=self.userid, value=message, time=5)
    self.redirect('/')

  def _get_products(self):
    """
    @return: list(dict)
    """
    items = []
    ll = self._get_last_location() or (-73.990452, 40.718167)
    url = "http://stylrapp.com/api/v1.8/product/?start_idx=0&distance=1609&ll=%s,%s" % (ll[0], ll[1])
    result = urlfetch.fetch(url, deadline=20)
    obj = json.loads(result.content)
    products = obj['data']['objects']
    for product in products:
      items.append({
          'url': product['product_images'][0]['url'],
          'price': product['price'],
          'store': product['store']['name'],
          'brand': product['brand']['name'],
          })
    return items

  def _insert_subscription(self):
    """Subscribe the app."""
    # self.userid is initialized in util.auth_required.
    body = {
        'collection': self.request.get('collection', 'timeline'),
        'userToken': self.userid,
        'callbackUrl': util.get_full_url(self, '/notify')
    }
    # self.mirror_service is initialized in util.auth_required.
    self.mirror_service.subscriptions().insert(body=body).execute()
    return 'Application is now subscribed to updates.'

  def _delete_subscription(self):
    """Unsubscribe from notifications."""
    collection = self.request.get('subscriptionId')
    self.mirror_service.subscriptions().delete(id=collection).execute()
    return 'Application has been unsubscribed.'

  def _get_last_location(self):
    """
    @return: LngLat
    """
    locations = self.mirror_service.locations().list().execute()
    for location in locations.get('items', []):
      longitude = location.get('longitude')
      latitude = location.get('latitude')
      return (longitude, latitude)
    return None

  def _insert_product(self, product, bundle_id):
    """
    Insert a timeline item.

    @param product: dict
    @param bundle_id: str
    """
    logging.info('Inserting timeline item')
    body = {
        'notification': {'level': 'DEFAULT'}
    }
    template = jinja_environment.get_template('templates/product.html')
    body['html'] = [
        template.render(product)
        ]

    body['creator'] = {
        'phoneNumber': '6503877186',
        }
    body['bundleId'] = bundle_id
    body['menuItems'] = [
        {'action': 'VOICE_CALL'},
        {'action': 'SHARE'},
        ]
    self.mirror_service.timeline().insert(
        body=body,
        media_body=self._upload_image(product['url'])
        ).execute()
    return  'A timeline item has been inserted.'

  def _get_items(self):
    """
    """

  def _insert_item(self):
    products = self._get_products()
    bundle_id = "stylr_%s" % str(datetime.now())
    for product in products[:3]:
      self._insert_product(product, bundle_id)

  def _insert_item_with_action(self):
    """Insert a timeline item user can reply to."""
    logging.info('Inserting timeline item')
    body = {
        'creator': {
            'displayName': 'Python Starter Project',
            'id': 'PYTHON_STARTER_PROJECT'
        },
        'text': 'Tell me what you had for lunch :)',
        'notification': {'level': 'DEFAULT'},
        'menuItems': [{'action': 'REPLY'}]
    }
    # self.mirror_service is initialized in util.auth_required.
    self.mirror_service.timeline().insert(body=body).execute()
    return 'A timeline item with action has been inserted.'

  def _insert_item_all_users(self):
    """Insert a timeline item to all authorized users."""
    logging.info('Inserting timeline item to all users')
    users = Credentials.all()
    total_users = users.count()

    if total_users > 10:
      return 'Total user count is %d. Aborting broadcast to save your quota' % (
          total_users)
    body = {
        'text': 'Hello Everyone!',
        'notification': {'level': 'DEFAULT'}
    }

    batch_responses = _BatchCallback()
    batch = BatchHttpRequest(callback=batch_responses.callback)
    for user in users:
      creds = StorageByKeyName(
          Credentials, user.key().name(), 'credentials').get()
      mirror_service = util.create_service('mirror', 'v1', creds)
      batch.add(
          mirror_service.timeline().insert(body=body),
          request_id=user.key().name())

    batch.execute(httplib2.Http())
    return 'Successfully sent cards to %d users (%d failed).' % (
        batch_responses.success, batch_responses.failure)

  def _insert_contact(self):
    """Insert a new Contact."""
    logging.info('Inserting contact')
    name = self.request.get('name')
    image_url = self.request.get('imageUrl')
    if not name or not image_url:
      return 'Must specify imageUrl and name to insert contact'
    else:
      if image_url.startswith('/'):
        image_url = util.get_full_url(self, image_url)
      body = {
          'id': name,
          'displayName': name,
          'imageUrls': [image_url]
      }
      # self.mirror_service is initialized in util.auth_required.
      self.mirror_service.contacts().insert(body=body).execute()
      return 'Inserted contact: ' + name

  def _delete_contact(self):
    """Delete a Contact."""
    # self.mirror_service is initialized in util.auth_required.
    self.mirror_service.contacts().delete(
        id=self.request.get('id')).execute()
    return 'Contact has been deleted.'

  def _delete_timeline_item(self):
    """Delete a Timeline Item."""
    logging.info('Deleting timeline item')
    # self.mirror_service is initialized in util.auth_required.
    self.mirror_service.timeline().delete(id=self.request.get('itemId')).execute()
    return 'A timeline item has been deleted.'

  def _upload_image(self, url):
    """
    @return: media_object
    """
    resp = urlfetch.fetch(url, deadline=20)
    media = MediaIoBaseUpload(
        io.BytesIO(resp.content), mimetype='image/jpeg', resumable=True)
    return media

	


MAIN_ROUTES = [
    ('/', MainHandler)
]

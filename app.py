from datetime import datetime
import io
import logging
import os

from apiclient.http import MediaIoBaseUpload
from google.appengine.api import urlfetch
import jinja2
import json

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class GlassApp(object):
    def __init__(self, mirror_service):
        self.mirror_service = mirror_service

    def _get_last_locations(self, num):
        """
        @return: list(LngLat)
        """
        locations = self.mirror_service.locations().list().execute()
        locations = locations.get('items', [])
        to_return = []
        for location in locations:
            longitude = location.get('longitude')
            latitude = location.get('latitude')
            to_return.append((longitude, latitude))
            if len(to_return) >= num:
                return to_return[:num]
        return to_return

    def _get_products(self):
        """
        @return: list(dict)
        """
        items = []
        locations = self._get_last_locations(1)
        ll = locations[0] if locations else (-73.990452, 40.718167)
        url = "http://stylrapp.com/api/vglass/product/?start_idx=0&distance=1609&ll=%s,%s" % (ll[0], ll[1])
        result = urlfetch.fetch(url, deadline=20)
        obj = json.loads(result.content)
        products = obj['data']['objects']
        neighborhood_name = obj['data']['neighborhood_name']
        for product in products:
            items.append({
                'url': product['product_images'][0]['url'],
                'price': product['price'],
                'store': product['store']['name'],
                'brand': product['brand']['name'],
                'phone': product['store_location']['phone'],
                'address': product['store_location']['address'],
                'longitude': product['store_location']['longitude'],
                'latitude': product['store_location']['latitude'],
                'neighborhood_name': neighborhood_name,
                })
        return items

    def insert_products(self):
        products = self._get_products()[:5]
        bundle_id = "stylr_%s" % str(datetime.now())
        context = products[0]
        context['num_products'] = len(products)
        self._insert_product_cover(bundle_id, context)
        for product in products:
            self._insert_product(bundle_id, product)

    def _insert_product_cover(self, bundle_id, context):
        logging.info('Inserting timeline item')
        template = jinja_environment.get_template('templates/cover.html')
        body = {
                'notification': {'level': 'DEFAULT'},
                'isBundleCover': True,
                'html': [
                    template.render(context),
                    ],
                'bundleId': bundle_id,
                }

        self.mirror_service.timeline().insert(
                body=body,
                media_body=self._upload_image(context['url'])
                ).execute()

    def _insert_product(self, bundle_id, product):
        """
        Insert a timeline item.

        @param bundle_id: str
        @param product: dict
        """
        logging.info('Inserting timeline item')
        template = jinja_environment.get_template('templates/product.html')

        creator = {
                'phoneNumber': product['phone'],
                'address': product['address'],
                'longitude': product['longitude'],
                'latitude': product['latitude'],
                }

        menu_items = [
                {'action': 'VOICE_CALL'},
                {'action': 'SHARE'},
                ]

        body = {
                'notification': {'level': 'DEFAULT'},
                'html': [
                    template.render(product)
                    ],
                'bundleId': bundle_id,
                'creator': creator,
                'menuItems': menu_items,
                }

        self.mirror_service.timeline().insert(
                body=body,
                media_body=self._upload_image(product['url'])
                ).execute()

    def _upload_image(self, url):
        """
        @return: media_object
        """
        resp = urlfetch.fetch(url, deadline=20)
        media = MediaIoBaseUpload(
            io.BytesIO(resp.content), mimetype='image/jpeg', resumable=True)
        return media

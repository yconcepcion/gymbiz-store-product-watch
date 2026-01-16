from datetime import datetime
import json

from products.core.utils.json_encoder import DecimalEncoder
from products.models import ProductStatusPipeline
from products.service.product_service import ProductService
from products.service.product_status_service import ProductStatusService


class UpdateProductAction:

    def __init__(self):
        self.price = None
        self.in_stock = True
        self.store_provider_url = None
        self.sku = None
        self.updated_by_user = None
        self.id = None
        self.new_status = None
        self.log = None
        self.product = None

    def set(self, updated_by_user, id, sku, store_provider_url, price, in_stock, new_status):
        self.id = id
        self.sku = sku
        self.store_provider_url = store_provider_url
        self.price = price
        self.in_stock = in_stock
        self.updated_by_user = updated_by_user
        self.new_status = new_status

    def execute(self):
        json_change = {
            "changes": []
        }
        with_changed = False
        product_service = ProductService()
        product = product_service.find(self.id)
        self.product = product
        current_product_status = product.get_current_pipeline().product_status

        if self.sku is not None and product.sku is not None and self.sku != product.sku:
            json_field_change = {
                "field": "sku",
                "from": product.sku,
                "to": self.sku
            }
            product.sku = self.sku
            json_change.get("changes").append(json_field_change)
            with_changed = True

        if self.store_provider_url is not None and product.store_provider_url is not None and self.store_provider_url != product.store_provider_url:
            json_field_change = {
                "field": "store_provider_url",
                "from": product.store_provider_url,
                "to": self.store_provider_url
            }
            product.store_provider_url = self.store_provider_url
            json_change.get("changes").append(json_field_change)
            with_changed = True

        if self.price is not None and self.price != product.price:
            json_field_change = {
                "field": "price",
                "from": product.price,
                "to": self.price
            }
            product.price = self.price
            json_change.get("changes").append(json_field_change)
            with_changed = True

        if self.in_stock is not None and self.in_stock != product.in_stock:
            json_field_change = {
                "field": "in_stock",
                "from": product.in_stock,
                "to": self.in_stock
            }
            product.in_stock = self.in_stock
            json_change.get("changes").append(json_field_change)
            with_changed = True

        product.save()

        if bool(self.new_status) and self.new_status != current_product_status.name:
            product_status_pipeline = ProductStatusPipeline()
            product_status_pipeline.posted = datetime.now()
            product_status_pipeline.product = product
            product_status_service = ProductStatusService()
            status = product_status_service.find_by_name(self.new_status)
            product_status_pipeline.product_status = status
            product_status_pipeline.user = self.updated_by_user

            json_field_change = {
                "field": "status",
                "from": current_product_status.name,
                "to": status.name
            }
            json_change.get("changes").append(json_field_change)

            if self.log is not None and len(self.log) > 0:
                json_change.update({
                    "message": self.log
                })
            product_status_pipeline.log = json.dumps(json_change, cls=DecimalEncoder, indent=2)
            product_status_pipeline.save()
        elif with_changed:
            product_status_pipeline = ProductStatusPipeline()
            product_status_pipeline.posted = datetime.now()
            product_status_pipeline.product = product
            product_status_pipeline.product_status = current_product_status
            product_status_pipeline.user = self.updated_by_user

            if self.log is not None and len(self.log) > 0:
                json_change.update({
                    "message": self.log
                })
            product_status_pipeline.log = json.dumps(json_change, cls=DecimalEncoder, indent=2)
            product_status_pipeline.save()

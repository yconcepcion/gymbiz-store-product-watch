from django.contrib.auth import get_user_model

from products.models import Product, ProductStatusPipeline, ProductStatus
from datetime import datetime

from products.service.product_status_service import ProductStatusService

User = get_user_model()


class CreateProductAction:

    def __init__(self):
        self.price = None
        self.store_provider_url = None
        self.sku = None
        self.created_by_user = None
        self.product = None
        self.in_stock = True

    def set(self, created_by_user, sku, store_provider_url, price, in_stock):
        self.sku = sku
        self.store_provider_url = store_provider_url
        self.price = price
        self.in_stock = in_stock
        self.created_by_user = created_by_user

    def execute(self):
        self.product = Product(sku=self.sku, store_provider_url=self.store_provider_url, price=self.price, in_stock=self.in_stock)
        self.product.save()

        product_status_pipeline = ProductStatusPipeline()
        product_status_pipeline.posted = datetime.now()
        product_status_pipeline.product = self.product
        product_status_service = ProductStatusService()
        created_status = product_status_service.find_by_name(ProductStatus.CREATED)
        product_status_pipeline.product_status = created_status
        product_status_pipeline.user = self.created_by_user
        product_status_pipeline.save()



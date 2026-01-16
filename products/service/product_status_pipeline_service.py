from products.models import ProductStatusPipeline
from products.repository.product_status_pipeline_repository import ProductStatusPipelineRepository


class ProductStatusPipelineService:

    def __init__(self):
        self.repository = ProductStatusPipelineRepository()

    def save(self, pipeline: ProductStatusPipeline):
        return self.repository.save(pipeline)

    def find(self, product):
        return self.repository.find_all_by_product_id(product.id)

    def find_all_by_product_id(self, product_id):
        return self.repository.find_all_by_product_id(product_id)

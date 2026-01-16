from products.models import ProductStatusPipeline


class ProductStatusPipelineRepository:

    def find_by_id(self, id):
        return ProductStatusPipeline.objects.filter(pk=id).first()

    def save(self, product_status_pipeline: ProductStatusPipeline):
        product_status_pipeline.save()

    def find_all_by_product_id(self, product_id):
        return ProductStatusPipeline.objects.filter(product_id=product_id).order_by("-posted")

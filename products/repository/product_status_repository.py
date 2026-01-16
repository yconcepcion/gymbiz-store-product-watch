from products.models import ProductStatus


class ProductStatusRepository:

    def find(self, id):
        return ProductStatus.objects.filter(pk=id).first()

    def find_by_name(self, name):
        return ProductStatus.objects.filter(name=name).first()

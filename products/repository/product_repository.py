from products.models import Product


class ProductRepository:

    def find_by_id(self, id) -> Product:
        return Product.objects.filter(pk=id).first()

    def save(self, product: Product):
        product.save()

    def find_by_sku(self, sku):
        return Product.objects.filter(sku=sku).first()

    def find_all(self):
        return Product.objects.all()

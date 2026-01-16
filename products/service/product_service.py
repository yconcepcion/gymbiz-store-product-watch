from products.repository.product_repository import ProductRepository


class ProductService:

    def __init__(self):
        self.repository = ProductRepository()

    def find(self, product_id):
        return self.repository.find_by_id(product_id)

    def save(self, product):
        self.repository.save(product)

    def find_by_sku(self, sku):
        return self.repository.find_by_sku(sku)

    def find_all(self):
        return self.repository.find_all()
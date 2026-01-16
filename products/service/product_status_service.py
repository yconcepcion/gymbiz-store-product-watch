from products.repository.product_status_repository import ProductStatusRepository


class ProductStatusService:
    def __init__(self):
        self.repository = ProductStatusRepository()

    def find(self, id):
        return self.repository.find(id)

    def find_by_name(self, name):
        return self.repository.find_by_name(name)

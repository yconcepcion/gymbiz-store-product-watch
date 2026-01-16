class PageInfo:

    def __init__(self):
        self.elements_per_page = 0
        self.current_page = 0
        self.total_elements = 0

    def get_page_count(self):
        return self.total_elements // self.elements_per_page if self.total_elements % self.elements_per_page == 0 else self.total_elements // self.elements_per_page + 1

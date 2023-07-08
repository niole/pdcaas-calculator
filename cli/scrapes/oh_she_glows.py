from scrapy_base import ScrapyBase


"""
go to each top level page, then drill down into each recipe and scrape the contents out of each recipe page
"""
class QuotesSpider(ScrapyBase):
    name = "vegan_recipes"

    max_recipes = 2000

    recipe_count = 0

    searched_page_count = 0

    start_urls = [
        "https://ohsheglows.com/categories/recipes-2/",
    ]

    default_description = "crowd-pleasing and family-approved plant-based recipes, healthy recipes free of any animal products. "

    def parse(self, response):
        self.print_final_stats()
        self.searched_page_count += 1
        # get recipes on this page
        for card in response.css('a.entry-title-link::attr("href")'):
            next_page = card.get()
            if next_page is not None:
                yield response.follow(next_page, self.parse_recipe)

        if self.recipe_count < self.max_recipes:
            # get next page
            next_page = response.css('li.pagination-next a::attr("href")').get()
            if next_page is not None:
                yield response.follow(next_page, self._parse)
        else:
            self.print_final_stats()

    def parse_title(self, response):
        return self.clean(response.css('h1.entry-title::text').get())

    def parse_yields(self, response):
        return self.clean(response.css('div.recipe_numbers span.yield::text').get())

    def parse_ingredients(self, response):
        return self.clean_array(response.css('li.ingredient::text').getall())

    def parse_instructions(self, response):
        return self.clean_array_to_str(response.css('div.instructions *::text').getall(), " ")

    def parse_description(self, response):
        return self.clean_array_to_str([self.default_description] + response.css('div.summary p::text').getall(), ' ')

    def parse_tags(self, response):
        return ["vegan"] + self.clean_array(response.css('span.entry-categories a::text').getall())

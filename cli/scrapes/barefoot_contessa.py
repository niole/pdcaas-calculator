import scrapy
from anyascii import anyascii
import logging
import re
from scrapy_base import ScrapyBase


class QuotesSpider(ScrapyBase):
    name = "barefoot_contessa_recipes"

    max_recipes = 500

    recipe_count = 0

    searched_page_count = 0

    start_urls = [
        "https://barefootcontessa.com/recipes/starters",
        "https://barefootcontessa.com/recipes/lunch",
        "https://barefootcontessa.com/recipes/dinner",
        "https://barefootcontessa.com/recipes/sides",
        "https://barefootcontessa.com/recipes/dessert",
        "https://barefootcontessa.com/recipes/breakfast"
    ]

    def parse(self, response):
        self.searched_page_count += 1
        # get recipes on this page
        for card in response.css('div.recipes figure div a::attr("href")'):
            next_page = card.get()
            if next_page is not None:
                yield response.follow(next_page, self.parse_recipe)

        if self.recipe_count < self.max_recipes:
            # get next page

            more_button = response.css('p.MixedResults__load-more a::attr("href")').get()
            next_button = response.css('div.menu-centered.container.text-center.mix.all.w-full.border-t.border-cream.pt-5.mb-9 ul li:nth-child(2) a::attr("href")').get()

            if more_button is not None:
                yield response.follow(more_button, self._parse)
            elif next_button is not None:
                yield response.follow(next_button, self._parse)
        else:
            self.print_final_stats()

    def parse_title(self, response):
        return self.clean(response.css('section.EntryPostTop div.container h1::text').get())

    def parse_yields(self, response):
        return self.clean(response.css('div.text-center.mt-3.h23 span:nth-child(1)::text').get())

    def parse_ingredients(self, response):
        return self.clean_array(response.css('ul.h29 li::text').getall())

    def parse_instructions(self, response):
        return self.clean_array_to_str(response.css('div.bd4.mb-10.EntryPost__text.a-bc-blue p::text').getall(), ' ')

    def parse_description(self, response):
        return "classic american comfort food. There’s nothing like a home-cooked meal to make everyone feel happy and loved."

    def parse_tags(self, response):
        return self.clean_array(response.css('div.EntryPost__tags p.h21 a::text').getall())

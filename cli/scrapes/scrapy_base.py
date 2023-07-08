import scrapy
from anyascii import anyascii
import logging
import re


class ScrapyBase(scrapy.Spider):
    max_recipes = 1

    recipe_count = 0

    searched_page_count = 0

    def parse(self, response):
        pass
    def parse_title(self, response):
        pass
    def parse_yields(self, response):
        pass
    def parse_ingredients(self, response):
        pass
    def parse_instructions(self, response):
        pass
    def parse_description(self, response):
        pass
    def parse_tags(self, response):
        pass

    def parse_recipe(self, response):
        if self.recipe_count < self.max_recipes:
            title = self.parse_title(response)
            yields = self.parse_yields(response)
            ingredients = self.parse_ingredients(response)
            instructions = self.parse_instructions(response)

            req_fields = [title, yields, ingredients, instructions]
            if None in req_fields or '' in req_fields or [] in req_fields:
                return

            yield {
                "title": title,
                "yields": yields,
                "ingredients": ingredients,
                "instructions": instructions,
                "description": self.parse_description(response),
                "tags": self.parse_tags(response),
            }

            self.recipe_count += 1
            
        else:
            self.print_final_stats()

    def print_final_stats(self):
        logging.info(f"Found recipe count {self.recipe_count}, max recipe count {self.max_recipes}. searched page count {self.searched_page_count}")

    def clean(self, s):
        return self.remove_new_lines(self.remove_unicode(s))

    def remove_new_lines(self, s):
        if s is not None:
            try:
                return re.sub(r'\n+', r'', s)
            except e as Error:
                logging.error(f"Failed to new lines: {e}")
        return s

    def remove_unicode(self, s):
        if s is not None:
            try:
                return anyascii(s)
            except e as Error:
                logging.error(f"Failed to remove ascii: {e}")
        return s

    def clean_array_to_str(self, arr, join_char):
        return join_char.join([self.clean(r) for r in arr if r is not None])


    def clean_array(self, arr):
        return [self.clean(r.strip()) for r in arr if r is not None]

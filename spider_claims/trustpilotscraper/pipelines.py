# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class TrustpilotscraperPipeline:
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)

        field_names = adapter.field_names()
        for field_name in field_names:
            value = adapter.get(field_name)
            if value:
                adapter[field_name] = value
            else:
                adapter[field_name] = 'NIL'

        ## Checking for verifiction and replacing with YES or NO
        check_verification = adapter.get('verified')
        if check_verification:
            if 'VERIFIED' in check_verification:
                adapter['verified'] = 'YES'
            else:
                adapter['verified'] = 'NO'
        else:
            adapter['verified'] = 'NO'

        ## Cleaning the categories of a company
        categories_list = adapter.get('company_category')
        # get all category except the last one
        cat_without_last = categories_list[:-1]
        # combining all category
        combined_cat = ','.join(cat_without_last)
        adapter['company_category'] = combined_cat

        ## Company Ratings --> convert string to float
        comp_rating_string = adapter.get('company_trustpilot_rating')
        adapter['company_trustpilot_rating'] = float(comp_rating_string)

        ## Reviews --> convert string to number
        num_reviews_string = adapter.get('number_of_reviews')
        num_reviews_string_without_comma = num_reviews_string.replace(',','')
        adapter['number_of_reviews'] = int(num_reviews_string_without_comma)


        
        return item

# use the parent import with amount with our preprocess row

from add_claims_with_amt import iterate_rows
import re

def preprocess_row(row):

   # 'subject', 'amt', and 'statement' are the configuration file settings we pull from
   m = re.search(r'^([^\?]+)', row['Source URL'])
   row['subject'] = m.group(1)
   row['amt'] = int(row['Amount Raised'].replace("$", "").replace(",", ""))
   row['statement'] = row['Title'] + ' : ' + row['Statement']

   # we actually changed row in place so the return value and setting to the return value is not really needed
   # but since we set it in the library we will do it anyway
   return row

iterate_rows('./gofundme/config.json', preprocess_row)

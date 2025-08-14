
from viet_badwords_filter.filter import VNBadwordsFilter

filter = VNBadwordsFilter()

print(filter.is_profane("hello")) 
print(filter.is_profane("vcl")) 
print(filter.clean("lồn"))  

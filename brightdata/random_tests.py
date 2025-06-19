# to run python -m brightdata.random_tests

from brightdata.auto import scrape_url

l= "https://tr.linkedin.com/in/enes-kuzucu"
r=scrape_url(l)

print(r)
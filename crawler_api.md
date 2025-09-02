sc
Crawler API
Extract and map URLs, HTMLs, and Markdown files from any domain. Transform any website into LLM-compatible data
Public web data



Crawler API
Extract and map URLs, HTMLs, and Markdown files from any domain. Transform any website into LLM-compatible data
Public web data
Results:
2 scrapers

Most popular
sc
Crawl API - collect by URL
Collect data from any domain as HTML or Markdown files by URL
all websites
271
sc
Crawl API - discover by domain url
Map all links from a given domain, collecting internal and external URLs for seamless analysis, auditing, or integration into your workflows.
all websites
271



Example.com
Crawl API - collect by URL


Result
This is an example of how API results will look like.
To see all data points, please refer to the dictionary. Missing data point? Click 
here
 to request new ones.


 [
  {
    "markdown": null,
    "url": "https://www.massgeneral.org/disaster-medicine/education-and-training/fellowship-in-disaster-medicine",
    "html2text": null,
    "page_html": "<!DOCTYPE html><html class=\"no-js\" lang=\"en\">\r\n<head>\r\n<META http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\r\n<title>Fellowship in Disaster Medicine & Health Care Emergency Management</title>\r\n<meta content=\"IE=edge\" http-equiv=\"X-UA-Compatible\">\r\n<meta content=\"on\" http-equiv=\"cleartype\">\r\n<!--grid-layout-->\r\n<!--ls:begin[stylesheet]-->\r\n<style type=\"text/",

    ....
    "ld_json": null,
    "page_title": null
  }
]

Column name
Description
Data type
Fill rate
markdown
Extracts content in Markdown format, preserving basic formatting like headings, lists, and links while removing complex HTML structures.
Html2markdown
26.22%
url
Url
100.00%
html2text
Extracts only the raw text from the page, stripping out all HTML tags and formatting.
Html2text
8.86%
page_html
Extracts the complete HTML source of the page, including all tags, scripts, and styles.
Html2html
76.16%
ld_json
Extracts structured metadata in JSON-LD format, often used for SEO and rich snippets (e.g., schema.org data).
Html2ldjson
2.86%



API request builder

Trigger Data Collection API
Use this API to start a data collection with specified parameters. It will return the "snapshot_id" for reference.


import requests

url = "https://api.brightdata.com/datasets/v3/trigger"
headers = {
	"Authorization": "Bearer e47fd9fc67f1bde198132d4404c902b9cb75223c50babdbc22e41698d4c06468",
	"Content-Type": "application/json",
}
params = {
	"dataset_id": "gd_m6gjtfmeh43we6cqc",
	"include_errors": "true",
}
data = [
	{"url":"https://example.com"},
	{"url":"https://example.com/1"},
]

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())



this was just  crawler api collect by url endpoint 


now i am showing you 

Discover by domain url endpoint 


This is an example of how API results will look like.
To see all data points, please refer to the dictionary. Missing data point? Click 
here
 to request new ones.


 [
  {
    "markdown": null,
    "url": "https://www.massgeneral.org/disaster-medicine/education-and-training/fellowship-in-disaster-medicine",
    "html2text": null,
    "page_html": "<!DOCTYPE html><html class=\"no-js\" lang=\"en\">\r\n<head>\r\n<META http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\r\n<title>Fellowship in Disaster Medicine & Health Care Emergency Management</title>\r\n<meta content=\"IE=edge\" http-equiv=\"X-UA-Compatible\">\r\n<meta content=\"on\" http-equiv=\"cleartype\">\r\n<!--grid-layout-->\r\n<!--ls:begin[stylesheet]-->\r\n<style type=\"text/css\">\r\n          \r\n          .iw_container\r\n          {\r\n            max-width:800px !important;\r\n            margin-left: auto;\r\n            margin-right: auto;\r\n          }\r\n          .

    ....



    "ld_json": null,
    "page_title": null
  }
]



Column name
Description
Data type
Fill rate
markdown
Extracts content in Markdown format, preserving basic formatting like headings, lists, and links while removing complex HTML structures.
Html2markdown
26.22%
url
Url
100.00%
html2text
Extracts only the raw text from the page, stripping out all HTML tags and formatting.
Html2text
8.86%
page_html
Extracts the complete HTML source of the page, including all tags, scripts, and styles.
Html2html
76.16%
ld_json
Extracts structured metadata in JSON-LD format, often used for SEO and rich snippets (e.g., schema.org data).
Html2ldjson
2.86%






Trigger Data Collection API
Use this API to start a data collection with specified parameters. It will return the "snapshot_id" for reference.


import requests

url = "https://api.brightdata.com/datasets/v3/trigger"
headers = {
	"Authorization": "Bearer e47fd9fc67f1bde198132d4404c902b9cb75223c50babdbc22e41698d4c06468",
	"Content-Type": "application/json",
}
params = {
	"dataset_id": "gd_m6gjtfmeh43we6cqc",
	"include_errors": "true",
	"type": "discover_new",
	"discover_by": "domain_url",
}
data = [
	{"url":"https://example.com/","filter":"","exclude_filter":""},
]

response = requests.post(url, headers=headers, params=params, json=data)
print(response.json())

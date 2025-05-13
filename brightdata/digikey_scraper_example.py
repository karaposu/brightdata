from .base_specialized_scraper import BrightdataBaseSpecializedScraper
import time

import logging
logger = logging.getLogger(__name__)


logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

class DigikeyByUrlScraper(BrightdataBaseSpecializedScraper):
    """
    Example subclass for scraping from Digi-Key by URL using Bright Data.
    In many cases, the base class logic is sufficient. We just override 
    or add extra checks if needed.
    """

    def __init__(self, dataset_id, bearer_token=None,  test_link=None, **kwargs):
      
        super().__init__(dataset_id, bearer_token, test_link, **kwargs)
    
    def test_connection(self):
        # If we need special checks for Digi-Key, do them here.
        # Otherwise, just call the base method:
        return super().test_connection()

    # def trigger(self, target: str) -> str:
    #     # Optionally ensure it's a valid Digi-Key URL:
    #     if "digikey" not in target.lower():
    #         raise ValueError("Target does not appear to be a valid Digi-Key URL.")
    #     return super().trigger(target)
    
    def trigger(self, target: str) -> str:
        # Optionally ensure it's a valid Digi-Key URL:
        
        if self.is_link(target):
            if "digikey" not in target.lower():
                raise ValueError("Target does not appear to be a valid Digi-Key URL.")
            return super().trigger(target)

        elif isinstance(target)== str:
            generated_link= self.make_link(target)
            return super().trigger(generated_link)
    
    def make_link(self, keyword ):
        digikey_base_url= ""
        return digikey_base_url+keyword

    def get_data(self, snapshot_id: str):
        # Optionally, parse or transform the final result specifically for Digi-Key
        result = super().get_data(snapshot_id)
        # If the result is 'not_ready' or an error string, just return it:
        if isinstance(result, str):
            return result

        # If it's a dict, we can do additional parsing if necessary
        if isinstance(result, dict) and "raw_html" in result:
            return self._parse_digikey_data(result["raw_html"])
        
        return result

    def _parse_digikey_data(self, raw_html):
        """
        Hypothetical method to parse details from raw HTML.
        For demonstration, we’ll return a simple dict. 
        """
        return {
            "part_number": "BAV99",
            "description": "Parsed from raw HTML",
            "html_preview": raw_html[:100]
        }





if __name__ == "__main__":
    

    from indented_logger import setup_logging
    from indented_logger import smart_indent_log

    setup_logging(level=logging.DEBUG,
            # log_file=log_file_path, 
            include_func=True, 
            include_module=False, 
            # no_datetime=True, 
            min_func_name_col=100 )

    dataset_id = "gd_lj74waf72416ro0k65"
    bearer_token = "ed81ba0163c55c2f60ea69545a14bb81301068a71ecd3049a69de9c3ecdd91b2"
    
    # all we need to provide is dataset_id and bearer_token.
  
    # Create scraper
    scraper = DigikeyByUrlScraper(dataset_id=dataset_id, bearer_token=bearer_token)
    
    a_digikey_link= "https://www.digikey.com/en/products/detail/stmicroelectronics/STM32F407VGT6/2747117"
    # snapshot_id = scraper.trigger(a_digikey_link)
    # logger.debug(f"snapshot_id: {snapshot_id}")

    # # # time.sleep(90)
    snapshot_id="s_m6iew8d912t7zq0i44"
    result = scraper.get_data(snapshot_id)
    print(result)

    
    smart_indent_log(logger,result, 0 )
    
    
    # Poll for the data in a simple loop (you might do something else in real code)
    # for _ in range(5):
    #     result = scraper.get_data(snapshot_id)
    #     if result == "not_ready":
    #         print("Job still in progress, waiting 15 seconds...")
    #         time.sleep(30)
    #     else:
    #         print("Job result or error:", result)
    #         break

import os
import requests
from dotenv import load_dotenv

class BrightdataWebUnlocker:
    def __init__(self):
        load_dotenv()  # Load the environment variables from .env
        self.bearer = os.getenv('BRIGHTDATA_WEBUNCLOKCER_BEARER')

        self.zone = os.getenv('BRIGHTDATA_WEBUNCLOKCER_APP_ZONE_STRING')
        self.format = "raw"

    def get_source_safe(self, target_weblink):
        """
        Retrieves the source for the given URL, returning the raw HTML/text if successful.
        If an error occurs, returns False instead of raising an exception.
        """
        try:
            return self.get_source(target_weblink)  # Uses the original method
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred while fetching {target_weblink}: {http_err}")
            return False
        except Exception as err:
            print(f"An unexpected error occurred while fetching {target_weblink}: {err}")
            return False

    def get_source(self, target_weblink):
        """
        Sends a request to Brightdata's Web Unlocker service for the given target URL
        and returns the raw HTML/text response.
        """
        url = "https://api.brightdata.com/request"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer}"
        }
        data = {
            "zone": self.zone,
            "url": target_weblink,
            "format": self.format
        }

        response = requests.post(url, headers=headers, json=data)
        # Raise an HTTPError if the response was unsuccessful
        response.raise_for_status()

        return response.text
        
    def test_unlocker(self):
        """
        Tests the BrightdataWebUnlocker by attempting to retrieve the source of 'https://example.com'.
        Returns:
            bool: True if the source is successfully retrieved and non-empty, False otherwise.
        """
        test_url = "https://example.com"
        try:
            source = self.get_source(test_url)
            if source and source.strip():
                print("Test Unlocker: Successfully retrieved source from 'https://example.com'.")
                return True
            else:
                print("Test Unlocker: Retrieved empty content from 'https://example.com'.")
                return False
        except requests.HTTPError as http_err:
            print(f"Test Unlocker: HTTP error occurred: {http_err}")  # HTTP error
            return False
        except Exception as err:
            print(f"Test Unlocker: An error occurred: {err}")  # Other errors
            return False



def main():
    # Instantiate the BrightdataWebUnlocker
    unlocker = BrightdataWebUnlocker()
    
    # Define a test URL
    test_url = "https://example.com"
    
    try:
        # Get the source HTML/text of the test URL
        source = unlocker.get_source(test_url)
        print("Successfully retrieved source:")
        print(source)
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP error
    except Exception as err:
        print(f"An error occurred: {err}")  # Other errors

if __name__ == "__main__":
    main()



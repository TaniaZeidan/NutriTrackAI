import os
from dotenv import load_dotenv

def test_get_google_api_key():
    load_dotenv()
    key = os.getenv("GOOGLE_API_KEY")
    testVal = os.getenv("TEST_ENV")
    assert testVal == 'abc'
    assert key == ''
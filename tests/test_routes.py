"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
import unittest
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)   

    def test_account_not_found(self):
        """It should return 404_NOT_FOUND when account does not exist"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_an_account(self):
        """It should Read an Account after creating it"""
        # Create a new account
        account_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "address": "123 Elm Street",
            "phone_number": "555-1234",
            "date_joined": "2023-01-01"
        }
        create_response = self.client.post(BASE_URL, json=account_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        # Get the account id from the response
        created_account = create_response.get_json()
        account_id = created_account["id"]

        # Read the account using the generated id
        read_response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)

        # Verify the returned data matches the original data
        read_account = read_response.get_json()
        self.assertEqual(read_account["name"], account_data["name"])
        self.assertEqual(read_account["email"], account_data["email"])
        self.assertEqual(read_account["address"], account_data["address"])
        self.assertEqual(read_account["phone_number"], account_data["phone_number"])
        self.assertEqual(read_account["date_joined"], account_data["date_joined"])

    def test_get_account_list(self):
        """It should Get a list of Accounts"""
        self._create_accounts(5)
        # send a self.client.get() request to the BASE_URL
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the data from resp.get_json()
        data = response.get_json()
        # assert that the len() of the data is 5 (the number of accounts you created)
        self.assertEqual(len(data), 5)

    def test_update_account(self):
        """It should Update an existing Account"""
        # create an Account to update
        test_account = AccountFactory()
        response = self.client.post(BASE_URL, json=test_account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get the data from resp.get_json() as new_account
        new_account = response.get_json()

        # update the account
        new_account["name"] = "Updated Name"
        response = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # get the data from resp.get_json() as updated_account
        updated_account = response.get_json()

        # assert that the updated_account["name"] is whatever you changed it to
        self.assertEqual(updated_account["name"], "Updated Name")

    def test_delete_account(self):
        """It should Delete an Account"""
        account = self._create_accounts(1)[0]
        # send a self.client.delete() request to the BASE_URL with an id of an account
        response = self.client.delete(f"{BASE_URL}/{account.id}")
        # assert that the resp.status_code is status.HTTP_204_NO_CONTENT
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


    def test_method_not_allowed(self):
            """It should not allow an illegal method call"""
            # call self.client.delete() on the BASE_URL
            response = self.client.delete(BASE_URL)
            # assert that the resp.status_code is status.HTTP_405_METHOD_NOT_ALLOWED
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_https_headers(self):
        """It should return the correct HTTPS headers"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the presence of headers and their values
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Content-Security-Policy'), "default-src 'self'; object-src 'none'")
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_access_control_allow_origin_header(self):
        """It should return the Access-Control-Allow-Origin header"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the presence of the Access-Control-Allow-Origin header
        self.assertEqual(response.headers.get('Access-Control-Allow-Origin'), '*')



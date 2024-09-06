import json
import time
import requests
from faker import Faker
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, TypeDecorator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


db = SQLAlchemy()

# Sets request retries and redirects to handle connection issues.
session = requests.Session()
retry = Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.max_redirects = 10000


# Enables book to handle serialized data.
class ListType(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)


class Book_info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Isbn_number = db.Column(db.Integer)
    title = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.Integer)
    summary = db.Column(db.String(200))
    price = db.Column(db.Integer)
    author = db.Column(ListType)
    category = db.Column(ListType)
    picture_url = db.Column(db.String)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    user_name = db.Column(db.String, nullable=False)
    password = db.Column(db.String(100))


class Cart(db.Model):
    user_id = db.Column(db.ForeignKey("user.id"), primary_key=True)
    book_item = db.Column(db.ForeignKey("book_info.id"))
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", backref=db.backref("carts"))
    book_info = db.relationship("Book_info", backref=db.backref("carts"))


# Creates a new data base containing users
def seed_data():
    faker = Faker()

    while User.query.count() < 50:
        # creates new variables
        n_username = faker.user_name()
        n_password = faker.password(
            length=6, digits=True, upper_case=True, lower_case=True
        )
        new_user = User(user_name=n_username, password=n_password)

        # Adds a new user
        db.session.add(new_user)
        db.session.commit()

    # Creates book data.
    while Book_info.query.count() < 50:
        try:
            book_response = session.get("https://openlibrary.org/random", timeout=5)
            book_key = book_response.url[30:].split("/")[0]
            openlib_response = session.get(
                f"https://openlibrary.org/search.json?q={book_key}", timeout=5
            )
            openlib_picture = f"https://covers.openlibrary.org/b/olid/{book_key}-M.jpg"

            # Checks if the openlib API's work.
            if (
                openlib_response.status_code == 200
                and session.get(openlib_picture, timeout=5).status_code == 200
            ):
                openlib_json = openlib_response.json()

                # Gets data from openlib.
                if "docs" in openlib_json and len(openlib_json["docs"]) > 0:
                    openlib_data = openlib_json["docs"][0]
                    authors = openlib_data.get("author_name", ["Unknown Authors"])
                    title = openlib_data.get("title", "Unknown Title")
                    wiki_response = session.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", timeout=5
                    )

                    # Checks if wiki API works.
                    if wiki_response.status_code == 200:
                        wiki_json = wiki_response.json()
                        summary = wiki_json.get("extract", "Summary Not Available")
                    
                        # Checks if the summary has data and creates variables.
                        Isbn_number = faker.random_int(min=10**12, max=10**13 - 1)
                        condition = faker.random_int(max=100)
                        price = faker.random_int(min=100, max=700)
                        category = []

                        # Adds the correct subjects to category.
                        for subject in openlib_json["docs"][0]["seed"]:
                            if subject.split("/")[1] == "subjects":
                                category.append(subject.split("/")[2])

                        # Creates a new book.
                        new_book = Book_info(
                            Isbn_number=Isbn_number,
                            title=title,
                            condition=condition,
                            summary=summary,
                            price=price,
                            author=authors,
                            category=category,
                            picture_url=openlib_picture,
                        )

                        # Adds and commits a new book to database.
                        db.session.add(new_book)
                        db.session.commit()
            else:
                print(f"OpenLibrary picture not available for {book_key}")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching book data: {e}")
            time.sleep(1)
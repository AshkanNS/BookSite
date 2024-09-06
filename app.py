from flask import Flask, render_template, request, redirect, url_for, session
from models import seed_data, db, Book_info
import os
from flask_migrate import Migrate, upgrade


"""Python file responsible for API functions and background processes"""

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.secret_key = 'supersecretkey'

db.init_app(app)

migrate = Migrate(app, db)

@app.route("/")
def home_page():
    sorting_column = request.args.get('sort_column', 'title')
    sorting_order = request.args.get('sort_order', 'asc')
    page = request.args.get('page', 1, type=int)
    search_word = request.args.get('q', '')

    search_books = Book_info.query.filter(
        Book_info.title.like("%" + search_word + "%")
    )

    match sorting_column:
        case 'title':
            sort_by = Book_info.title
        case 'price':
            sort_by = Book_info.price
        case 'author':
            sort_by = Book_info.author
        # Add more sorting options as needed
        case _:
            sort_by = Book_info.title  # Default sorting column

    sort_by = sort_by.asc() if sorting_order == 'asc' else sort_by.desc()

    all_books = search_books.order_by(sort_by)

    pa_obj = all_books.paginate(page=page, per_page=20, error_out=False)

    return render_template("index.html",
                           all_books=pa_obj.items,
                           pagination=pa_obj,
                           sort_column=sorting_column,
                           sort_order=sorting_order,
                           q=search_word,
                           page=page,
                           pages=pa_obj.pages,
                           has_next=pa_obj.has_next,
                           has_prev=pa_obj.has_prev)

@app.route("/sell_book")
def sell_page():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("index.html")

@app.route("/book_detail/<int:book_id>")
def book_detail(book_id):
    book = Book_info.query.get(book_id)
    if not book:
        return redirect(url_for('home_page'))
    return render_template("book_detail.html", book=book)

@app.route("/cart")
def cart_page():
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        session['cart'] = {}
        cart = session.get('cart', {})
    
    cart_books = []
    total_price = 0
    for book_id_str, quantity in cart.items():
        try:
            book_id = int(book_id_str)
        except ValueError:
            continue
        
        book = Book_info.query.get(book_id)
        if book:
            book_info = {
                'id': book.id,
                'title': book.title,
                'description': book.summary,
                'author': book.author,
                'price': book.price,
                'quantity': quantity,
                'total': quantity * book.price,
                'image_url': book.picture_url
            }
            total_price += book_info['total']
            cart_books.append(book_info)
    return render_template("cart.html", cart=cart_books, total_price=total_price)

@app.route("/add_to_cart/<int:book_id>")
def add_to_cart(book_id):
    cart = session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    
    book_id_str = str(book_id)
    if book_id_str in cart:
        cart[book_id_str] += 1
    else:
        cart[book_id_str] = 1
    
    session['cart'] = cart
    return redirect(url_for('cart_page'))

@app.route("/remove_from_cart/<int:book_id>")
def remove_from_cart(book_id):
    cart = session.get('cart', {})
    book_id_str = str(book_id)
    
    if book_id_str in cart:
        cart.pop(book_id_str)
    
    session['cart'] = cart
    return redirect(url_for('cart_page'))

@app.route("/increase_quantity/<int:book_id>")
def increase_quantity(book_id):
    cart = session.get('cart', {})
    book_id_str = str(book_id)
    if book_id_str in cart:
        cart[book_id_str] += 1
    session['cart'] = cart
    return redirect(url_for('cart_page'))

@app.route("/decrease_quantity/<int:book_id>")
def decrease_quantity(book_id):
    cart = session.get('cart', {})
    book_id_str = str(book_id)
    if book_id_str in cart:
        if cart[book_id_str] > 1:
            cart[book_id_str] -= 1
        else:
            cart.pop(book_id_str)
    session['cart'] = cart
    return redirect(url_for('cart_page'))

def calculate_total_price(cart):
    return sum(item['total'] for item in cart)

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    cart_books = []
    for book_id_str, quantity in cart.items():
        try:
            book_id = int(book_id_str)
        except ValueError:
            continue
        
        book = Book_info.query.get(book_id)
        if book:
            book_info = {
                'id': book.id,
                'title': book.title,
                'description': book.summary,
                'author': book.author,
                'price': book.price,
                'quantity': quantity,
                'total': quantity * book.price,
                'image_url': book.picture_url
            }
            cart_books.append(book_info)
    total_price = calculate_total_price(cart_books)
    return render_template('order_overview.html', cart=cart_books, total_price=total_price)

@app.route('/place_order', methods=['POST'])
def place_order():
    delivery_option = request.form.get('delivery')
    payment_option = request.form.get('payment')
    if payment_option != 'swish':
        return redirect(url_for('checkout'))

    cart = session.get('cart', {})
    cart_books = []
    for book_id_str, quantity in cart.items():
        try:
            book_id = int(book_id_str)
        except ValueError:
            continue
        
        book = Book_info.query.get(book_id)
        if book:
            book_info = {
                'id': book.id,
                'title': book.title,
                'description': book.summary,
                'author': book.author,
                'price': book.price,
                'quantity': quantity,
                'total': quantity * book.price,
                'image_url': book.picture_url
            }
            cart_books.append(book_info)
    total_price = calculate_total_price(cart_books)
    final_total = total_price

    session.pop('cart', None)

    return render_template('confirmation.html', final_total=final_total, delivery_option=delivery_option, payment_option=payment_option)

@app.route('/confirmation')
def confirmation():
    return

#More API's to be added
"""
@app.route("/register_user")
def register_user():
    
    #Placeholder for data base and code.
    return render_template(register.html)
    
@app.route("/user_page/<int: user_id>")
def user_page(user_id):
    
    #Placeholder for database and code.
    return render_template(user_page.html)

@app.route("/search_book/<str: category>")
def search_book(category):
    
    #Placeholder for database and code.
    return render_template(search_book.html, category = category)     

"""

# Start arguments for Flask
if __name__ == "__main__":
    with app.app_context():
        # Initialize the database
        db.create_all()
        os.system("flask db init")

        # Perform database upgrade (if needed)
        upgrade()
        seed_data()
    app.run(debug=True, port=5500)
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
from typing import List
import datetime 

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:Gi0vanna@localhost/e_commerce_project"
app.json.sort_keys = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)

class Customer(Base):
    __tablename__ = "Customers"
    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(320))
    phone: Mapped[str] = mapped_column(db.String(15))

    orders: Mapped[List["Order"]] = db.relationship(back_populates="customer")
    

order_product = db.Table(
    "Order_Product",
    Base.metadata,
    db.Column("order_id", db.ForeignKey("Orders.order_id"), primary_key=True)
    db.Colomn("product_id", db.ForeignKey("Products.product_id"), primary_key=True)
)



class Order(Base):
    __tablename__ = "Orders"
    order_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(db.Date, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("Customers.customer_id"))

    customer : Mapped["Customer"] = db.relationship(back_populates="orders")
    products: Mapped[List["Product"]]= db.relationship(secondary=order_product)



class Product(Base):
    __tablename__ = "Products"
    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255),nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)    


with app.app_context():
    db.create_all()



class CustomerSchema(ma.Schema):
    customer_id = fields.Integer(required=False)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("customer_id", "name", "email", "phone")



class CustomersSchema(ma.Schema):
    customer_id = fields.Integer(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:
        fields = ("customer_id", "name", "email", "phone")




class ProductSchema(ma.Schema):
    product_id = fields.Integer(required=False)
    name = fields.String(required=True)
    price = fields.Float(required=True)

    class Meta:
        fields = ("product_id", "name", "price")


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

class OrderSchema(ma.Schema):
    order_id = fields.Integer(required=False)
    date = fields.Date(required=True)
    customer_id = fields.Integer(required=True)

    class Meta:
        fields = ("order_id", "date", "customer_id")
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

       






@app.route("/")
def home():
    return "Welcome to our candle ecommerce store !"

@app.route("/customers", methods = ["GET"])
def get_customers():
    query = select(Customer)
    result = db.session.execute(query).scalars()
    customers = result.all()

    return customers_schema.jsonify(customers)


@app.route("/customers", methods=["POST"])
def add_customer():
    try:
        customer_data = customer_schema.load(request.json)

    except ValidationError as err:
        return jsonify(err.messages), 400

    with Session(db.engine) as session:
        new_customer = Customer(name=customer_data["name"], email = customer_data["email"], phone=customer_data["phone"])
        session.add(new_customer)
        session.commit()

    return jsonify({"message": "New customer added succesfully"}), 201        



@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Customer).filter(Customer.customer_id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"error": "Customer Not Found"}), 404
            customer = result

            try:
                customer_data = customer_schema.load(request.json)

            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in customer_data.items():
                setattr(customer, field, value)

            session.commit()    

    return jsonify({"message": "Customer details uploaded successfully"}), 200



@app.route("/customers/<int:id>", methods = ["DELETE"])
def delete_customer(id):
    delete_statement = delete(Customer).where(Customer.customer_id==id)

    with db.session.begin():
        result = db.session.execute(delete_statement)

        if result.rowcount == 0:
            return jsonify({"error": "Customer Not Found"}), 404
        

        return jsonify({"message": "Customer removed successfully"}), 200
        

#----------------------------------------

@app.route('/products', methods=["POST"])
def add_product():
    try: 
        product_data = product_schema.load(request.json)

    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            new_product = Product(name=product_data['name'], price=product_data['price'] )
            session.add(new_product)
            session.commit()

    return jsonify({"message": "Product added successfully"}), 201


@app.route("/products", methods=["GET"])
def get_products():
    query = select(Product)
    result = db.session.execute(query).scalars()
    products = result.all()

    return products_schema.jsonify(products)

@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Product).filter(Product.product_id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"error": "Product not found"}), 404
            product = result

            try:
                product_data = product_schema.load(request.json)
            except ValidationError as err:
                return jsonify(err.messages), 400
            
            for field, value in product_data.items():
                setattr(product, field, value )
            
            session.commit()
            return jsonify({"message": "Product successfully updated!"}), 200

@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    delete_statement = delete(Product).where(Product.product_id==id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Product Not found"}), 404
        
        return jsonify({"message": "Product removed successfully"}), 200
    
#-------
@app.route('/orders', methods=["POST"])
def create_order():
    try: 
        order_data = order_schema.load(request.json)

    except ValidationError as err:
        return jsonify(err.messages), 400
    
    with Session(db.engine) as session:
        with session.begin():
            new_order = Order(name=order_data['name'], price=order_data['price'] )
            session.add(new_order)
            session.commit()

    return jsonify({"message": "Order added successfully"}), 201




@app.route("/orders/by-name/<string:thing>", methods = ["GET"])
def retrieve_order_by_name(thing):
    search = f"%{thing}%"
    query = select(Order).where(Order.name.like(search)).order_by(Order.price.asc())
    orders = db.session.execute(query).scalars().all()

    return orders_schema.jsonify(orders)


@app.route("/products/<int:id>", methods=["DELETE"])
def cancel_order(id):
    delete_statement = delete(Order).where(Order.order_id==id)
    with db.session.begin():
        result = db.session.execute(delete_statement)
        if result.rowcount == 0:
            return jsonify({"error": "Order Not found"}), 404
        
        return jsonify({"message": "Order Cancelled"}), 200








if __name__ == "__main__":
    app.run(debug=True)




from fastapi import FastAPI, Query, Response, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel

class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

class CategoryBase(BaseModel):
    name: str

class CategoryId(CategoryBase):
    id: int


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float
    description: str | None = None
    category_id: int | None = Field(default=None, foreign_key="category.id")

class ProductBase(BaseModel):
    name: str
    price: float
    description: str | None = None
    category_id: int | None = None

class ProductId(BaseModel):
    id: int
    name: str | None = None
    price: float | None = None
    description: str | None = None
    category_id: int | None = None


engine = create_engine("sqlite:///database.db", echo=True)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app=FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/categories/", status_code=201)
def create_category(category: CategoryBase):
    with Session(engine) as session:
        db_category = Category(name=category.name)
        session.add(db_category)
        session.commit()
        session.refresh(db_category)
        return CategoryId(id=db_category.id, name=db_category.name)


@app.get("/categories/")
def read_categories():
    with Session(engine) as session:
        categories = session.exec(select(Category)).all()
        return categories


@app.get("/categories/{category_id}")
def read_category(category_id: int):
    with Session(engine) as session:
        category = session.exec(select(Category).where(Category.id == category_id)).one()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        return CategoryId(id = category.id, name = category.name)


@app.put("/categories/", response_model=CategoryId)
def update_category(category_update: CategoryId):
    with Session(engine) as session:
        category = session.exec(select(Category).where(Category.id == category_update.id)).one()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")

        category.name = category_update.name
        session.add(category)
        session.commit()
        session.refresh(category)
        return CategoryId(id = category.id, name = category.name)


@app.delete("/categories/{category_id}")
def delete_category(category_id: int):
    with Session(engine) as session:
        category = session.exec(select(Category).where(Category.id == category_id)).one()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        session.delete(category)
        session.commit()
        return {"detail": "Категория успешно удалена"}



@app.post("/products/", status_code=201)
def create_product(product: ProductBase):
    with Session(engine) as session:
        db_product = Product(name=product.name, price=product.price, description=product.description, category_id=product.category_id)
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return ProductId(id=db_product.id, name=db_product.name, price=db_product.price, description=db_product.description, category_id=db_product.category_id)


@app.get("/products/")
def read_products():
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        return products


@app.get("/products/{product_id}")
def read_category(product_id: int):
    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.id == product_id)).one()
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")
        return ProductId(id=product.id, name=product.name, price=product.price, description=product.description, category_id=product.category_id)


@app.put("/products/", response_model=ProductId)
def update_product(product_update: ProductId):
    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.id == product_update.id)).one()
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")

        product.name = product_update.name or product.name
        product.price = product_update.price or product.price
        product.description = product_update.description or product.description
        product.category_id = product_update.category_id or product.category_id
        session.add(product)
        session.commit()
        session.refresh(product)
        return ProductId(id=product.id, name=product.name, price=product.price, description=product.description, category_id=product.category_id)


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.id == product_id)).one()
        if not product:
            raise HTTPException(status_code=404, detail="Продукт не найден")
        session.delete(product)
        session.commit()
        return {"detail": "Продукт успешно удален"}
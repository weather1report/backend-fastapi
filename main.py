from fastapi import FastAPI, Path, Query, Response
from math import sqrt
import random


app=FastAPI()

@app.get("/about")
def about():
    return {
        "ФИО": "Ермаков Егор Андреевич",
        "группа": "Т-333901-ИСТ",
        "курс": 3,
        "название вуза": "НТИ (филиал) УРФУ",
        "Github": "https://github.com/weather1report"
    }

@app.get("/rnd")
def randReturn(min:int = 1, max:int = 100):
    return random.randint(min, max)


@app.post("/t_square", status_code=200)
def triangle(response: Response, a:float = Query(gt=0), b:float = Query(gt=0), c:float = Query(gt=0)):
    if (b+c <= a or c+a <= b or a+b <= c):
        response.status_code = 400
        return {"message": "Incorrect Data"}
    p = (a + b + c) / 2
    square = sqrt(p*(p-a)*(p-b)*(p-c))
    return {
        "perimeter": p*2,
        "square": square
    }

@app.get("/convert/{from_unit}/{to_unit}/{value}")
def convert(
    from_unit:str = Path(..., pattern=r"^(celsius|fahrenheit)$"),
    to_unit:str = Path(..., pattern=r"^(celsius|fahrenheit)$"),
    value: float = Path(...)
    ):
    res = value
    if from_unit == "celsius" and to_unit == "fahrenheit":
        res = value * 1.8 + 32
    if from_unit == "fahrenheit" and to_unit == "celsius":
        res = (value - 32) / 1.8

    return {
        "result": f"{res}{("°F" if to_unit == "fahrenheit" else "°C")}",
        "input": f"{value}{("°F" if from_unit == "fahrenheit" else "°C")}"
    }
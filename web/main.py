from datetime import datetime, timedelta
import logging

from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from charts import viewers_common
from chartjs import chart_load_js
from chartjs import chart_datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
mongo = AsyncIOMotorClient('mongo', 27017)


def render(request: Request, template: str, data: dict):
    data['request'] = request
    data['chart_load_js'] = chart_load_js
    data['chart_datetime'] = chart_datetime
    return templates.TemplateResponse(template, data)


@app.get("/info")
def home(request: Request):
    return render(request, "info.html", {})


@app.get("/")
@app.get("/week")
async def viewers_week(request: Request):
    week_ago = (datetime.now() - timedelta(days=7)).timestamp()
    data = await viewers_common(mongo, week_ago, 'week')
    return render(request, "chart.html", data)


@app.get("/month")
async def viewers_month(request: Request):
    month_ago = (datetime.now() - timedelta(days=30)).timestamp()
    data = await viewers_common(mongo, month_ago, 'month')
    return render(request, "chart.html", data)


@app.get("/year")
async def viewers_year(request: Request):
    year_ago = (datetime.now() - timedelta(days=365)).timestamp()
    data = await viewers_common(mongo, year_ago, 'year')
    return render(request, "chart.html", data)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    try:
        uvicorn.run(app, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        logging.info("^C pressed, exiting...")

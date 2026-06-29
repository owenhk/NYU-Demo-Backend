from fastapi import FastAPI
from fastapi import Request, HTTPException
import asyncpg
import os
import pydantic
import uuid
import datetime
app = FastAPI()

class AVEquipmentInventory(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    powered_on: bool

class StaffShiftSchedules(pydantic.BaseModel):
    id: uuid.UUID
    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/getdata")
async def say_hello(request: Request):
    headers = request.headers
    username = headers.get("username")
    password = headers.get("password")
    try:
        con = await asyncpg.connect(
            host=os.environ.get("PGHOST"),
            user=username,
            password=password,
            database="railway"
        )
        equipment = await con.fetch("SELECT * FROM AV_EQUIPMENT_INVENTORY")
        equipment = [AVEquipmentInventory.model_validate(dict(r)) for r in equipment]
        shift_schedules = await con.fetch("SELECT * FROM STAFF_SHIFT_SCHEDULES")
        shift_schedules = [StaffShiftSchedules.model_validate(dict(r)) for r in shift_schedules]
        await con.close()
        return {"equipment": equipment, "shift_schedules": shift_schedules}

    except Exception as e:
        return HTTPException(status_code=403, detail="Forbidden")


@app.post("/toggle_power")
async def toggle_power(request: Request):
    headers = request.headers
    username = headers.get("username")
    password = headers.get("password")
    body = await request.json()
    item_id = body["id"]
    try:
        con = await asyncpg.connect(
            host=os.environ.get("PGHOST"),
            user=username,
            password=password,
            database="railway"
        )
        await con.execute("UPDATE AV_EQUIPMENT_INVENTORY SET powered_on = NOT powered_on WHERE id = $1", item_id)
        await con.close()
        return {"command": "toggle_power", "device": item_id}
    except Exception as e:
        return HTTPException(status_code=403, detail="Forbidden")

@app.get("/getrole")
async def get_role(request: Request):
    headers = request.headers
    username = headers.get("username")
    password = headers.get("password")
    try:
        con = await asyncpg.connect(
            host=os.environ.get("PGHOST"),
            user=username,
            password=password,
            database="railway"
        )
        # Check what permisison the user has
        rows = await con.fetch(
            """
            SELECT r.rolname
            FROM pg_roles r
                     JOIN pg_auth_members m ON m.roleid = r.oid
                     JOIN pg_roles u ON u.oid = m.member
            WHERE u.rolname = $1
            """,
            username
        )
        roles = [row["rolname"] for row in rows]
        await con.close()
        return {"roles": roles}
    except Exception as e:
        return HTTPException(status_code=403, detail="Forbidden")
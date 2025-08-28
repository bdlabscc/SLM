# main.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/list_sgs", response_class=HTMLResponse)
async def list_sgs(request: Request, profiles: str = Form(...)):
    profile_list = [p.strip() for p in profiles.replace(",", " ").split() if p.strip()]
    sg_data = {}

    for profile in profile_list:
        try:
            session = boto3.Session(profile_name=profile)
            ec2 = session.client("ec2")
            response = ec2.describe_security_groups()
            sg_data[profile] = response.get("SecurityGroups", [])
        except Exception as e:
            sg_data[profile] = [{"GroupId": "Error", "GroupName": str(e)}]

    return templates.TemplateResponse(
        "list_sgs.html", {"request": request, "sg_data": sg_data}
    )


@app.get("/sg_details/{profile}/{sg_id}", response_class=HTMLResponse)
async def sg_details(request: Request, profile: str, sg_id: str):
    try:
        session = boto3.Session(profile_name=profile)
        ec2 = session.client("ec2")
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        sg = response["SecurityGroups"][0]
    except Exception as e:
        sg = {"GroupId": sg_id, "Error": str(e)}

    return templates.TemplateResponse(
        "sg_details.html", {"request": request, "profile": profile, "sg": sg}
    )

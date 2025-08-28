from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import aioboto3
import asyncio
from botocore.config import Config
from typing import List, Dict, Any, Optional

app = FastAPI(title="AWS SG Viewer")
templates = Jinja2Templates(directory="templates")

# Concurrency and timeouts
MAX_CONCURRENCY = 10
PER_PROFILE_TIMEOUT = 15
AWS_CONNECT_TIMEOUT = 5
AWS_READ_TIMEOUT = 10
sem = asyncio.Semaphore(MAX_CONCURRENCY)

aws_config = Config(
    connect_timeout=AWS_CONNECT_TIMEOUT,
    read_timeout=AWS_READ_TIMEOUT,
    retries={"max_attempts": 5, "mode": "standard"},
)


def parse_profiles(text: str) -> List[str]:
    raw = (text or "").replace(",", " ")
    profs = [p.strip() for p in raw.split() if p.strip()]
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for p in profs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


async def read_uploaded_profiles(file: Optional[UploadFile]) -> List[str]:
    if not file:
        return []
    content = await file.read()
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    return parse_profiles(text)


async def fetch_sgs_for_profile(profile: str, region: Optional[str]) -> Dict[str, Any]:
    try:
        async with sem:
            session = aioboto3.Session(profile_name=profile, region_name=region or None)
            async with session.client("ec2", config=aws_config) as ec2:
                paginator = ec2.get_paginator("describe_security_groups")
                groups: List[Dict[str, Any]] = []
                async for page in paginator.paginate():
                    groups.extend(page.get("SecurityGroups", []))
                return {"ok": True, "profile": profile, "groups": groups}
    except Exception as e:
        return {"ok": False, "profile": profile, "error": str(e)}


async def fetch_sg_details(profile: str, sg_id: str, region: Optional[str]) -> Dict[str, Any]:
    try:
        async with sem:
            session = aioboto3.Session(profile_name=profile, region_name=region or None)
            async with session.client("ec2", config=aws_config) as ec2:
                resp = await ec2.describe_security_groups(GroupIds=[sg_id])
                sgs = resp.get("SecurityGroups", [])
                if not sgs:
                    return {"ok": False, "error": f"SecurityGroup {sg_id} not found"}
                return {"ok": True, "sg": sgs[0]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/list_sgs", response_class=HTMLResponse)
async def list_sgs(
    request: Request,
    profiles: str = Form(""),
    region: str = Form(""),
    profiles_file: UploadFile | None = File(None),
):
    typed_profiles = parse_profiles(profiles)
    uploaded_profiles = await read_uploaded_profiles(profiles_file)
    all_profiles = typed_profiles + uploaded_profiles
    # Deduplicate
    seen = set()
    profiles_list: List[str] = []
    for p in all_profiles:
        if p not in seen:
            seen.add(p)
            profiles_list.append(p)

    if not profiles_list:
        return templates.TemplateResponse("home.html", {"request": request, "error": "No profiles provided"})

    tasks = [
        asyncio.wait_for(fetch_sgs_for_profile(p, region or None), timeout=PER_PROFILE_TIMEOUT)
        for p in profiles_list
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    for g in gathered:
        if isinstance(g, Exception):
            results.append({"ok": False, "profile": "unknown", "error": str(g)})
        else:
            results.append(g)

    return templates.TemplateResponse(
        "list_sgs.html",
        {"request": request, "results": results, "region": region}
    )


@app.get("/sg_details", response_class=HTMLResponse)
async def sg_details(profile: str, sg_id: str, region: str = ""):
    try:
        result = await asyncio.wait_for(
            fetch_sg_details(profile, sg_id, region or None),
            timeout=PER_PROFILE_TIMEOUT,
        )
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    return templates.TemplateResponse("sg_details.html", {"request": {}, "result": result})


@app.get("/healthz")
async def healthz():
    return "ok"

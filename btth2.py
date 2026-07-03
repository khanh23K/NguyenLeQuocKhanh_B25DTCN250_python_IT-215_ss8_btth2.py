from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal

app = FastAPI(title="IT Asset Management API")

assets = [
    {
        "id": 1,
        "serial_number": "SN-MAC-01",
        "model": "MacBook Pro M3",
        "stock_available": 5,
        "status": "READY"
    },
    {
        "id": 2,
        "serial_number": "SN-DELL-02",
        "model": "Dell UltraSharp 27",
        "stock_available": 10,
        "status": "READY"
    },
    {
        "id": 3,
        "serial_number": "SN-THINK-03",
        "model": "ThinkPad X1 Carbon",
        "stock_available": 0,
        "status": "REPAIRING"
    }
]

allocations = [
    {
        "id": 1,
        "asset_id": 1,
        "employee_email": "dev.nguyen@company.com",
        "allocated_quantity": 1,
        "start_date": "2026-07-01",
        "duration_months": 12
    }
]

class AssetCreate(BaseModel):
    serial_number: str
    model: str = Field(min_length=2, max_length=255)
    stock_available: int = Field(ge=0)
    status: Literal["READY", "ALLOCATED", "REPAIRING", "SCRAPPED"]


class AllocationCreate(BaseModel):
    asset_id: int
    employee_email: EmailStr
    allocated_quantity: int = Field(gt=0)
    start_date: str
    duration_months: int = Field(gt=0)

def find_asset(asset_id: int):
    for asset in assets:
        if asset["id"] == asset_id:
            return asset
    return None

@app.post("/assets", status_code=status.HTTP_201_CREATED)
def create_asset(asset: AssetCreate):

    for item in assets:
        if item["serial_number"].lower() == asset.serial_number.lower():
            raise HTTPException(
                status_code=400,
                detail="Serial number already exists"
            )

    new_asset = {
        "id": len(assets) + 1,
        **asset.model_dump()
    }

    assets.append(new_asset)

    return {
        "message": "Asset created successfully",
        "data": new_asset
    }


@app.get("/assets")
def get_assets(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    min_stock: Optional[int] = Query(None, ge=0)
):

    result = assets

    if keyword:
        keyword = keyword.lower()
        result = [
            asset for asset in result
            if keyword in asset["serial_number"].lower()
            or keyword in asset["model"].lower()
        ]

    if status:
        result = [
            asset for asset in result
            if asset["status"] == status
        ]

    if min_stock is not None:
        result = [
            asset for asset in result
            if asset["stock_available"] >= min_stock
        ]

    return {
        "total": len(result),
        "data": result
    }


@app.get("/assets/{asset_id}")
def get_asset(asset_id: int):

    asset = find_asset(asset_id)

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


@app.put("/assets/{asset_id}")
def update_asset(asset_id: int, asset: AssetCreate):

    old_asset = find_asset(asset_id)

    if old_asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    for item in assets:
        if (
            item["id"] != asset_id
            and item["serial_number"].lower() == asset.serial_number.lower()
        ):
            raise HTTPException(
                status_code=400,
                detail="Serial number already exists"
            )

    old_asset.update(asset.model_dump())

    return {
        "message": "Asset updated successfully",
        "data": old_asset
    }


@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):

    asset = find_asset(asset_id)

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    assets.remove(asset)

    return {
        "message": "Asset deleted successfully"
    }

@app.post("/allocations", status_code=status.HTTP_201_CREATED)
def create_allocation(allocation: AllocationCreate):

    asset = find_asset(allocation.asset_id)

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if asset["status"] != "READY":
        raise HTTPException(
            status_code=400,
            detail="Asset is not available for allocation"
        )

    if allocation.allocated_quantity > asset["stock_available"]:
        raise HTTPException(
            status_code=400,
            detail="Allocated quantity exceeds available stock"
        )

    asset["stock_available"] -= allocation.allocated_quantity

    if asset["stock_available"] == 0:
        asset["status"] = "ALLOCATED"

    new_allocation = {
        "id": len(allocations) + 1,
        **allocation.model_dump()
    }

    allocations.append(new_allocation)

    return {
        "message": "Allocation created successfully",
        "data": new_allocation
    }


@app.get("/allocations")
def get_allocations():

    return {
        "total": len(allocations),
        "data": allocations
    }
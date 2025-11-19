"""
Admin API Module
"""
from fastapi import APIRouter

from . import resellers, products, credit, customers

router = APIRouter()

# Include all admin routers
router.include_router(resellers.router, prefix="", tags=["Admin - Resellers"])
router.include_router(products.router, prefix="/products", tags=["Admin - Products"])
router.include_router(credit.router, prefix="/credit", tags=["Admin - Credit"])
router.include_router(customers.router, prefix="/customers", tags=["Admin - Customers"])

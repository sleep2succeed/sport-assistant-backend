# from fastapi import APIRouter, HTTPException

# # TODO: when service modules are moved into `backend/app/services/`,
# # update this import to `from src.services import proxy`.
# from src.services import proxy

# from src.schemas.chat import ProxyIpResponse

# router = APIRouter(prefix="/proxy", tags=["proxy"])


# @router.get("/ip", response_model=ProxyIpResponse)
# def proxy_ip() -> ProxyIpResponse:
#     try:
#         return ProxyIpResponse(ip="dummpy")#proxy.get_proxy_ip())
#     except Exception as e:
#         raise HTTPException(status_code=502, detail=str(e))

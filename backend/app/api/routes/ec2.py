from fastapi import APIRouter, Depends, HTTPException
from app.services.aws.client import AWSClientProvider
from app.services.aws.ec2 import EC2Scanner
from app.api.middleware.dependency import get_aws_client_provider
import asyncio

router = APIRouter()

@router.get("/ec2/scan-all-regions", tags=["EC2"])
async def scan_all_ec2_instances(
    client_provider: AWSClientProvider = Depends(get_aws_client_provider)
):
    """
    Quét TẤT CẢ các khu vực AWS để tìm mọi máy chủ EC2.
    Yêu cầu phải có một JWT token hợp lệ.
    """
    try:
        # 1. Tạo một instance của scanner, truyền vào "thẻ truy cập" đã được xác thực.
        scanner = EC2Scanner(client_provider)

        # 2. Chạy quá trình quét. Vì scan_all_regions là hàm đồng bộ (sync),
        # chúng ta cần chạy nó trong một luồng riêng để không chặn server.
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(
            None, scanner.scan_all_regions
        )

        # 3. Trả về kết quả
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xảy ra trong quá trình quét: {str(e)}")

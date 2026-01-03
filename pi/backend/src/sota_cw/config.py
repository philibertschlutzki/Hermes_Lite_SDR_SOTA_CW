import os
from pydantic import BaseModel

class Settings(BaseModel):
    hl2_ip: str = os.getenv("SOTA_CW_HL2_IP", "192.168.1.50")
    hl2_port: int = int(os.getenv("SOTA_CW_HL2_PORT", "1024"))
    io_reg_base: int = int(os.getenv("SOTA_CW_IO_REG_BASE", "200"))

settings = Settings()

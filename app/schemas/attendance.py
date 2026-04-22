from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel, TimestampedSchema
from app.schemas.enums import AttendanceStatus
from app.schemas.profiles import StudentDetailResponse


class AttendanceBase(ORMModel):
    lesson_id: UUID
    enrollment_id: UUID
    student_id: UUID
    para: int = Field(default=1, ge=1, le=4)
    status: AttendanceStatus = AttendanceStatus.PRESENT
    note: str | None = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(ORMModel):
    para: int | None = Field(default=None, ge=1, le=4)
    status: AttendanceStatus | None = None
    note: str | None = None


class AttendanceBulkUpsert(ORMModel):
    records: list[AttendanceCreate] = Field(default_factory=list)


class AttendanceResponse(TimestampedSchema, AttendanceBase):
    student: StudentDetailResponse

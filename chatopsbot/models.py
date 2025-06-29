import datetime

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    ForeignKey,
    Text,
    Enum,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base

from consts import TIMEZONE
from enums import PositionEnum

Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    role_name = Column(String, nullable=False, unique=True)
    chat_id = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    notification_threshold = Column(Integer, default=0, nullable=False)
    git_repo_name = Column(String, nullable=True, unique=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    team = relationship("Team", back_populates="services")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    chat_id = Column(String, nullable=True, unique=True)
    thread_id = Column(String, nullable=True, unique=True)

    members = relationship("Employee", back_populates="team")
    services = relationship(
        "Service",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class Employee(Base):
    __tablename__ = "employees"

    id = Column(BigInteger, primary_key=True)
    full_name = Column(String(150), nullable=False)
    telegram_username = Column(String(100), unique=True, nullable=True)
    phone_number = Column(String(20), nullable=True)

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    role = relationship("Role")

    position = Column(
        Enum(PositionEnum),
        default=PositionEnum.DEVELOPER,
        nullable=False,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    team = relationship("Team", back_populates="members")


class ServiceSubscription(Base):
    __tablename__ = "service_subscriptions"

    id = Column(Integer, primary_key=True)
    employee_id = Column(
        BigInteger,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )

    subscription_end = Column(DateTime, nullable=True)

    employee = relationship("Employee", lazy="joined")
    service = relationship("Service", lazy="joined")

    def is_subscription_active(self):
        if self.subscription_end:
            return self.subscription_end > datetime.datetime.now(tz=TIMEZONE)
        return True

    def set_subscription_end(self, hours=0):
        self.subscription_end = datetime.datetime.now(
            tz=TIMEZONE,
        ) + datetime.timedelta(hours=hours)


class RegistrationRequest(Base):
    __tablename__ = "registration_requests"

    id = Column(BigInteger, primary_key=True)
    full_name = Column(String(255), nullable=False)
    telegram_username = Column(String(255), unique=True, nullable=True)
    phone_number = Column(String(50), nullable=True)

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=True,
    )
    role = relationship("Role")

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
    )
    team = relationship("Team")


class ServiceIncident(Base):
    __tablename__ = "service_incidents"

    id = Column(Integer, primary_key=True)
    service_id = Column(
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id = Column(Integer, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    timestamp = Column(
        DateTime,
        default=datetime.datetime.now(tz=TIMEZONE),
    )

    service = relationship("Service", lazy="joined")

    def get_service_chat(self):
        return self.service.team.chat_id

    def acknowledge(self):
        self.acknowledged = True


class MergeRequest(Base):
    __tablename__ = "merge_requests"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    author = Column(String, nullable=True)
    status = Column(String, nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    timestamp = Column(
        DateTime,
        default=datetime.datetime.now(tz=TIMEZONE),
    )

    service = relationship("Service", lazy="joined")

    def get_service_chat(self):
        return self.service.team.chat_id

    def acknowledge(self):
        self.acknowledged = True


__all__ = [
    "Base",
    "Employee",
    "MergeRequest",
    "RegistrationRequest",
    "Role",
    "Service",
    "ServiceIncident",
    "ServiceSubscription",
    "Team",
]

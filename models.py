from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("client_portfolios.id"), nullable=False)
    ticker = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    currency = Column(String, default="USD", nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)

    portfolio = relationship("ClientPortfolio", back_populates="transactions")


class ClientPortfolio(Base):
    __tablename__ = 'client_portfolios'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ClientPortfolio(name={self.name})>"


class Holding(Base):
    __tablename__ = 'holdings'

    id = Column(Integer, primary_key=True)
    datatype = Column(Integer, nullable=False, default=0, server_default="0")
    name = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    ticker = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=False)

    portfolio_id = Column(Integer, ForeignKey('client_portfolios.id'))
    portfolio = relationship("ClientPortfolio", back_populates="holdings")

    def __repr__(self):
        return f"<Holding(name={self.name}, ticker={self.ticker}, quantity={self.quantity})>"


# Replace with your actual DB URL, e.g., 'postgresql://user:pass@localhost/dbname'
DATABASE_URL = 'postgresql://portfolio_user:portfolio_pass@localhost:5432/portfolio_db'


engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()


from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    type = Column(String(50))  # 仓库类型：京仓、云仓、统仓、金融仓
    location = Column(String(200))
    contact = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    inventories = relationship("Inventory", back_populates="store")
    sales = relationship("Sale", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), index=True)
    model = Column(String(200), index=True)
    name = Column(String(300))
    unit = Column(String(20), default="件")
    price = Column(Float, default=0.0)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    inventories = relationship("Inventory", back_populates="product")
    sales = relationship("Sale", back_populates="product")

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=0)
    location = Column(String(100))  # 具体库位
    batch_number = Column(String(50))
    expiry_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    store = relationship("Store", back_populates="inventories")
    product = relationship("Product", back_populates="inventories")

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)
    total_amount = Column(Float)
    sale_date = Column(DateTime(timezone=True))
    customer = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    store = relationship("Store", back_populates="sales")
    product = relationship("Product", back_populates="sales")

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20))
    message = Column(Text)
    module = Column(String(100))
    function = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
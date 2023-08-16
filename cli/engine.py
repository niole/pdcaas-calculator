"""
this initializes the engine and the models
"""

from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

from sqlalchemy import create_engine
engine = create_engine("sqlite:///food.db", echo=True)

class Base(DeclarativeBase):
    pass

class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(60))
    total_protein_g: Mapped[Optional[float]] = mapped_column()
    total_eaa_g: Mapped[Optional[float]] = mapped_column()
    total_complete_digestible_protein_g: Mapped[Optional[float]] = mapped_column()
    limiting_aa: Mapped[Optional[str]] = mapped_column(String(30))
    ingredients: Mapped[List["Ingredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    aas: Mapped[List["RecipeAminoAcid"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )

class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipe.id"))
    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    name: Mapped[str] = mapped_column(String(60))
    unit: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column()
    digestible_protein_g: Mapped[Optional[float]] = mapped_column()
    total_protein_g: Mapped[Optional[float]] = mapped_column()
    td: Mapped[Optional[float]] = mapped_column()
    aas: Mapped[List["IngredientAminoAcid"]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )

class IngredientAminoAcid(Base):
    __tablename__ = "ingredient_amino_acid"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id"))
    ingredient: Mapped["Ingredient"] = relationship(back_populates="aas")
    name: Mapped[str] = mapped_column(String(30))
    g: Mapped[float] = mapped_column()

class RecipeAminoAcid(Base):
    __tablename__ = "recipe_amino_acid"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipe.id"))
    recipe: Mapped["Recipe"] = relationship(back_populates="aas")
    name: Mapped[str] = mapped_column(String(30))
    g: Mapped[float] = mapped_column()

Base.metadata.create_all(engine)

# socialsimullm/frontend/components/forms.py

# -*- coding: utf-8 -*-

"""
Pydantic-to-Streamlit form mapping helpers.

Provides utilities for generating Streamlit form widgets from
Pydantic model field definitions and converting form values
back to Pydantic model instances.

@author: Huang Miaosen
"""

from __future__ import annotations

from typing import Any, Type

import streamlit as st


def pydantic_to_streamlit(
    model_class: Type,
    defaults: dict[str, Any] | None = None,
    prefix: str = "",
) -> dict[str, Any]:
    """Generate Streamlit form fields from a Pydantic model.

    Maps Pydantic field types to appropriate Streamlit widgets:
    - int -> st.number_input
    - float -> st.number_input (step=0.01)
    - str -> st.text_input
    - bool -> st.checkbox
    - list[str] -> st.text_area (split by newline)

    Args:
        model_class: A Pydantic BaseModel subclass.
        defaults: Override default values for specific fields.
        prefix: Optional prefix for widget keys (avoid collisions).

    Returns:
        Dict mapping field names to widget values.
    """
    from pydantic import BaseModel

    if not issubclass(model_class, BaseModel):
        raise TypeError(f"Expected Pydantic BaseModel, got {model_class}")

    values: dict[str, Any] = {}
    defaults = defaults or {}

    for field_name, field_info in model_class.model_fields.items():
        widget_key = f"{prefix}{field_name}" if prefix else field_name
        default = defaults.get(field_name, field_info.default)

        if field_info.annotation is bool or field_info.default is True or field_info.default is False:
            values[field_name] = st.checkbox(
                field_name.replace("_", " ").title(),
                value=bool(default if default is not None else field_info.default),
                key=widget_key,
            )
        elif field_info.annotation is int or "int" in str(field_info.annotation):
            values[field_name] = st.number_input(
                field_name.replace("_", " ").title(),
                value=int(default) if default is not None else 0,
                key=widget_key,
            )
        elif field_info.annotation is float or "float" in str(field_info.annotation):
            values[field_name] = st.number_input(
                field_name.replace("_", " ").title(),
                value=float(default) if default is not None else 0.0,
                step=0.01,
                format="%f",
                key=widget_key,
            )
        elif field_info.annotation is str or "str" in str(field_info.annotation):
            values[field_name] = st.text_input(
                field_name.replace("_", " ").title(),
                value=str(default) if default is not None else "",
                key=widget_key,
            )
        else:
            values[field_name] = st.text_input(
                field_name.replace("_", " ").title(),
                value=str(default) if default is not None else "",
                key=widget_key,
            )

    return values


def form_to_config(
    form_data: dict[str, Any], config_class: Type
) -> Any:
    """Convert Streamlit form values to a Pydantic config instance.

    Args:
        form_data: Dict of field_name -> widget value from the form.
        config_class: The Pydantic model class to instantiate.

    Returns:
        A validated Pydantic model instance.
    """
    return config_class.model_validate(form_data)

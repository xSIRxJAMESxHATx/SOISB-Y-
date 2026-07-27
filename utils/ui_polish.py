"""Small high-end UI fragments."""
from __future__ import annotations
import streamlit as st


def hero_strip(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="sbsby-banner" style="margin-bottom:0.75rem">
          <h1>{title}</h1>
          <p class="subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def soft_divider() -> None:
    st.markdown(
        '<hr style="border:none;height:1px;background:linear-gradient(90deg,transparent,#FF5A00,transparent);margin:1rem 0"/>',
        unsafe_allow_html=True,
    )

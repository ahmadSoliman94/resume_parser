from typing import Any

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    """Line item in an invoice."""

    h_itemnumber: str = Field(..., description="The SKU or product code")
    h_description: str = Field(..., description="The name or description of the item")
    h_quantity: str = Field(..., description="How many units were purchased")
    h_unit: str = Field(..., description="The unit of measurement")
    h_unitprice: str = Field(..., description="The price per unit")
    h_totalprice: str = Field(..., description="The total price for this line item")


class InvoiceData(BaseModel):
    """Invoice data extracted from document."""

    h_invoicenumber: str = Field(
        ..., description="The unique identifier for the invoice"
    )
    h_ordernumber: str = Field(..., description="The unique identifier for the order")
    h_documentdate: str = Field(..., description="The date when the invoice was issued")
    h_creditorname: str = Field(
        ..., description="The name of the company issuing the invoice"
    )
    h_vatid: str = Field(..., description="The VAT ID")
    h_discount: str = Field(..., description="Cash discount offered for early payment")
    h_grossamount: str = Field(..., description="The total amount including taxes")
    h_netamount1: str = Field(..., description="The amount before taxes")
    h_lineitems: list[LineItem] = Field(
        default_factory=list, description="Line items in the invoice"
    )


class PageData(BaseModel):
    """Data extracted from a single page."""

    page_data: InvoiceData


class MultiPageInvoice(BaseModel):
    """Structure for multi-page invoice data."""

    pages: dict[str, InvoiceData] = Field(..., description="Page-specific invoice data")


class ProcessingResponse(BaseModel):
    """Response model for processing requests."""

    status: str
    message: str
    data: dict[str, Any] | None = None
    execution_time: float | None = None

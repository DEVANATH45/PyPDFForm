# -*- coding: utf-8 -*-
"""Contains helpers for filling a PDF form."""

from typing import Dict, Union

import pdfrw
from pdfrw.objects.pdfname import BasePdfName

from ..middleware.element import Element as ElementMiddleware
from ..middleware.element import ElementType
from .constants import Template as TemplateConstants
from .template import Template as TemplateCore
from .utils import Utils
from .watermark import Watermark as WatermarkCore


class Filler:
    """Contains methods for filling a PDF form with dict."""

    @staticmethod
    def fill(template_stream: bytes, elements: Dict[str, "ElementMiddleware"]) -> bytes:
        """Fills a PDF using watermarks."""

        template_pdf = pdfrw.PdfReader(fdata=template_stream)

        texts_to_draw = {}
        text_watermarks = []

        radio_button_tracker = {}

        for page, _elements in (
            TemplateCore().get_elements_by_page(template_pdf).items()
        ):
            texts_to_draw[page] = []
            text_watermarks.append(b"")
            for _element in _elements:
                key = TemplateCore().get_element_key(_element)

                update_dict = {
                    TemplateConstants().field_editable_key.replace(
                        "/", ""
                    ): pdfrw.PdfObject(1)
                }
                if elements[key].type == ElementType.checkbox:
                    update_dict[
                        TemplateConstants().checkbox_field_value_key.replace("/", "")
                    ] = Utils().bool_to_checkbox(elements[key].value)
                elif elements[key].type == ElementType.radio:
                    if key not in radio_button_tracker:
                        radio_button_tracker[key] = 0
                    radio_button_tracker[key] += 1

                    if elements[key].value == radio_button_tracker[key] - 1:
                        _element.update(
                            pdfrw.PdfDict(
                                **{
                                    TemplateConstants().checkbox_field_value_key.replace(
                                        "/", ""
                                    ): BasePdfName(
                                        "/" + str(elements[key].value), False
                                    ),
                                }
                            )
                        )

                    _element[TemplateConstants().radio_button_group_key].update(
                        pdfrw.PdfDict(
                            **{
                                TemplateConstants().field_editable_key.replace(
                                    "/", ""
                                ): pdfrw.PdfObject(1)
                            }
                        )
                    )
                    continue
                else:
                    texts_to_draw[page].append(
                        [
                            elements[key],
                            TemplateCore().get_draw_text_coordinates(_element)[0],
                            TemplateCore().get_draw_text_coordinates(_element)[1],
                        ]
                    )
                _element.update(pdfrw.PdfDict(**update_dict))

        for page, texts in texts_to_draw.items():
            _watermarks = WatermarkCore().create_watermarks_and_draw(
                template_stream, page, "text", texts
            )
            for i, watermark in enumerate(_watermarks):
                if watermark:
                    text_watermarks[i] = watermark

        return WatermarkCore().merge_watermarks_with_pdf(
            Utils().generate_stream(template_pdf), text_watermarks
        )

    @staticmethod
    def simple_fill(
        template_stream: bytes,
        data: Dict[str, Union[str, bool, int]],
        editable: bool,
    ) -> bytes:
        """Fills a PDF form in simple mode."""

        template_pdf = pdfrw.PdfReader(fdata=template_stream)
        data = Utils().bool_to_checkboxes(data)

        radio_button_tracker = {}

        for element in TemplateCore().iterate_elements(template_pdf):
            key = TemplateCore().get_element_key(element)

            if key in data.keys():
                update_dict = {}
                if data[key] in [
                    pdfrw.PdfName.Yes,
                    pdfrw.PdfName.Off,
                ]:
                    update_dict = {
                        TemplateConstants().checkbox_field_value_key.replace(
                            "/", ""
                        ): data[key]
                    }
                elif isinstance(data[key], int):
                    if key not in radio_button_tracker:
                        radio_button_tracker[key] = 0
                    radio_button_tracker[key] += 1

                    if data[key] == radio_button_tracker[key] - 1:
                        element.update(
                            pdfrw.PdfDict(
                                **{
                                    TemplateConstants().checkbox_field_value_key.replace(
                                        "/", ""
                                    ): BasePdfName(
                                        "/" + str(data[key]), False
                                    ),
                                }
                            )
                        )

                        if not editable:
                            element[TemplateConstants().radio_button_group_key].update(
                                pdfrw.PdfDict(
                                    **{
                                        TemplateConstants().field_editable_key.replace(
                                            "/", ""
                                        ): pdfrw.PdfObject(1)
                                    }
                                )
                            )
                        continue
                else:
                    update_dict = {
                        TemplateConstants().text_field_value_key.replace("/", ""): data[
                            key
                        ]
                    }

                if not editable:
                    update_dict[
                        TemplateConstants().field_editable_key.replace("/", "")
                    ] = pdfrw.PdfObject(1)

                element.update(pdfrw.PdfDict(**update_dict))

        return Utils().generate_stream(template_pdf)

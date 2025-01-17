# -*- coding: utf-8 -*-

import os
import uuid

import pdfrw
import pytest

from PyPDFForm.core.constants import Merge as MergeCoreConstants
from PyPDFForm.core.constants import Template as TemplateCoreConstants
from PyPDFForm.core.template import Template as TemplateCore
from PyPDFForm.middleware.element import ElementType
from PyPDFForm.middleware.exceptions.template import InvalidTemplateError
from PyPDFForm.middleware.template import Template as TemplateMiddleware


@pytest.fixture
def pdf_samples():
    return os.path.join(os.path.dirname(__file__), "..", "..", "pdf_samples", "v2")


@pytest.fixture
def template_stream(pdf_samples):
    with open(os.path.join(pdf_samples, "sample_template.pdf"), "rb+") as f:
        return f.read()


@pytest.fixture
def template_with_radiobutton_stream(pdf_samples):
    with open(
        os.path.join(pdf_samples, "sample_template_with_radio_button.pdf"), "rb+"
    ) as f:
        return f.read()


@pytest.fixture
def data_dict():
    return {
        "test": False,
        "check": False,
        "radio_1": False,
        "test_2": False,
        "check_2": False,
        "radio_2": False,
        "test_3": False,
        "check_3": False,
        "radio_3": False,
    }


def test_validate_template():
    bad_inputs = [""]

    try:
        TemplateMiddleware().validate_template(*bad_inputs)
        assert False
    except InvalidTemplateError:
        assert True


def test_validate_template_stream(template_stream):
    try:
        TemplateMiddleware().validate_stream(b"")
        assert False
    except InvalidTemplateError:
        assert True

    TemplateMiddleware().validate_stream(template_stream)
    assert True


def test_iterate_elements_and_get_element_key(
    template_with_radiobutton_stream, data_dict
):
    for each in TemplateCore().iterate_elements(template_with_radiobutton_stream):
        data_dict[TemplateCore().get_element_key(each)] = True

    for k in data_dict.keys():
        assert data_dict[k]


def test_get_elements_by_page(template_with_radiobutton_stream):
    expected = {
        1: {
            "test": False,
            "check": False,
            "radio_1": False,
        },
        2: {
            "test_2": False,
            "check_2": False,
            "radio_2": False,
        },
        3: {
            "test_3": False,
            "check_3": False,
            "radio_3": False,
        },
    }

    for page, elements in (
        TemplateCore().get_elements_by_page(template_with_radiobutton_stream).items()
    ):
        for each in elements:
            expected[page][TemplateCore().get_element_key(each)] = True

    for page, elements in expected.items():
        for k in elements.keys():
            assert expected[page][k]


def test_get_element_type(template_stream):
    type_mapping = {
        "test": ElementType.text,
        "check": ElementType.checkbox,
        "test_2": ElementType.text,
        "check_2": ElementType.checkbox,
        "test_3": ElementType.text,
        "check_3": ElementType.checkbox,
    }

    for each in TemplateCore().iterate_elements(template_stream):
        assert type_mapping[
            TemplateCore().get_element_key(each)
        ] == TemplateCore().get_element_type(each)

    read_template_stream = pdfrw.PdfReader(fdata=template_stream)

    for each in TemplateCore().iterate_elements(read_template_stream):
        assert type_mapping[
            TemplateCore().get_element_key(each)
        ] == TemplateCore().get_element_type(each)


def test_get_element_type_radiobutton(template_with_radiobutton_stream):
    type_mapping = {
        "test": ElementType.text,
        "check": ElementType.checkbox,
        "test_2": ElementType.text,
        "check_2": ElementType.checkbox,
        "test_3": ElementType.text,
        "check_3": ElementType.checkbox,
        "radio_1": ElementType.radio,
        "radio_2": ElementType.radio,
        "radio_3": ElementType.radio,
    }

    for each in TemplateCore().iterate_elements(template_with_radiobutton_stream):
        assert type_mapping[
            TemplateCore().get_element_key(each)
        ] == TemplateCore().get_element_type(each)

    read_template_stream = pdfrw.PdfReader(fdata=template_with_radiobutton_stream)

    for each in TemplateCore().iterate_elements(read_template_stream):
        assert type_mapping[
            TemplateCore().get_element_key(each)
        ] == TemplateCore().get_element_type(each)


def test_build_elements(template_with_radiobutton_stream, data_dict):
    for k, v in (
        TemplateMiddleware().build_elements(template_with_radiobutton_stream).items()
    ):
        if k in data_dict and k == v.name:
            data_dict[k] = True

    for k in data_dict.keys():
        assert data_dict[k]


def test_get_draw_text_coordinates(template_stream):
    for element in TemplateCore().iterate_elements(template_stream):
        assert TemplateCore().get_draw_text_coordinates(element) == (
            float(element[TemplateCoreConstants().annotation_rectangle_key][0]),
            (
                float(element[TemplateCoreConstants().annotation_rectangle_key][1])
                + float(element[TemplateCoreConstants().annotation_rectangle_key][3])
            )
            / 2
            - 2,
        )


def test_assign_uuid(template_with_radiobutton_stream, data_dict):
    for element in TemplateCore().iterate_elements(
        TemplateCore().assign_uuid(template_with_radiobutton_stream)
    ):
        key = TemplateCore().get_element_key(element)
        assert MergeCoreConstants().separator in key

        key, _uuid = key.split(MergeCoreConstants().separator)

        assert len(_uuid) == len(uuid.uuid4().hex)
        data_dict[key] = True

    for k in data_dict.keys():
        assert data_dict[k]

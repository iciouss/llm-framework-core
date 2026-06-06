import pytest

from llm_framework.tools.builtins import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
    subtract_numbers,
)


def test_add_integers():
    result = add_numbers(2, 3)
    print(f"add(2, 3) = {result}")
    assert result == 5


def test_add_floats():
    result = add_numbers(1.5, 2.5)
    print(f"add(1.5, 2.5) = {result}")
    assert result == pytest.approx(4.0)


def test_add_negative():
    result = add_numbers(-3, 1)
    print(f"add(-3, 1) = {result}")
    assert result == -2


def test_subtract():
    result = subtract_numbers(10, 4)
    print(f"subtract(10, 4) = {result}")
    assert result == 6


def test_subtract_negative_result():
    result = subtract_numbers(2, 5)
    print(f"subtract(2, 5) = {result}")
    assert result == -3


def test_multiply():
    result = multiply_numbers(3, 4)
    print(f"multiply(3, 4) = {result}")
    assert result == 12


def test_multiply_by_zero():
    result = multiply_numbers(999, 0)
    print(f"multiply(999, 0) = {result}")
    assert result == 0


def test_multiply_floats():
    result = multiply_numbers(2.5, 4.0)
    print(f"multiply(2.5, 4.0) = {result}")
    assert result == pytest.approx(10.0)


def test_divide():
    result = divide_numbers(10, 2)
    print(f"divide(10, 2) = {result}")
    assert result == pytest.approx(5.0)


def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero") as exc_info:
        divide_numbers(1, 0)
    print(f"divide(1, 0) raised: {exc_info.value}")


def test_divide_floats():
    result = divide_numbers(1.0, 3.0)
    print(f"divide(1.0, 3.0) = {result:.6f}")
    assert result == pytest.approx(1 / 3)


def test_tools_have_schema():
    for fn in [add_numbers, subtract_numbers, multiply_numbers, divide_numbers]:
        has = hasattr(fn, "schema")
        print(f"  {fn.__name__}.schema present: {has}")
        assert has, f"{fn.__name__} missing schema"

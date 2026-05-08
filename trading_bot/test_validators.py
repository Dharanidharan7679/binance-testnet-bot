"""Validation unit tests — run to verify all validators work correctly."""
from bot.validators import validate_order_params, ValidationError

tests_passed = 0
tests_failed = 0

def check(name, fn):
    global tests_passed, tests_failed
    try:
        fn()
        print(f"  [PASS] {name}")
        tests_passed += 1
    except AssertionError as e:
        print(f"  [FAIL] {name}: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: unexpected exception: {e}")
        tests_failed += 1

print("\n--- Validator Tests ---\n")

# 1. LIMIT order missing price must raise
def t1():
    raised = False
    try:
        validate_order_params("BTCUSDT", "BUY", "LIMIT", 0.01, price=None)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for LIMIT without price"
check("LIMIT order without price raises ValidationError", t1)

# 2. Negative quantity must raise
def t2():
    raised = False
    try:
        validate_order_params("BTCUSDT", "BUY", "MARKET", -1)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for negative quantity"
check("Negative quantity raises ValidationError", t2)

# 3. Invalid side must raise
def t3():
    raised = False
    try:
        validate_order_params("BTCUSDT", "LONG", "MARKET", 0.01)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for invalid side 'LONG'"
check("Invalid side raises ValidationError", t3)

# 4. STOP missing stop_price must raise
def t4():
    raised = False
    try:
        validate_order_params("BTCUSDT", "SELL", "STOP", 0.01, price=85000, stop_price=None)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for STOP without stop_price"
check("STOP order without stop_price raises ValidationError", t4)

# 5. Valid MARKET order — lowercase input is normalised
def t5():
    result = validate_order_params("btcusdt", "buy", "market", 0.01)
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "BUY"
    assert result["order_type"] == "MARKET"
    assert result["price"] is None
check("Valid MARKET order normalises symbol/side/type to uppercase", t5)

# 6. Valid LIMIT order
def t6():
    result = validate_order_params("ETHUSDT", "SELL", "LIMIT", 0.5, price=3200.0)
    assert result["price"] == 3200.0
    assert result["order_type"] == "LIMIT"
check("Valid LIMIT order sets price correctly", t6)

# 7. Valid STOP order
def t7():
    result = validate_order_params("BTCUSDT", "SELL", "STOP", 0.01, price=85000, stop_price=85500)
    assert result["stop_price"] == 85500
    assert result["price"] == 85000
check("Valid STOP order sets price and stop_price", t7)

# 8. STOP_MARKET missing stop_price must raise
def t8():
    raised = False
    try:
        validate_order_params("BTCUSDT", "SELL", "STOP_MARKET", 0.01, stop_price=None)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for STOP_MARKET without stop_price"
check("STOP_MARKET without stop_price raises ValidationError", t8)

# 9. Symbol with numbers raises
def t9():
    raised = False
    try:
        validate_order_params("BTC123", "BUY", "MARKET", 0.01)
    except ValidationError:
        raised = True
    assert raised, "Expected ValidationError for symbol with digits"
check("Symbol with digits raises ValidationError", t9)

print(f"\n--- Results: {tests_passed} passed, {tests_failed} failed ---\n")

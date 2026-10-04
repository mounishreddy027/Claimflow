from decimal import ROUND_HALF_EVEN, Decimal

TWOPLACES = Decimal("0.01")


def to_decimal(value: object) -> Decimal:
    """Convert input value to high-precision Decimal with scale 2 (Banker's rounding)."""
    if isinstance(value, Decimal):
        return value.quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)


def calculate_payable_amount(
    claim_amount: Decimal,
    sum_insured: Decimal,
    deductible: Decimal,
    copay: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Calculate financial assessment according to AC-05 & NFR-01:
    effective_claim = min(claim_amount, sum_insured)
    gross_deductions = deductible + copay
    net_payable = effective_claim - gross_deductions
    payable_amount = max(0.00, net_payable)
    """
    c_amt = to_decimal(claim_amount)
    s_ins = to_decimal(sum_insured)
    ded = to_decimal(deductible)
    c_pay = to_decimal(copay)

    effective_claim = min(c_amt, s_ins)
    gross_deductions = to_decimal(ded + c_pay)
    net_payable = to_decimal(effective_claim - gross_deductions)
    payable_amount = max(Decimal("0.00"), net_payable)

    return (effective_claim, gross_deductions, net_payable, payable_amount)

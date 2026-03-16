def calculate_emi(principal, rate, tenure):

    monthly_rate = rate / (12 * 100)

    emi = (principal * monthly_rate * (1 + monthly_rate) ** tenure) / \
          ((1 + monthly_rate) ** tenure - 1)

    return round(emi, 2)
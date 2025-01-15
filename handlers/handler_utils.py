def predict_rub_salary(salary_from: int, salary_to: int) -> int:
    if salary_from and salary_to:
        return round((salary_from + salary_to) / 2)
    if salary_from:
        return round(salary_from * 1.2)
    if salary_to:
        return round(salary_to * 0.8)
    if not salary_from and not salary_to:
        return 0

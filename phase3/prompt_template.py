def comparable_explanation_prompt(subject, comparable):
    return (
        "Given the subject property:\n"
        f"{subject}\n\n"
        "and this comparable property:\n"
        f"{comparable}\n\n"
        "Write 1-2 sentences explaining why this is a good comparable property (mention similarity in size, location, age, and type)."
    )

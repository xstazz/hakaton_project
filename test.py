import g4f

def generate_menu_from_prompt(prompt):
    response = g4f.ChatCompletion.create(
        model=g4f.models.blackbox,
        messages=[{"role": "user", "content": prompt}],
    )
    return response
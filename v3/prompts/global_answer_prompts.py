def get_prompts(answers: list[str]):
    GLOBAL_ANSWER_PROMPTS = f"""
You are an AI assistant that helps a human analyst to perform general information discovery. Information discovery is the process of identifying and assessing relevant information associated with certain entities (e.g., organizations and individuals) within a network.

# Goal
Summarize the list of answers into a detail, comprehensive and exploratory paragraph. Remember, ONLY USE the information from answers.

# Real data

Answers:
{answers}

Output:
"""

    return GLOBAL_ANSWER_PROMPTS
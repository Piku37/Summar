import re
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_google_genai import GoogleGenerativeAI

# Initialize LLM (again, or import from summarizer)
llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)


def generate_quiz(summary_md):
    """
    Return a list of 5 MCQs (2 easy, 2 medium, 1 hard) with explanations.
    """
    quiz_prompt = (
        "Based on the following markdown summary, generate a multiple-choice quiz "
        "with 5 questions: 2 easy, 2 medium, and 1 hard. Format each question as:\n\n"
        "Question <n> [<difficulty>]:\n"
        "Question: <text>\n"
        "Option A: <text>\n"
        "Option B: <text>\n"
        "Option C: <text>\n"
        "Option D: <text>\n"
        "Answer: <letter>\n"
        "Explanation: <text>\n\n"
        "Summary:\n{text}"
    )
    prompt_template = PromptTemplate(template=quiz_prompt, input_variables=["text"])
    chain = LLMChain(llm=llm, prompt=prompt_template)
    raw = chain.run({"text": summary_md})
    return parse_quiz_text(raw)


def parse_quiz_text(quiz_text):
    """
    Parse raw quiz text into structured list of dicts.
    """
    questions = []
    parts = re.split(r"\n\s*\n", quiz_text.strip())
    for part in parts:
        lines = part.splitlines()
        if len(lines) < 8:
            continue
        diff = re.search(r"Question\s+\d+\s+\[(\w+)\]", lines[0]).group(1).lower()
        q_text = re.match(r"Question:\s*(.+)", lines[1]).group(1)
        opts = {
            m.group(1): m.group(2)
            for m in (re.match(r"Option\s+([A-D]):\s*(.+)", l) for l in lines[2:6])
            if m
        }
        ans = re.match(r"Answer:\s*([A-D])", lines[6]).group(1)
        expl = re.match(r"Explanation:\s*(.+)", lines[7]).group(1)
        questions.append({
            "difficulty": diff,
            "question": q_text,
            "options": opts,
            "correct_answer": ans,
            "explanation": expl
        })
    return questions

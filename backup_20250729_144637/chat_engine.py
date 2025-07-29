# chat_engine.py
from openai import OpenAI
from memory_manager import retrieve_memories, store_memory

openai_client = OpenAI()

SYSTEM_PROMPT = """
You are a helpful assistant. Only use the facts given in 'Memories:' to answer.
If none are relevant, say "I don't recall that."
"""

def build_prompt(user_input, memories):
    messages = [{"role":"system","content":SYSTEM_PROMPT.strip()}]
    if memories:
        mem_lines = "\n".join(f"- [{m['category']}] {m['summary']}" for m in memories)
        messages.append({"role":"assistant","content":"Memories:\n" + mem_lines})
    else:
        messages.append({"role":"assistant","content":"Memories:\n- None"})
    messages.append({"role":"user","content":user_input})
    return messages

def chat_with_memory(user_input: str) -> str:
    # 1) Retrieve past facts
    memories = retrieve_memories(user_input)

    # 2) Build prompt & call ChatCompletion
    prompt = build_prompt(user_input, memories)
    resp = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        temperature=0
    )
    answer = resp.choices[0].message.content.strip()

    # 3) Store the user turn as a new memory
    store_memory(user_input)
    return answer

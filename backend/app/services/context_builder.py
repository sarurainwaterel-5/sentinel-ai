class ContextBuilder:
    def build_context(
        self,
        question: str,
        chunks: list,
    ) -> str:
        context_blocks = []

        for index, point in enumerate(chunks, start=1):
            payload = point.payload or {}

            context_blocks.append(
                f"""
Source {index}
Filename: {payload.get("filename")}
Module: {payload.get("module")}
Topic: {payload.get("topic")}
Collection: {payload.get("collection")}
Chunk Index: {payload.get("chunk_index")}
Similarity Score: {point.score}

Text:
{payload.get("text")}
""".strip()
            )

        context = "\n\n---\n\n".join(context_blocks)

        return f"""
Question:
{question}

Use only the supplied evidence.

Requirements:

- Answer the question directly.
- Do not introduce facts that are absent from the evidence.
- Explain briefly why the evidence supports or limits the answer.
- Recommend one practical next step.
- Suggest one natural follow-up question.
- Return two to five concise related-topic labels.
- If the evidence is insufficient, state that clearly in the answer.

Evidence:
{context}
""".strip()

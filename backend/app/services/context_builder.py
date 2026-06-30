class ContextBuilder:
    def build_context(self, question: str, chunks: list):
        context_blocks = []

        for index, point in enumerate(chunks, start=1):
            payload = point.payload

            context_blocks.append(
                f"""
Source {index}
Filename: {payload.get("filename")}
Chunk Index: {payload.get("chunk_index")}
Score: {point.score}

Text:
{payload.get("text")}
"""
            )

        context = "\n---\n".join(context_blocks)

        return f"""
Question:
{question}

Use only the evidence below to answer.

Evidence:
{context}

Return:
1. Answer
2. Evidence used
3. Confidence level
4. Recommended next step
"""

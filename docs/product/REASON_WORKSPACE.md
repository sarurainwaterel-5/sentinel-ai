# Reason local operator release

Reason implements ADR-035’s cockpit hierarchy: mission, supported judgment, independent confidence and governance, inspectable evidence, safe operational trace, distinct limitations/alternatives/missing information, and recommended next action. Presentation does not create inference or authorize execution.

The shared domain and optional exact topic filter are sent to retrieval. The operator may inspect bounded retrieval controls (1–25 chunks and 0–1 minimum similarity); similarity remains separate from confidence. Questions are bounded to 10,000 characters, metadata to 200 characters, and workspace labels to 100 characters in the public request contract.

Each completed report preserves its submitted question, domain, retrieval settings, mission identifier and completion time. Drafts and the last report are retained in the current browser tab where session storage is available. Domain changes cannot silently relabel an older judgment. The previous report remains identifiable while a new request is pending or fails; Clear report explicitly removes it. This browser snapshot is not durable server-side reasoning history.

The request supports stopping local waiting and aborts on navigation. A three-minute wait limit prevents indefinite loading. Aborting local HTTP waiting does not promise to stop provider processing. No autonomous action is authorized. Transport, provider and invalid-report failures are readable; the preserved question/settings support an explicit retry.

Insufficient evidence remains a backend outcome with zero/low confidence and preserved gaps, rather than a generated answer. Teach and Recall routes help the operator acquire or inspect evidence. Confidence factor explanations and contributions, complete source excerpts and provenance, backend uncertainty, and constitutional evaluation remain independently inspectable. An unassessed evaluation receives no constitutional meter or acceptance claim. ADR-037 remains Proposed and proposition-to-inference remains closed.

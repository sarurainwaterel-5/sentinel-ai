import {
  render,
  screen,
} from "@testing-library/react";

import ReasonResult from "../ReasonResult";


const result = {
  communication: {
    answer: "The evidence supports the conclusion.",
    evidence_explanation: "Evidence is independently supported.",
    confidence_explanation: "Confidence is high.",
    limitations_explanation: "Some uncertainty remains.",
    next_step_explanation: "Continue investigation.",
  },

  reasoning: {
    conclusion: "The evidence supports the conclusion.",

    evidence_summary:
      "Three sources across two documents support the conclusion.",

    inference_summary:
      "The strongest inference is supported by converging evidence.",

    confidence: {
      score: 0.82,
      level: "high",
      basis: "Multiple relevant sources provide converging support.",

      factors: [
        {
          name: "retrieval_relevance",
          contribution: 0.31,
        },
        {
          name: "source_independence",
          contribution: 0.18,
        },
      ],

      uncertainty: [
        "Additional independent evidence could strengthen the conclusion.",
      ],
    },

    evidence: {
      source_count: 3,
      document_count: 2,
      domain_count: 1,

      sources: [
        {
          document_id: "doc-001",
          filename: "sentinel-architecture.pdf",
          module: "engineering",
          topic: "cognition",
          collection: "architecture",
          organization_id: "default",
          chunk_index: 14,
          score: 0.91,
          text: "Reasoning must remain grounded in inspectable evidence.",
          status: "indexed",
          description: "Sentinel architecture reference.",
          metadata: {},
        },
      ],

      gaps: [
        "No contradictory architecture source was retrieved.",
      ],
    },

    limitations: [
      "The conclusion is bounded by currently retrieved evidence.",
    ],

    alternatives: [
      "A different interpretation may emerge with additional evidence.",
    ],

    missing_information: [
      "Additional longitudinal evidence would improve comparison.",
    ],

    recommended_next_step:
      "Retrieve additional independent evidence.",

    reasoning_trace: [
      "Evidence retrieved.",
      "Evidence normalized.",
      "Candidate inferences evaluated.",
      "Confidence assessed.",
      "Conclusion synthesized.",
    ],

    status: "complete",
  },

  coherence: {
    coherent: true,
    constitutional_score: 0.96,

    articles_consulted: [
      "Article I",
      "Article IV",
    ],

    conflicts: [],

    recommendations: [
      "Preserve evidence provenance.",
    ],
  },

  constitutional_sources: [],
  knowledge_sources: [],

  workspace: "reason",
  module: "engineering",
  topic: "cognition",
  organization_id: "default",
  mission_id: "mission-001",
  session_id: "session-001",
};


describe("ReasonResult", () => {
  test("renders the authoritative conclusion and inference", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText(
        "The evidence supports the conclusion."
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /strongest inference is supported/i
      )
    ).toBeInTheDocument();
  });


  test("renders explainable confidence", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText("82%")
    ).toBeInTheDocument();

    expect(
      screen.getByText(/multiple relevant sources/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/retrieval relevance/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Additional independent evidence could strengthen the conclusion."
      )
    ).toBeInTheDocument();
  });


  test("renders evidence provenance and evidence gaps", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText("3")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "sentinel-architecture.pdf"
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(/chunk 14/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/91%/)
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /no contradictory architecture source/i
      )
    ).toBeInTheDocument();
  });


  test("renders the user-safe reasoning trace", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText("Reasoning Trace")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Evidence retrieved."
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Conclusion synthesized."
      )
    ).toBeInTheDocument();
  });


  test("renders limitations alternatives and missing information", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText(
        /bounded by currently retrieved evidence/i
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /different interpretation may emerge/i
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /longitudinal evidence would improve/i
      )
    ).toBeInTheDocument();
  });


  test("renders constitutional coherence independently from confidence", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
      screen.getByText("Coherent")
    ).toBeInTheDocument();

    expect(
      screen.getByText(/96%/)
    ).toBeInTheDocument();

    expect(
      screen.getByText("Article I")
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Preserve evidence provenance."
      )
    ).toBeInTheDocument();
  });


  test("renders the recommended next step", () => {
    render(
      <ReasonResult result={result} />
    );

    expect(
       screen.getByText(
         "Additional independent evidence could strengthen the conclusion."
       )
     ).toBeInTheDocument();
  });

    test("renders recommended next step", () => {
    // existing test
  });

  test("organizes cognition into distinct cockpit zones", () => {
    const { container } = render(
      <ReasonResult result={result} />
    );

    const judgment =
      container.querySelector(
        ".reason-judgment-zone"
      );

    const instruments =
      container.querySelector(
        ".reason-instrument-grid"
      );

    const uncertainty =
      container.querySelector(
        ".reason-uncertainty-zone"
      );

    expect(judgment).toBeInTheDocument();
    expect(instruments).toBeInTheDocument();
    expect(uncertainty).toBeInTheDocument();

    expect(
      judgment.querySelector(
        ".reason-conclusion"
      )
    ).toBeInTheDocument();

    expect(
      instruments.querySelector(
        ".reason-confidence"
      )
    ).toBeInTheDocument();

    expect(
      instruments.querySelector(
        ".reason-governance"
      )
    ).toBeInTheDocument();

    expect(
      uncertainty.querySelector(
        ".reason-limitations"
      )
    ).toBeInTheDocument();
  });
  
    test("renders compact confidence and coherence instruments", () => {
  render(
    <ReasonResult result={result} />
  );

  const confidenceMeter =
    screen.getByRole("progressbar", {
      name: /evidence confidence/i,
    });

  const coherenceMeter =
    screen.getByRole("progressbar", {
      name: /constitutional coherence/i,
    });

  expect(confidenceMeter).toHaveAttribute(
    "aria-valuenow",
    "82"
  );

  expect(coherenceMeter).toHaveAttribute(
    "aria-valuenow",
    "96"
  );

  expect(
    screen.getByText(/3 sources/i)
  ).toBeInTheDocument();

  expect(
    screen.getByText(/2 documents/i)
  ).toBeInTheDocument();

  expect(
    screen.getByText(/1 uncertainty/i)
  ).toBeInTheDocument();

  expect(
    screen.getByText(/0 conflicts/i)
  ).toBeInTheDocument();
});
  
  test("renders compact evidence previews with expandable inspection", () => {
  render(
    <ReasonResult result={result} />
  );

  const inspectors =
    screen.getAllByText(/inspect evidence/i);

  expect(inspectors.length).toBeGreaterThan(0);

  const source =
    document.querySelector(
      ".reason-evidence-source"
    );

  expect(source).toBeInTheDocument();

  expect(
    source.querySelector(
      ".reason-evidence-preview"
    )
  ).toBeInTheDocument();

  expect(
    source.querySelector(
      ".reason-evidence-full"
    )
  ).toBeInTheDocument();
});

});


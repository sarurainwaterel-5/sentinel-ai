import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import { vi } from "vitest";

import Reason from "../Reason";

vi.mock("../../services/reasonApi", () => ({
  reasonAbout: vi.fn(),
}));

import {
  reasonAbout,
} from "../../services/reasonApi";

vi.mock("../../context/useDomain", () => ({
  useDomain: vi.fn(),
}));

import {
  useDomain,
} from "../../context/useDomain";


describe("Reason workspace", () => {
  beforeEach(() => {
  vi.clearAllMocks();

  useDomain.mockReturnValue({
    activeDomain: {
      id: "all",
      name: "All Domains",
      kind: "cross-domain",
    },
  });
});


test("scopes reasoning to the active domain", async () => {
  useDomain.mockReturnValue({
    activeDomain: {
      id: "engineering",
      name: "Engineering",
      kind: "system",
    },
  });

  reasonAbout.mockResolvedValue({
    reasoning: {
      conclusion: "Domain-scoped conclusion.",
      confidence: {
        score: 0.8,
        level: "high",
        basis: "Domain evidence.",
        factors: [],
        uncertainty: [],
      },
      evidence: {
        source_count: 1,
        document_count: 1,
        domain_count: 1,
        sources: [],
        gaps: [],
      },
      limitations: [],
      alternatives: [],
      missing_information: [],
      reasoning_trace: [],
      status: "complete",
    },

    coherence: {
      coherent: true,
      constitutional_score: 1,
      articles_consulted: [],
      conflicts: [],
      recommendations: [],
    },
  });

  render(<Reason />);

  fireEvent.change(
    screen.getByRole("textbox"),
    {
      target: {
        value: "Evaluate engineering evidence.",
      },
    }
  );

  fireEvent.click(
    screen.getByRole(
      "button",
      { name: /analyze evidence/i }
    )
  );

  await waitFor(() => {
    expect(reasonAbout).toHaveBeenCalledWith(
      expect.objectContaining({
        question: "Evaluate engineering evidence.",
        workspace: "reason",
        module: "engineering",
      })
    );
  });
});


  test("renders the reasoning mission input", () => {
    render(<Reason />);

    expect(
      screen.getByText(/reasoning mission/i)
    ).toBeInTheDocument();

    expect(
      screen.getByRole("textbox")
    ).toBeInTheDocument();

    expect(
      screen.getByRole(
        "button",
        { name: /analyze evidence/i }
      )
    ).toBeInTheDocument();
  });


  test("rejects an empty reasoning question", async () => {
    render(<Reason />);

    fireEvent.click(
      screen.getByRole(
        "button",
        { name: /analyze evidence/i }
      )
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent(
      /what should sentinel reason about/i
    );

    expect(
      reasonAbout
    ).not.toHaveBeenCalled();
  });


  test("submits a valid reasoning request", async () => {
    reasonAbout.mockResolvedValue({
      answer: "Supported conclusion.",
      reasoning: {
        conclusion: "Supported conclusion.",
        evidence_summary: "Evidence summary.",
        inference_summary: "Inference summary.",
        confidence: {
          score: 0.82,
          level: "high",
          basis: "Strong evidence support.",
          factors: [],
          uncertainty: [],
        },
        evidence: {
          source_count: 2,
          document_count: 2,
          domain_count: 1,
          sources: [],
          gaps: [],
        },
        limitations: [],
        alternatives: [],
        missing_information: [],
        recommended_next_step: (
          "Continue investigation."
        ),
        reasoning_trace: [
          "Evidence retrieved.",
          "Inference evaluated.",
        ],
        status: "complete",
      },
      coherence: {
        coherent: true,
        constitutional_score: 1.0,
        articles_consulted: [],
        conflicts: [],
        recommendations: [],
      },
      constitutional_sources: [],
      knowledge_sources: [],
      workspace: "reason",
      module: null,
      topic: null,
      organization_id: "default",
      mission_id: null,
      session_id: null,
    });

    render(<Reason />);

    fireEvent.change(
      screen.getByRole("textbox"),
      {
        target: {
          value: (
            "What does the available evidence support?"
          ),
        },
      }
    );

    fireEvent.click(
      screen.getByRole(
        "button",
        { name: /analyze evidence/i }
      )
    );

    await waitFor(() => {
      expect(
        reasonAbout
      ).toHaveBeenCalledTimes(1);
    });

    expect(
      reasonAbout
    ).toHaveBeenCalledWith(
      expect.objectContaining({
        question: (
          "What does the available evidence support?"
        ),
      })
    );
  });


  test("renders completed reasoning", async () => {
    reasonAbout.mockResolvedValue({
      answer: "The evidence supports the conclusion.",
      reasoning: {
        conclusion: (
          "The evidence supports the conclusion."
        ),
        evidence_summary: (
          "Two independent sources support it."
        ),
        inference_summary: (
          "The inference is evidence-grounded."
        ),
        confidence: {
          score: 0.82,
          level: "high",
          basis: "Strong evidence support.",
          factors: [],
          uncertainty: [],
        },
        evidence: {
          source_count: 2,
          document_count: 2,
          domain_count: 1,
          sources: [],
          gaps: [],
        },
        limitations: [],
        alternatives: [],
        missing_information: [],
        recommended_next_step: (
          "Continue investigation."
        ),
        reasoning_trace: [
          "Evidence retrieved.",
          "Inference evaluated.",
        ],
        status: "complete",
      },
      coherence: {
        coherent: true,
        constitutional_score: 1.0,
        articles_consulted: [],
        conflicts: [],
        recommendations: [],
      },
      constitutional_sources: [],
      knowledge_sources: [],
      workspace: "reason",
      organization_id: "default",
    });

    render(<Reason />);

    fireEvent.change(
      screen.getByRole("textbox"),
      {
        target: {
          value: "Evaluate this evidence.",
        },
      }
    );

    fireEvent.click(
      screen.getByRole(
        "button",
        { name: /analyze evidence/i }
      )
    );

    expect(
      await screen.findByText(
        /the evidence supports the conclusion/i
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(/82%/)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/coherent/i)
    ).toBeInTheDocument();
  });


  test("surfaces reasoning API failure", async () => {
    reasonAbout.mockRejectedValue(
      new Error(
        "Sentinel could not complete reasoning."
      )
    );

    render(<Reason />);

    fireEvent.change(
      screen.getByRole("textbox"),
      {
        target: {
          value: "Evaluate this evidence.",
        },
      }
    );

    fireEvent.click(
      screen.getByRole(
        "button",
        { name: /analyze evidence/i }
      )
    );

    expect(
       await screen.findByRole("alert")
     ).toHaveTextContent(
       /sentinel could not complete reasoning/i
     );
  });
});

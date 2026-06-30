import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResearchForm } from "@/components/ResearchForm";

function renderForm(overrides = {}) {
  const props = {
    query: "",
    tickerA: "",
    tickerB: "",
    period: "6mo" as const,
    loading: false,
    onQueryChange: vi.fn(),
    onTickerAChange: vi.fn(),
    onTickerBChange: vi.fn(),
    onPeriodChange: vi.fn(),
    onExample: vi.fn(),
    onSubmit: vi.fn(),
    ...overrides
  };
  render(<ResearchForm {...props} />);
  return props;
}

describe("ResearchForm", () => {
  it("renders the main inputs", () => {
    renderForm();
    expect(screen.getByLabelText("자연어 질문")).toBeInTheDocument();
    expect(screen.getByLabelText("종목 A")).toBeInTheDocument();
    expect(screen.getByLabelText("종목 B")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "분석 시작" })).toBeInTheDocument();
  });

  it("submits when the analyze button is clicked", () => {
    const props = renderForm();
    fireEvent.click(screen.getByRole("button", { name: "분석 시작" }));
    expect(props.onSubmit).toHaveBeenCalledTimes(1);
  });

  it("shows a loading state", () => {
    renderForm({ loading: true });
    expect(screen.getByRole("button", { name: "분석 시작" })).toBeDisabled();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorBanner } from "@/components/ErrorBanner";

describe("ErrorBanner", () => {
  it("renders API error messages", () => {
    render(<ErrorBanner message="백엔드 서버에 연결하지 못했습니다." />);
    expect(screen.getByRole("alert")).toHaveTextContent("백엔드 서버에 연결하지 못했습니다.");
  });
});

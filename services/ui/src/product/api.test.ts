import { afterEach, describe, it, expect, vi } from "vitest";
import {
  forecastSchema,
  readFilters,
  forecastKey,
  getForecast,
  getRisk,
  ApiError,
} from "./api";
const filters = readFilters("");
const fixture = {
  city: "Calgary",
  target: "price",
  horizon: 12,
  model: "arima",
  data: [{ date: "2026-01-01", value: 0, lower: 0, upper: 0 }],
};
afterEach(() => vi.unstubAllGlobals());
describe("existing API adapter", () => {
  it("preserves zero bounds", () =>
    expect(forecastSchema.parse(fixture).data[0].lower).toBe(0));
  it("rejects invalid intervals", () =>
    expect(() =>
      forecastSchema.parse({
        ...fixture,
        data: [{ ...fixture.data[0], lower: 1 }],
      }),
    ).toThrow());
  it("rejects malformed responses", () =>
    expect(() =>
      forecastSchema.parse({ ...fixture, data: [{ value: "oops" }] }),
    ).toThrow());
  it("validates filters restored from URLs", () =>
    expect(readFilters("?horizon=bad&model=auto&target=bad")).toEqual(filters));
  it("isolates cache entries by every filter", () => {
    for (const changed of [
      { city: "Toronto" },
      { target: "rent" as const },
      { horizon: "2y" as const },
      { model: "lstm" as const },
    ])
      expect(forecastKey({ ...filters, ...changed })).not.toEqual(
        forecastKey(filters),
      );
  });
  it("passes cancellation to forecast requests", async () => {
    const controller = new AbortController();
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => fixture });
    vi.stubGlobal("fetch", fetcher);
    await getForecast(filters, controller.signal);
    const signal = fetcher.mock.calls[0][1].signal;
    controller.abort();
    expect(signal.aborted).toBe(true);
    expect(fetcher.mock.calls[0][0]).toContain("/forecast?");
  });
  it("rejects previous-city responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => ({ ...fixture, city: "Toronto" }),
        }),
    );
    await expect(getForecast(filters)).rejects.toThrow("different filters");
  });
  it("handles unavailable combinations", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    await expect(getForecast(filters)).rejects.toBeInstanceOf(ApiError);
  });
  it("keeps risk usable independently of forecasts and drops the composite", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => ({
            city: "Calgary",
            date: "2026-01-01",
            score: 99,
            breakdown: [{ name: "Inventory", status: "Unavailable" }],
          }),
        }),
    );
    const risk = await getRisk("Calgary");
    expect(risk.breakdown[0].status).toBe("Unavailable");
    expect(risk).not.toHaveProperty("score");
  });
});

export async function downloadReport(city: string) {
  try {
    const res = await fetch(
      `https://housing-insights-risk-dashboard.vercel.app/report/${city}.pdf`
    );

    if (!res.ok) throw new Error("Failed to fetch PDF");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `HIRD_${city.toLowerCase()}-report.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Download failed", err);
  }
}

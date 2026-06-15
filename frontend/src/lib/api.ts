import type { AssessmentRequest, AssessmentResponse } from "../types";

export async function createAssessment(payload: AssessmentRequest): Promise<AssessmentResponse> {
  const response = await fetch("/api/assessments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function downloadReport(payload: AssessmentRequest, kind: "pdf" | "docx", facilityName: string) {
  const response = await fetch(`/api/reports/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const safeName = facilityName.replace(/[^a-z0-9]+/gi, "_").replace(/^_+|_+$/g, "") || "facility";
  link.href = url;
  link.download = `${safeName}_assessment.${kind}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function readError(response: Response) {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) {
      return payload.detail.map((item: { msg?: string }) => item.msg ?? "Validation error").join(" ");
    }
  } catch {
    // Use status fallback below.
  }
  return `Request failed with status ${response.status}`;
}

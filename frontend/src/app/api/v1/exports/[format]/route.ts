import { NextResponse } from "next/server";

export async function GET(_request: Request, context: { params: Promise<{ format: string }> }) {
  const { format } = await context.params;
  if (format !== "csv" && format !== "jsonl") {
    return NextResponse.json({ detail: "Supported export formats are CSV and JSONL." }, { status: 400 });
  }
  return NextResponse.json({
    detail: "Dataset exports are not enabled yet because this deployment does not have persistent archive records or verified licence metadata. Public-source discovery results are not a curated or cleared training dataset.",
  }, { status: 503 });
}

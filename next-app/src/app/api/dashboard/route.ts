import { NextResponse } from 'next/server';
import Airtable from 'airtable';
import { GoogleGenAI } from '@google/genai';

export async function GET() {
  const apiKey = process.env.GEMINI_API_KEY || '';
  const airtableApiKey = process.env.AIRTABLE_API_KEY || '';
  const airtableBaseId = process.env.AIRTABLE_BASE_ID || '';

  let rawData = [
    { Transaction_ID: 101, Customer: "Acme Corp", Category: "Hardware", Amount_USD: 4500, Status: "Completed", Region: "Europe" },
    { Transaction_ID: 102, Customer: "TechNova", Category: "Software", Amount_USD: 12000, Status: "Completed", Region: "North America" },
    { Transaction_ID: 103, Customer: "GlobalLogistics", Category: "Logistics", Amount_USD: 8500, Status: "Pending", Region: "Europe" },
    { Transaction_ID: 104, Customer: "Apex Retail", Category: "Hardware", Amount_USD: 3200, Status: "Completed", Region: "Asia" },
    { Transaction_ID: 105, Customer: "BioHealth Ltd", Category: "Software", Amount_USD: 15400, Status: "Completed", Region: "North America" }
  ];

  // Try Airtable fetch if configured
  if (airtableApiKey && airtableBaseId) {
    try {
      const airtable = new Airtable({ apiKey: airtableApiKey }).base(airtableBaseId);
      const records = await airtable('DashboardMetrics').select({ maxRecords: 50 }).firstPage();
      if (records && records.length > 0) {
        rawData = records.map(r => r.fields as any);
      }
    } catch (err) {
      console.warn("Airtable fetch fallback to internal dataset");
    }
  }

  let aiSummary = "Summary generated based on active sales dataset.";
  if (apiKey) {
    try {
      const ai = new GoogleGenAI({ apiKey });
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-pro',
        contents: `Analyze this dashboard dataset and summarize key trends: ${JSON.stringify(rawData)}`,
      });
      aiSummary = response.text || aiSummary;
    } catch (err) {
      console.warn("Gemini API call fallback to standard metrics summary");
    }
  }

  return NextResponse.json({
    metrics: rawData,
    aiSummary: aiSummary,
  });
}

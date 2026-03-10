export async function analyzeProctoring(imageBuffer: string) {
  try {
    const response = await fetch("/api/ai/proctor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ imageBuffer }),
    });
    if (!response.ok) throw new Error("Failed to call proctoring API");
    return await response.json();
  } catch (error) {
    console.error("AI Proctoring Error:", error);
    return { malpracticeDetected: false, reason: "Vision analysis skipped (check API key/model)" };
  }
}

export async function scoreExplanation(userExplanation: string, masterRationale: string) {
  if (!userExplanation || userExplanation.trim().length < 5) {
    return { score: 0, feedback: "Explanation too short or missing." };
  }
  try {
    const response = await fetch("/api/ai/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userExplanation, masterRationale }),
    });
    if (!response.ok) throw new Error("Failed to call scoring API");
    return await response.json();
  } catch (error) {
    console.error("AI Scoring Error:", error);
    return { score: 0, feedback: "Error in scoring" };
  }
}

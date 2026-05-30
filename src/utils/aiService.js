/**
 * AI Work Log Verification Service.
 * Uses the Anthropic Claude API to verify work log authenticity.
 */

const verifyWorkLog = async (taskTitle, taskDescription, logText) => {
  if (!process.env.AI_API_KEY) {
    return {
      aiScore: null,
      aiFeedback: 'AI verification not configured. Set AI_API_KEY in .env to enable.',
      verificationStatus: 'pending',
    };
  }

  try {
    const prompt = `You are an AI work log verifier for a task management system. Your job is to evaluate whether an employee's work log genuinely reflects real work done on a specific task.

TASK TITLE: ${taskTitle}
TASK DESCRIPTION: ${taskDescription || 'No description provided'}

EMPLOYEE WORK LOG:
"${logText}"

Evaluate this log on the following criteria:
1. Relevance: Does the log actually relate to the assigned task?
2. Specificity: Does it describe concrete actions taken (not vague claims)?
3. Credibility: Does it sound like genuine work, not a bluff or filler?
4. Progress: Does it indicate measurable progress?

Respond ONLY with a valid JSON object in this exact format (no extra text, no markdown):
{
  "score": <integer 0-100>,
  "feedback": "<1-2 sentence plain English feedback for the manager>",
  "status": "<one of: genuine | flagged | verified>"
}

Score guide: 80-100 = genuine and detailed, 50-79 = acceptable but could be better, 0-49 = vague/irrelevant/likely bluffing.
Status: "genuine" if score >= 75, "flagged" if score < 50, "verified" if 50-74.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.AI_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: process.env.AI_MODEL || 'claude-sonnet-4-20250514',
        max_tokens: 256,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    if (!response.ok) {
      throw new Error(`AI API responded with status ${response.status}`);
    }

    const data = await response.json();
    const rawText = data.content?.[0]?.text || '';
    const cleaned = rawText.replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(cleaned);

    return {
      aiScore: parsed.score,
      aiFeedback: parsed.feedback,
      verificationStatus: parsed.status,
    };
  } catch (error) {
    console.error('AI verification error:', error.message);
    return {
      aiScore: null,
      aiFeedback: `AI verification failed: ${error.message}`,
      verificationStatus: 'pending',
    };
  }
};

const generateManagerSummary = async (tasks, employees) => {
  if (!process.env.AI_API_KEY) {
    return 'AI summary not available. Set AI_API_KEY in .env to enable this feature.';
  }

  try {
    const taskSummary = tasks.map((t) => ({
      title: t.title,
      assignedTo: t.assignedTo?.name || 'Unknown',
      status: t.status,
      priority: t.priority,
      deadline: t.deadline,
      isOverdue: new Date() > new Date(t.deadline) && t.status !== 'completed',
    }));

    const prompt = `You are a manager's AI assistant for a workforce platform. Based on the following task data, write a concise plain-English briefing (max 200 words) for the manager. Highlight: who is behind, what is at risk, which deadlines are slipping, and who is performing well.

TASK DATA:
${JSON.stringify(taskSummary, null, 2)}

Write a direct, actionable briefing. No bullet points in the middle; write it as 2-3 short paragraphs.`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.AI_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: process.env.AI_MODEL || 'claude-sonnet-4-20250514',
        max_tokens: 512,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    if (!response.ok) {
      throw new Error(`AI API responded with status ${response.status}`);
    }

    const data = await response.json();
    return data.content?.[0]?.text || 'Unable to generate summary.';
  } catch (error) {
    console.error('AI summary error:', error.message);
    return 'AI summary generation failed. Please try again.';
  }
};

module.exports = { verifyWorkLog, generateManagerSummary };

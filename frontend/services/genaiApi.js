import apiClient from './apiClient';

/**
 * Sends a query to the centralized GenAI backend.
 * @param {Object} params
 * @param {string} params.userQuery
 * @param {string} params.assistantType - "cad_coach" | "diabetes_explainer" | "care_navigator"
 * @param {Object} [params.context] - Unified Patient Context
 * @param {Object} [params.rawInput] - Raw form metrics & prediction object
 * @param {Array} [params.history] - Prior chat message history
 */
export async function sendGenAIQuery({ userQuery, assistantType, context, rawInput, history }) {
  return apiClient('/api/genai/chat', {
    method: 'POST',
    body: JSON.stringify({
      user_query: userQuery,
      assistant_type: assistantType,
      context,
      raw_input: rawInput,
      history
    })
  });
}

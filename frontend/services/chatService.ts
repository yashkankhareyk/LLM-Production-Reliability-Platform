import { apiClient } from "./apiClient";

export const sendChatMessage = async (message: string) => {
  const response = await apiClient.post("/v1/agent/run", {
    messages: [
      {
        role: "user",
        content: message
      }
    ],
    use_rag: false
  });

  return response.data;
};
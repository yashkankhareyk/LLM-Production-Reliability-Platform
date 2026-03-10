import { apiClient } from "./apiClient";

export const sendChatMessage = async (message: string) => {
  const response = await apiClient.post("/v1/chat", {
    messages: [
      {
        role: "user",
        content: message
      }
    ],
    use_rag: true
  });

  return response.data;
};
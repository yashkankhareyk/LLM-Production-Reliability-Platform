import { apiClient } from "./apiClient";

/* Upload single file */
export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await apiClient.post("/v1/ingest/file", formData);
  return res.data;
};

/* Upload multiple files */
export const uploadFiles = async (files: File[]) => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const res = await apiClient.post("/v1/ingest/files", formData);
  return res.data;
};

/* Get documents */
export const getDocuments = async (limit = 20, offset = 0) => {
  const res = await apiClient.get(`/v1/documents?limit=${limit}&offset=${offset}`);
  return res.data;
};

/* DELETE ALL DOCUMENTS */
export const deleteDocuments = async () => {
  const res = await apiClient.delete("/v1/documents");
  return res.data;
};
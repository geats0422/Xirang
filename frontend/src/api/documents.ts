import { getAuthHeaders } from "./authHeaders";
import { apiRequest } from "./http";

export type DocumentListItem = {
  id: string;
  title: string;
  file_name?: string;
  format?: string;
  status?: string;
  created_at?: string | null;
};

export type DocumentListResponse = {
  items: DocumentListItem[];
};

export const listDocuments = async (): Promise<DocumentListItem[]> => {
  const response = await apiRequest<DocumentListResponse>("/api/v1/documents/", {
    headers: getAuthHeaders(),
  });
  return response.items;
};

type UploadDocumentResponse = {
  document: {
    id: string;
    title: string;
    ingest_status: string;
  };
};

export const uploadDocument = async (file: File): Promise<DocumentListItem> => {
  const formData = new FormData();
  formData.set("file", file);
  formData.set("title", file.name);
  formData.set("format", file.name.split(".").pop()?.toLowerCase() ?? "txt");

  const response = await apiRequest<UploadDocumentResponse>("/api/v1/documents/upload", {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  return {
    id: response.document.id,
    title: response.document.title,
    status: response.document.ingest_status,
  };
};

type DeleteDocumentResponse = {
  id: string;
  deleted: boolean;
};

export const deleteDocument = async (documentId: string): Promise<DeleteDocumentResponse> => {
  return apiRequest<DeleteDocumentResponse>(`/api/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
};

export type DocumentProgressResponse = {
  document_id: string;
  status: string;
  progress: number;
  stage: string;
};

export const getDocumentProgress = async (
  documentId: string,
): Promise<DocumentProgressResponse> => {
  return apiRequest<DocumentProgressResponse>(
    `/api/v1/documents/${documentId}/progress`,
    { headers: getAuthHeaders() },
  );
};

type BatchDeleteDocumentsResponse = {
  deleted_ids: string[];
  deleted_count: number;
};

export const batchDeleteDocuments = async (
  documentIds: string[],
): Promise<BatchDeleteDocumentsResponse> => {
  return apiRequest<BatchDeleteDocumentsResponse>("/api/v1/documents/batch-delete", {
    method: "POST",
    headers: getAuthHeaders(),
    body: { document_ids: documentIds },
  });
};

type RetryDocumentResponse = {
  id: string;
  status: string;
};

export const retryDocument = async (documentId: string): Promise<RetryDocumentResponse> => {
  return apiRequest<RetryDocumentResponse>(`/api/v1/documents/${documentId}/retry`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
};
